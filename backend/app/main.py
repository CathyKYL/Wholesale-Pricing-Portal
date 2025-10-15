"""
FastAPI Application - Main Entry Point
---------------------------------------
Purpose:
- Create FastAPI application with all necessary middleware
- Configure CORS for Netlify frontend compatibility
- Set up API routes and documentation
- Works seamlessly in both local and cloud environments

Usage:
    # Local development:
    uvicorn main:app --reload --port 8000
    
    # Production (cloud):
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
import logging
import os
import sys

# Import our modules
from config import settings
from db import get_db, init_db
from models import CatalogRow

# Add parent directory to path for book_portal_pricing imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import pricing calculator
from book_portal_pricing.calculator import calculate_quote, Inputs, Outputs
from book_portal_pricing.supabase_repo import SupabaseRepo
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== PYDANTIC MODELS FOR API ==========

class QuoteRequest(BaseModel):
    """
    Request model for quote generation
    
    Attributes:
        asin: Product ASIN identifier
        marketplace: 'US' or 'UK'
        m: Our ROI floor (default 0.10 = 10%)
        fx_gbp_to_usd: GBP to USD exchange rate (default 1.30)
    """
    asin: str
    marketplace: str
    m: float = 0.10
    fx_gbp_to_usd: float = 1.30

class QuoteResponse(BaseModel):
    """
    Response model for quote generation
    
    Contains all calculated values from the pricing calculator
    """
    feasible: bool
    reason: Optional[str] = None
    quote_q: float
    seller_roi_pct: float
    our_roi_pct: float
    margin_abs: float
    margin_pct: float
    af: float
    fc: float
    sc: float
    s_bundle: float
    qmin: float
    qmax_our: float
    bb_avg: float
    
# ========== SUPABASE CLIENT INITIALIZATION ==========

def get_supabase_client():
    """
    Initialize Supabase client for quote generation
    
    Uses environment variables for credentials
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
        )
    
    return create_client(supabase_url, supabase_key)

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc"  # ReDoc at /redoc
)

# ========== CORS MIDDLEWARE ==========
# This is CRITICAL for Netlify frontend → Cloud backend communication
# Without this, browsers will block API calls from your frontend

app.add_middleware(
    CORSMiddleware,
    # Allow requests from these origins (domains)
    # In production, this includes your Netlify domain
    allow_origins=settings.CORS_ORIGINS,
    
    # Allow cookies and authentication headers
    allow_credentials=True,
    
    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    
    # Allow all headers
    allow_headers=["*"],
)

logger.info(f"CORS enabled for origins: {settings.CORS_ORIGINS}")
logger.info(f"Running in {settings.ENVIRONMENT} mode")
logger.info(f"Cloud deployment: {settings.is_cloud()}")


# ========== STARTUP EVENT ==========
@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts
    Initialize database tables if they don't exist
    """
    logger.info("🚀 Starting Wholesale Pricing Portal API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Initialize database (creates tables if needed)
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


# ========== HEALTH CHECK ENDPOINT ==========
@app.get("/")
async def root():
    """
    Root endpoint / Health check
    Use this to verify the API is running
    """
    return {
        "status": "healthy",
        "message": "Wholesale Pricing Portal API is running",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "cloud": settings.is_cloud()
    }


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint
    Useful for monitoring and debugging
    """
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.ENVIRONMENT,
        "config": settings.get_database_config()
    }


# ========== CATALOG ENDPOINTS ==========

@app.get("/api/catalog", response_model=List[dict])
async def get_catalog(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by title or author"),
    marketplace: Optional[str] = Query(None, regex="^(US|UK)$", description="Filter by marketplace (US or UK)"),
    db: Session = Depends(get_db)
):
    """
    Get catalog items with pagination and optional filtering
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Max number of records to return
    - search: Optional search term for title or author
    - marketplace: Optional filter by marketplace ('US' or 'UK')
    
    Returns:
    - List of catalog items
    
    Examples:
    - Get all items: /api/catalog
    - Get UK items only: /api/catalog?marketplace=UK
    - Get US items only: /api/catalog?marketplace=US
    - Search UK items: /api/catalog?marketplace=UK&search=Dragon
    """
    query = db.query(CatalogRow)
    
    # Filter by marketplace if provided
    if marketplace:
        query = query.filter(CatalogRow.marketplace == marketplace)
    
    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (CatalogRow.title.ilike(search_pattern)) |
            (CatalogRow.author.ilike(search_pattern)) |
            (CatalogRow.asin.ilike(search_pattern))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    items = query.offset(skip).limit(limit).all()
    
    # Convert to dictionaries
    results = []
    for item in items:
        results.append({
            "id": item.id,
            "asin": item.asin,
            "marketplace": item.marketplace,
            "title": item.title,
            "author": item.author,
            "available_stock": item.available_stock,
            "rrp": float(item.rrp) if item.rrp else None,
            "our_price": float(item.our_price) if item.our_price else None,
            # Keepa enrichment fields
            "isbn13": item.isbn13,
            "description": item.description,
            "image_url": item.image_url,
            "category_lvl1": item.category_lvl1,
            "category_lvl2": item.category_lvl2,
            "category_lvl3": item.category_lvl3,
            "package_dimensions": item.package_dimensions,
            "package_weight": float(item.package_weight) if item.package_weight else None
        })
    
    return results


@app.get("/api/catalog/{item_id}")
async def get_catalog_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get a single catalog item by ID
    
    Parameters:
    - item_id: The ID of the catalog item
    
    Returns:
    - Catalog item details
    """
    item = db.query(CatalogRow).filter(CatalogRow.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    return {
        "id": item.id,
        "asin": item.asin,
        "marketplace": item.marketplace,
        "title": item.title,
        "author": item.author,
        "available_stock": item.available_stock,
        "rrp": float(item.rrp) if item.rrp else None,
        "our_price": float(item.our_price) if item.our_price else None,
        # Keepa enrichment fields
        "isbn13": item.isbn13,
        "description": item.description,
        "image_url": item.image_url,
        "category_lvl1": item.category_lvl1,
        "category_lvl2": item.category_lvl2,
        "category_lvl3": item.category_lvl3,
        "package_dimensions": item.package_dimensions,
        "package_weight": float(item.package_weight) if item.package_weight else None
    }


@app.get("/api/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get catalog statistics
    
    Returns:
    - Various statistics about the catalog including marketplace breakdowns
    """
    from sqlalchemy import func
    
    # Overall statistics
    overall_stats = db.query(
        func.count(CatalogRow.id).label('total_items'),
        func.avg(CatalogRow.rrp).label('avg_rrp'),
        func.avg(CatalogRow.our_price).label('avg_our_price'),
        func.min(CatalogRow.our_price).label('min_price'),
        func.max(CatalogRow.our_price).label('max_price')
    ).first()
    
    # UK marketplace statistics
    uk_stats = db.query(
        func.count(CatalogRow.id).label('uk_items'),
        func.avg(CatalogRow.our_price).label('uk_avg_price')
    ).filter(CatalogRow.marketplace == 'UK').first()
    
    # US marketplace statistics
    us_stats = db.query(
        func.count(CatalogRow.id).label('us_items'),
        func.avg(CatalogRow.our_price).label('us_avg_price')
    ).filter(CatalogRow.marketplace == 'US').first()
    
    return {
        "total_items": overall_stats.total_items,
        "uk_marketplace_items": uk_stats.uk_items if uk_stats else 0,
        "us_marketplace_items": us_stats.us_items if us_stats else 0,
        "avg_rrp": float(overall_stats.avg_rrp) if overall_stats.avg_rrp else None,
        "avg_our_price": float(overall_stats.avg_our_price) if overall_stats.avg_our_price else None,
        "uk_avg_price": float(uk_stats.uk_avg_price) if uk_stats and uk_stats.uk_avg_price else None,
        "us_avg_price": float(us_stats.us_avg_price) if us_stats and us_stats.us_avg_price else None,
        "min_price": float(overall_stats.min_price) if overall_stats.min_price else None,
        "max_price": float(overall_stats.max_price) if overall_stats.max_price else None
    }


# ========== QUOTE GENERATION ENDPOINT ==========

@app.post("/api/quote", response_model=QuoteResponse)
async def generate_quote(request: QuoteRequest = Body(...)):
    """
    Generate wholesale quote for a product
    
    Purpose:
    - Calculate optimal wholesale quote using smooth continuous ROI logic
    - Fetch live Buy Box data from Supabase
    - Return complete quote with ROI calculations
    
    Parameters:
    - asin: Product ASIN identifier
    - marketplace: 'US' or 'UK'
    - m: Our ROI floor (default 0.10 = 10%)
    - fx_gbp_to_usd: GBP to USD exchange rate (default 1.30)
    
    Returns:
    - Complete quote data including:
      - quote_q: Wholesale quote price (Q)
      - seller_roi_pct: Seller ROI percentage
      - our_roi_pct: Our ROI percentage
      - All component values (AF, FC, SC, etc.)
    
    Example Request:
    ```json
    {
        "asin": "143914995X",
        "marketplace": "US",
        "m": 0.10,
        "fx_gbp_to_usd": 1.30
    }
    ```
    
    Example Response:
    ```json
    {
        "feasible": true,
        "quote_q": 17.90,
        "seller_roi_pct": 25.50,
        "our_roi_pct": 15.00,
        "bb_avg": 23.45,
        ...
    }
    ```
    """
    try:
        logger.info(f"Generating quote for {request.asin} ({request.marketplace})")
        
        # Initialize Supabase client
        supabase_client = get_supabase_client()
        repo = SupabaseRepo(supabase_client)
        
        # Generate quote using calculator
        outputs, _, _ = calculate_quote(
            repo=repo,
            product_id=request.asin,
            marketplace=request.marketplace,
            m=request.m,
            fx_gbp_to_usd=request.fx_gbp_to_usd
        )
        
        # Get Buy Box average for response
        bb_avg = repo.get_avg_bb_price(request.asin, request.marketplace)
        
        # Convert Outputs to response format
        response = QuoteResponse(
            feasible=outputs.feasible,
            reason=outputs.reason,
            quote_q=float(outputs.quote_q),
            seller_roi_pct=float(outputs.seller_roi_pct),
            our_roi_pct=float(outputs.our_roi_pct),
            margin_abs=float(outputs.margin_abs),
            margin_pct=float(outputs.margin_pct),
            af=float(outputs.af),
            fc=float(outputs.fc),
            sc=float(outputs.sc),
            s_bundle=float(outputs.s_bundle),
            qmin=float(outputs.qmin),
            qmax_our=float(outputs.qmax_our),
            bb_avg=float(bb_avg)
        )
        
        logger.info(
            f"Quote generated: Q=${response.quote_q:.2f}, "
            f"Seller ROI={response.seller_roi_pct:.2f}%, "
            f"Our ROI={response.our_roi_pct:.2f}%"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Quote generation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ========== ERROR HANDLERS ==========

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return {
        "error": "Not Found",
        "message": str(exc.detail) if hasattr(exc, 'detail') else "Resource not found"
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }


# ========== MAIN (for local testing) ==========
if __name__ == "__main__":
    import uvicorn
    
    # Run the application locally
    # In production, use: uvicorn main:app --host 0.0.0.0 --port $PORT
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

