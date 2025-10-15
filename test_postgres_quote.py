"""
Test PostgreSQL Quote Calculator Integration (Direct Database Connection)
--------------------------------------------------------------------------
Purpose:
- Verify PostgreSQL connection using DATABASE_URL
- Test fetching live data from database
- Calculate a single quote using real data
- NO Supabase API key needed!

This script uses direct PostgreSQL connection instead of Supabase API.

Usage:
    python test_postgres_quote.py
    
Environment Variables Required:
    DATABASE_URL - Your PostgreSQL connection string (already in your .env)
"""

import os
import sys
from decimal import Decimal

# Load .env file first
env_file = '.env'
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

# Check environment variable
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("=" * 80)
    print("❌ ERROR: Missing DATABASE_URL environment variable!")
    print("=" * 80)
    print()
    print("Set it in your .env file:")
    print('  DATABASE_URL="postgresql://user:pass@host:port/database"')
    print()
    sys.exit(1)

# Import PostgreSQL repo
try:
    from book_portal_pricing.postgres_repo import PostgresRepo
except ImportError as e:
    print("=" * 80)
    print("❌ ERROR: Could not import PostgresRepo")
    print("=" * 80)
    print()
    print(str(e))
    print()
    if "psycopg2" in str(e):
        print("Install psycopg2:")
        print("  pip install psycopg2-binary")
    print()
    sys.exit(1)

# Import calculator
from book_portal_pricing.calculator import decide_quote, Inputs
from book_portal_pricing.money import D


def test_connection():
    """Test PostgreSQL connection."""
    print("=" * 80)
    print("🔌 TESTING POSTGRESQL CONNECTION")
    print("=" * 80)
    print()
    
    print(f"DATABASE_URL: {database_url[:50]}...")
    print()
    
    try:
        repo = PostgresRepo(database_url)
        print("✅ PostgreSQL connection successful!")
        return repo
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        sys.exit(1)


def test_fetch_products(repo):
    """Test fetching products from public.products."""
    print()
    print("=" * 80)
    print("📚 TESTING PRODUCT FETCH (public.products)")
    print("=" * 80)
    print()
    
    try:
        products = repo.list_all_products()
        print(f"✅ Found {len(products)} products in database")
        print()
        
        # Show first 5 products
        print("First 5 products:")
        for i, p in enumerate(products[:5], 1):
            print(f"  {i}. ASIN={p['asin']}, Marketplace={p['marketplace']}")
        
        if len(products) > 5:
            print(f"  ... and {len(products) - 5} more")
        
        return products
    except Exception as e:
        print(f"❌ Error fetching products: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def test_single_quote(repo, asin, marketplace):
    """Test calculating a single quote with live data."""
    print()
    print("=" * 80)
    print(f"💰 TESTING QUOTE CALCULATION")
    print("=" * 80)
    print()
    
    print(f"Product: {asin} ({marketplace})")
    print()
    
    try:
        # Step 1: Fetch Buy Box prices
        print("📊 Step 1: Fetching Buy Box prices from Backfill_test.dynamic_data...")
        bb_prices = repo.get_bb_prices_last_30_days(asin, marketplace)
        bb_avg = repo.get_avg_bb_price(asin, marketplace)
        print(f"  ✅ Found {len(bb_prices)} daily prices")
        print(f"  ✅ 30-day average (BB̄): {bb_avg}")
        print()
        
        # Step 2: Fetch our cost
        print("💵 Step 2: Fetching our cost from public.products.our_price...")
        c_cost = repo.get_our_cost_c(asin, marketplace)
        print(f"  ✅ Our cost (C): {c_cost}")
        print()
        
        # Step 3: Fetch weight
        print("⚖️  Step 3: Fetching weight from public.products.package_weight...")
        weight_kg = repo.get_weight_kg(asin, marketplace)
        print(f"  ✅ Weight: {weight_kg} kg")
        print()
        
        # Step 4: Calculate quote
        print("🧮 Step 4: Calculating quote with smooth continuous ROI logic...")
        inputs = Inputs(
            product_id=asin,
            marketplace=marketplace,
            bb_avg=bb_avg,
            c_cost=c_cost,
            weight_kg=weight_kg,
            m=D('0.10'),
            fx_gbp_to_usd=D('1.30')
        )
        
        outputs = decide_quote(inputs)
        print()
        
        # Display results
        print("=" * 80)
        print("📊 QUOTE RESULTS")
        print("=" * 80)
        print()
        
        if outputs.feasible:
            print(f"✅ FEASIBLE QUOTE")
            print(f"  Quote (Q):         {inputs.marketplace} {outputs.quote_q}")
            print(f"  Seller ROI:        {outputs.seller_roi_pct}%")
            print(f"  Our ROI:           {outputs.our_roi_pct}%")
            print(f"  Our Margin:        {inputs.marketplace} {outputs.margin_abs} ({outputs.margin_pct}%)")
            print()
        else:
            print(f"❌ NOT FEASIBLE")
            print(f"  Reason: {outputs.reason}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error calculating quote: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 10 + "POSTGRESQL QUOTE CALCULATOR TEST (Direct DB)" + " " * 22 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Test connection
    repo = test_connection()
    
    # Test fetching products
    products = test_fetch_products(repo)
    
    if not products:
        print()
        print("❌ No products found. Cannot test quote calculation.")
        sys.exit(1)
    
    # Test calculating quote for first product
    first_product = products[0]
    asin = first_product['asin']
    marketplace = first_product['marketplace']
    
    success = test_single_quote(repo, asin, marketplace)
    
    # Summary
    print()
    print("=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    print()
    
    if success:
        print("✅ ALL TESTS PASSED!")
        print()
        print("Live PostgreSQL Integration Verified:")
        print("  ✓ Connection to PostgreSQL successful")
        print("  ✓ Fetched products from public.products")
        print("  ✓ Fetched Buy Box prices from Backfill_test.dynamic_data")
        print("  ✓ Fetched our_price from public.products")
        print("  ✓ Fetched package_weight from public.products")
        print("  ✓ Calculated quote using smooth continuous ROI logic")
        print()
        print("✨ NO SUPABASE API KEY NEEDED!")
        print()
        print("Ready to generate full report!")
    else:
        print("❌ TESTS FAILED")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

