"""
Keepa API Integration Module
-----------------------------
Purpose:
- Fetch product metadata from Keepa API for Amazon ASINs
- Enrich our database with ISBN, images, dimensions, weight
- Handle US and UK marketplace separately
- Batch requests to respect Keepa API limits (100 ASINs per request)

Keepa API Documentation: https://keepa.com/#!discuss/t/product-object/116

Usage:
    from keepa_integration import fetch_keepa_data, update_catalog_with_keepa
    
    # Fetch and update all catalog items
    update_catalog_with_keepa()
    
    # Or fetch specific ASINs
    products = fetch_keepa_data(['B0FCFLLM8L'], 'US')
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
from decimal import Decimal

# Import our configuration and database
from config import settings
from db import SessionLocal
from models import CatalogRow


def fetch_keepa_data(asins: List[str], marketplace: str) -> List[Dict]:
    """
    Fetch Product Data from Keepa API
    ----------------------------------
    Retrieves product information from Keepa for a list of ASINs.
    
    Args:
        asins: List of Amazon ASINs to fetch (max 100 per call)
        marketplace: 'US' or 'UK' - which Amazon marketplace
    
    Returns:
        List of dictionaries containing product data
    
    Example:
        products = fetch_keepa_data(['B0FCFLLM8L', '912424788X'], 'US')
        for p in products:
            print(f"{p['asin']}: {p['title']}")
    """
    
    # Check if we have a Keepa API key
    if not settings.KEEPA_API_KEY:
        print("❌ ERROR: KEEPA_API_KEY not found in environment variables")
        print("→ Add to .env file: KEEPA_API_KEY=your_key_here")
        return []
    
    # Map marketplace to Keepa domain code
    # Keepa uses numeric codes: 1=US, 2=UK, 3=DE, 4=FR, etc.
    domain_map = {
        'US': 1,  # Amazon.com (United States)
        'UK': 2,  # Amazon.co.uk (United Kingdom)
        'DE': 3,  # Amazon.de (Germany)
        'FR': 4,  # Amazon.fr (France)
        'JP': 5,  # Amazon.co.jp (Japan)
        'CA': 6,  # Amazon.ca (Canada)
        'IT': 7,  # Amazon.it (Italy)
        'ES': 8,  # Amazon.es (Spain)
    }
    
    domain = domain_map.get(marketplace, 1)
    
    print(f"📡 Fetching {len(asins)} ASINs from Keepa ({marketplace} marketplace)...")
    
    # Keepa API allows max 100 ASINs per request
    # Split into chunks if we have more
    chunk_size = 100
    chunks = [asins[i:i + chunk_size] for i in range(0, len(asins), chunk_size)]
    
    all_products = []
    
    for chunk_num, chunk in enumerate(chunks, 1):
        print(f"  Processing chunk {chunk_num}/{len(chunks)} ({len(chunk)} ASINs)...")
        
        # Build the API URL
        # Join ASINs with comma
        asin_string = ",".join(chunk)
        
        # Keepa API endpoint
        url = f"https://api.keepa.com/product"
        
        # Query parameters
        # Note: Only include required parameters to avoid API errors
        params = {
            'key': settings.KEEPA_API_KEY,
            'domain': domain,
            'asin': asin_string
        }
        
        try:
            # Make the API request
            response = requests.get(url, params=params, timeout=30)
            
            # Check if request was successful
            if response.status_code != 200:
                print(f"  ⚠️  Keepa API error (HTTP {response.status_code}): {response.text}")
                continue
            
            # Parse JSON response
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                print(f"  ⚠️  Keepa API error: {data['error']}")
                continue
            
            # Extract products from response
            products = data.get('products', [])
            
            if not products:
                print(f"  ⚠️  No products returned for this chunk")
                continue
            
            print(f"  ✅ Received {len(products)} products from Keepa")
            
            # Process each product
            for product in products:
                all_products.append(product)
        
        except requests.exceptions.Timeout:
            print(f"  ⚠️  Request timeout for chunk {chunk_num}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Request error for chunk {chunk_num}: {e}")
            continue
        except Exception as e:
            print(f"  ⚠️  Unexpected error for chunk {chunk_num}: {e}")
            continue
    
    print(f"✅ Total products fetched from Keepa: {len(all_products)}")
    return all_products


def parse_keepa_product(product: Dict, marketplace: str) -> Dict:
    """
    Parse Keepa Product Data
    ------------------------
    Extracts relevant fields from Keepa's product object.
    
    Args:
        product: Raw product dictionary from Keepa API
        marketplace: 'US' or 'UK'
    
    Returns:
        Dictionary with cleaned/formatted product data
    """
    
    # Extract ASIN (product identifier)
    asin = product.get('asin', '')
    
    # Extract title
    # Keepa sometimes returns title as bytes, decode if needed
    title = product.get('title', '')
    if isinstance(title, bytes):
        title = title.decode('utf-8', errors='ignore')
    
    # Extract ISBN-13 from EAN list
    # EAN is European Article Number, equivalent to ISBN-13 for books
    isbn13 = None
    eans = product.get('eanList', [])
    if eans and len(eans) > 0:
        # First EAN is usually the ISBN-13
        isbn13 = str(eans[0]) if eans[0] else None
    
    # Extract first image URL only
    # Keepa returns images as comma-separated string
    # We only need the first image to save space and keep it simple
    image_url = None
    images_csv = product.get('imagesCSV', '')
    if images_csv:
        # Images are in format: "id1,id2,id3"
        # Full URL is: https://images-na.ssl-images-amazon.com/images/I/{id}
        image_ids = images_csv.split(',')
        # Take only the first image
        if image_ids and image_ids[0]:
            image_url = image_ids[0].strip()
    
    # Extract category hierarchy (up to 3 levels)
    # Keepa provides a categoryTree array with category objects
    # Each object has: {"catId": 123, "name": "Category Name"}
    category_lvl1 = None
    category_lvl2 = None  
    category_lvl3 = None
    
    category_tree = product.get('categoryTree', [])
    if category_tree:
        # Level 1: Top-level category (e.g., "Books")
        if len(category_tree) > 0:
            category_lvl1 = category_tree[0].get('name', '')
        
        # Level 2: Second-level category (e.g., "Health, Family & Lifestyle")
        if len(category_tree) > 1:
            category_lvl2 = category_tree[1].get('name', '')
        
        # Level 3: Third-level category (e.g., "Psychology & Psychiatry")
        if len(category_tree) > 2:
            category_lvl3 = category_tree[2].get('name', '')
    
    # Extract package dimensions
    # Format: [length, width, height] in inches * 100
    # Example: [1020, 850, 120] = 10.2" x 8.5" x 1.2"
    package_dimensions = None
    dims = product.get('packageDimension', [])
    if dims and len(dims) >= 3:
        # Convert from hundredths of inch to inches
        length = dims[0] / 100.0 if dims[0] else 0
        width = dims[1] / 100.0 if dims[1] else 0
        height = dims[2] / 100.0 if dims[2] else 0
        package_dimensions = f"{length:.2f} x {width:.2f} x {height:.2f}"
    
    # Extract package weight
    # Keepa returns weight in grams
    # Convert to pounds (1 pound = 453.592 grams)
    package_weight = None
    weight_grams = product.get('packageWeight')
    if weight_grams:
        package_weight = Decimal(str(weight_grams / 453.592))
    
    return {
        'asin': asin,
        'marketplace': marketplace,
        'title': title,
        'isbn13': isbn13,
        'image_url': image_url,
        'category_lvl1': category_lvl1,
        'category_lvl2': category_lvl2,
        'category_lvl3': category_lvl3,
        'package_dimensions': package_dimensions,
        'package_weight': package_weight
    }


def update_catalog_with_keepa(marketplace: Optional[str] = None, limit: Optional[int] = None):
    """
    Update Catalog with Keepa Data
    -------------------------------
    Fetches Keepa data for all (or filtered) catalog items and updates the database.
    
    Args:
        marketplace: Optional filter - 'US', 'UK', or None for all
        limit: Optional limit on number of items to update
    
    Returns:
        Number of items updated
    
    Example:
        # Update all US items
        updated = update_catalog_with_keepa(marketplace='US')
        
        # Update first 10 UK items
        updated = update_catalog_with_keepa(marketplace='UK', limit=10)
    """
    
    print("\n" + "=" * 70)
    print("🔄 KEEPA CATALOG UPDATE")
    print("=" * 70)
    
    # Create database session
    session = SessionLocal()
    
    try:
        # Build query to get catalog items
        query = session.query(CatalogRow)
        
        # Filter by marketplace if specified
        if marketplace:
            query = query.filter(CatalogRow.marketplace == marketplace)
            print(f"📋 Filtering by marketplace: {marketplace}")
        
        # Apply limit if specified
        if limit:
            query = query.limit(limit)
            print(f"📋 Limiting to first {limit} items")
        
        # Get all items to update
        items = query.all()
        
        if not items:
            print("⚠️  No items found to update")
            return 0
        
        print(f"📊 Found {len(items)} items to update")
        
        # Group ASINs by marketplace
        # We need to make separate API calls for US and UK
        asins_by_marketplace = {}
        for item in items:
            if item.marketplace not in asins_by_marketplace:
                asins_by_marketplace[item.marketplace] = []
            asins_by_marketplace[item.marketplace].append(item.asin)
        
        # Fetch data from Keepa for each marketplace
        total_updated = 0
        
        for mkt, asins in asins_by_marketplace.items():
            print(f"\n📡 Processing {mkt} marketplace ({len(asins)} ASINs)...")
            
            # Fetch from Keepa
            keepa_products = fetch_keepa_data(asins, mkt)
            
            if not keepa_products:
                print(f"  ⚠️  No data received from Keepa for {mkt}")
                continue
            
            # Update database with Keepa data
            print(f"💾 Updating database with {mkt} data...")
            
            for keepa_product in keepa_products:
                # Parse the Keepa product data
                parsed = parse_keepa_product(keepa_product, mkt)
                
                # Find the corresponding catalog item
                catalog_item = session.query(CatalogRow).filter(
                    CatalogRow.asin == parsed['asin'],
                    CatalogRow.marketplace == parsed['marketplace']
                ).first()
                
                if not catalog_item:
                    print(f"  ⚠️  ASIN {parsed['asin']} not found in catalog")
                    continue
                
                # Update fields with Keepa data
                # Only update if Keepa has data (don't overwrite with None)
                if parsed.get('title'):
                    catalog_item.title = parsed['title']
                if parsed.get('isbn13'):
                    catalog_item.isbn13 = parsed['isbn13']
                if parsed.get('image_url'):
                    catalog_item.image_url = parsed['image_url']
                if parsed.get('category_lvl1'):
                    catalog_item.category_lvl1 = parsed['category_lvl1']
                if parsed.get('category_lvl2'):
                    catalog_item.category_lvl2 = parsed['category_lvl2']
                if parsed.get('category_lvl3'):
                    catalog_item.category_lvl3 = parsed['category_lvl3']
                if parsed.get('package_dimensions'):
                    catalog_item.package_dimensions = parsed['package_dimensions']
                if parsed.get('package_weight'):
                    catalog_item.package_weight = parsed['package_weight']
                
                total_updated += 1
                print(f"  ✅ Updated: {parsed['asin']} - {parsed['title'][:50]}")
            
            # Commit changes for this marketplace
            session.commit()
            print(f"✅ Committed {mkt} updates to database")
        
        print(f"\n" + "=" * 70)
        print(f"🎉 Update complete! {total_updated} items enriched with Keepa data")
        print("=" * 70)
        
        return total_updated
    
    except Exception as e:
        print(f"\n❌ ERROR during Keepa update: {e}")
        session.rollback()
        return 0
    
    finally:
        session.close()


# Allow running this module directly for testing
if __name__ == "__main__":
    print("🧪 Keepa Integration Test")
    print("=" * 70)
    
    # Test with a single ASIN
    test_asins = ['B0FCFLLM8L']
    test_marketplace = 'US'
    
    print(f"Testing with ASIN: {test_asins[0]} ({test_marketplace})")
    products = fetch_keepa_data(test_asins, test_marketplace)
    
    if products:
        print(f"\n✅ Successfully fetched {len(products)} product(s)")
        for p in products:
            parsed = parse_keepa_product(p, test_marketplace)
            print(f"\nParsed data:")
            print(f"  ASIN: {parsed['asin']}")
            print(f"  Title: {parsed['title']}")
            print(f"  ISBN-13: {parsed['isbn13']}")
            print(f"  Dimensions: {parsed['package_dimensions']}")
            print(f"  Weight: {parsed['package_weight']} lbs")
    else:
        print("\n❌ No products fetched")

