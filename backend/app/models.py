"""
Database Models (ORM Layer)
---------------------------
Purpose:
- Define SQLAlchemy ORM classes that map to PostgreSQL tables
- This file contains the CatalogRow model for storing marketplace-specific product data

All models use:
- Numeric(12, 2) for currency (no floats allowed)
- Clear column names matching business terminology
- Proper constraints (NOT NULL, unique constraints, etc.)

Schema Design:
- Each product can have separate entries for different marketplaces (US, UK)
- One Excel row with both UK and US ASINs creates TWO database rows
- This allows marketplace-specific pricing and stock levels
"""

from sqlalchemy import Column, Integer, String, Numeric, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

# Base class for all ORM models
# All models inherit from this to get SQLAlchemy functionality
Base = declarative_base()


class CatalogRow(Base):
    """
    Catalog Row Model (Normalized Schema)
    -------------------------------------
    This model represents a single product in a specific marketplace.
    Each product/marketplace combination is a separate row.
    
    Table name: catalog_rows
    
    Fields explanation:
    - id: Auto-incrementing primary key (unique identifier for each row)
    - asin: Amazon Standard Identification Number (UK or US depending on marketplace)
    - marketplace: Which Amazon marketplace this product is from ('US' or 'UK')
    - title: Book title (required field)
    - author: Book author name
    - available_stock: Number of units in stock for this marketplace
    - rrp: Recommended Retail Price in this marketplace (stored as decimal)
    - our_price: Our selling price in this marketplace (stored as decimal)
    
    Example:
    If Excel has one row with both UK and US ASINs, this creates TWO database rows:
    - Row 1: asin='ABC123', marketplace='UK', title='Book', rrp=44.95
    - Row 2: asin='XYZ789', marketplace='US', title='Book', rrp=39.99
    
    This design allows:
    - Different prices per marketplace
    - Different stock levels per marketplace
    - Easy querying by marketplace
    - Future expansion to other marketplaces (CA, DE, FR, etc.)
    """
    
    # The actual table name in PostgreSQL
    __tablename__ = "catalog_rows"
    
    # Primary key - auto-increments with each new row
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Amazon ASIN - REQUIRED field
    # This is either a UK ASIN or US ASIN depending on the marketplace column
    asin = Column(String(32), nullable=False, index=True)
    
    # Marketplace identifier - REQUIRED field
    # Must be exactly 'US' or 'UK' (2 characters)
    # This tells us which Amazon marketplace this ASIN belongs to
    marketplace = Column(String(2), nullable=False, index=True)
    
    # Book title - REQUIRED field (cannot be NULL)
    title = Column(String(512), nullable=False)
    
    # Author name - can be NULL if not specified
    author = Column(String(512), nullable=True)
    
    # Number of books available in stock - can be NULL if unknown
    # This is marketplace-specific (UK stock vs US stock)
    available_stock = Column(Integer, nullable=True)
    
    # Recommended Retail Price (RRP) - stored as decimal with 2 decimal places
    # Using Numeric instead of Float to avoid floating-point precision errors
    # Example: 44.95 is stored exactly as 44.95, not 44.949999...
    # This is marketplace-specific (UK price in GBP vs US price in USD)
    rrp = Column(Numeric(12, 2), nullable=True)
    
    # Our selling price - stored as decimal with 2 decimal places
    # This is the price we charge customers in this marketplace
    our_price = Column(Numeric(12, 2), nullable=True)
    
    # ========== KEEPA API ENRICHMENT FIELDS ==========
    # These fields are populated by fetching data from Keepa API
    # They provide additional product metadata from Amazon
    
    # ISBN-13 number (International Standard Book Number)
    # This is a 13-digit unique book identifier
    # Fetched from Keepa's EAN field
    isbn13 = Column(String(13), nullable=True)
    
    # Product image URL from Amazon (first image only)
    # Stored as single image ID from Keepa
    # Full URL format: https://images-na.ssl-images-amazon.com/images/I/{image_id}
    image_url = Column(String(200), nullable=True)
    
    # Amazon category hierarchy (from Keepa categoryTree)
    # Categories are organized in levels from broad to specific
    # Example: Books → Health, Family & Lifestyle → Psychology & Psychiatry
    
    # Top-level category (broadest)
    # Example: "Books", "Electronics", "Home & Kitchen"
    category_lvl1 = Column(String(200), nullable=True)
    
    # Second-level category (more specific)
    # Example: "Health, Family & Lifestyle", "Computers & Accessories"
    category_lvl2 = Column(String(200), nullable=True)
    
    # Third-level category (most specific)
    # Example: "Psychology & Psychiatry", "Networking & Cloud Computing"
    category_lvl3 = Column(String(200), nullable=True)
    
    # Package dimensions in inches (Length x Width x Height)
    # Stored as string (e.g., "10.2 x 8.5 x 1.2")
    # Useful for calculating shipping costs
    package_dimensions = Column(String(100), nullable=True)
    
    # Package weight in pounds
    # Stored as decimal for precision
    # Useful for calculating shipping costs
    package_weight = Column(Numeric(10, 2), nullable=True)
    
    # Unique constraint: same ASIN cannot appear twice for the same marketplace
    # But same ASIN CAN appear in both US and UK marketplaces
    # Example: ASIN 'ABC123' can only have one UK entry, but could also have a US entry
    __table_args__ = (
        UniqueConstraint('asin', 'marketplace', name='uq_asin_marketplace'),
    )
    
    def __repr__(self):
        """
        String representation of the object (for debugging)
        Shows the key fields when you print a CatalogRow object
        """
        return f"<CatalogRow(id={self.id}, asin='{self.asin}', marketplace='{self.marketplace}', title='{self.title[:30]}...', our_price={self.our_price})>"

