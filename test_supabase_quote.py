"""
Test Supabase Quote Calculator Integration
-------------------------------------------
Purpose:
- Verify connection to Supabase
- Test fetching live data from database
- Calculate a single quote using real data

This script tests the complete flow:
1. Connect to Supabase
2. Fetch product data from public.products
3. Fetch Buy Box history from Backfill_test.dynamic_data
4. Calculate quote using smooth continuous ROI logic

Usage:
    python test_supabase_quote.py
    
Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_KEY - Your Supabase API key
"""

import os
import sys
from decimal import Decimal

# Check environment variables first
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("=" * 80)
    print("❌ ERROR: Missing environment variables!")
    print("=" * 80)
    print()
    print("Required environment variables:")
    print("  SUPABASE_URL - Your Supabase project URL")
    print("  SUPABASE_KEY - Your Supabase API key (anon or service role)")
    print()
    print("Set them in your .env file or environment:")
    print('  export SUPABASE_URL="https://your-project.supabase.co"')
    print('  export SUPABASE_KEY="your-api-key"')
    print()
    sys.exit(1)

# Import Supabase client
try:
    from supabase import create_client
except ImportError:
    print("=" * 80)
    print("❌ ERROR: supabase-py not installed!")
    print("=" * 80)
    print()
    print("Install with:")
    print("  pip install supabase")
    print()
    sys.exit(1)

# Import our modules
from book_portal_pricing.supabase_repo import SupabaseRepo
from book_portal_pricing.calculator import decide_quote, Inputs
from book_portal_pricing.money import D


def test_connection():
    """Test Supabase connection."""
    print("=" * 80)
    print("🔌 TESTING SUPABASE CONNECTION")
    print("=" * 80)
    print()
    
    print(f"SUPABASE_URL: {supabase_url[:40]}...")
    print(f"SUPABASE_KEY: {supabase_key[:20]}...")
    print()
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully!")
        return client
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
        
        print(f"Inputs:")
        print(f"  ASIN:              {asin}")
        print(f"  Marketplace:       {marketplace}")
        print(f"  Buy Box Avg (BB̄): {inputs.marketplace} {inputs.bb_avg}")
        print(f"  Our Cost (C):      {inputs.marketplace} {inputs.c_cost}")
        print(f"  Weight:            {inputs.weight_kg} kg")
        print()
        
        print(f"Components:")
        print(f"  Amazon Fee (AF):   {inputs.marketplace} {outputs.af} (17% of BB̄)")
        print(f"  Fulfilment (FC):   {inputs.marketplace} {outputs.fc}")
        print(f"  Shipping (SC):     {inputs.marketplace} {outputs.sc}")
        print(f"  Seller Costs (S):  {inputs.marketplace} {outputs.s_bundle}")
        print()
        
        print(f"Our ROI Band:")
        print(f"  Q_min (10%):       {inputs.marketplace} {outputs.qmin}")
        print(f"  Q_max_our (20%):   {inputs.marketplace} {outputs.qmax_our}")
        print()
        
        print(f"Seller ROI Boundaries (continuous):")
        print(f"  Q_seller10:        {inputs.marketplace} {outputs.q_seller10}")
        print(f"  Q_seller30:        {inputs.marketplace} {outputs.q_seller30}")
        print(f"  Q_seller40:        {inputs.marketplace} {outputs.q_seller40}")
        print()
        
        if outputs.feasible:
            print(f"✅ FEASIBLE QUOTE")
            print(f"  Quote (Q):         {inputs.marketplace} {outputs.quote_q}")
            print(f"  Seller ROI:        {outputs.seller_roi_pct}%")
            print(f"  Our ROI:           {outputs.our_roi_pct}%")
            print(f"  Our Margin:        {inputs.marketplace} {outputs.margin_abs} ({outputs.margin_pct}%)")
            print()
            
            # Explain decision
            if outputs.our_roi_pct >= D('19.90'):
                print(f"  Decision: We took our 20% ROI cap (seller-favoured)")
                print(f"            Seller ROI floats smoothly: {outputs.seller_roi_pct}%")
            else:
                print(f"  Decision: Lowered Q to ensure seller gets 10% ROI")
                print(f"            Our ROI: {outputs.our_roi_pct}% (within 10-20%)")
        else:
            print(f"❌ NOT FEASIBLE")
            print(f"  Reason: {outputs.reason}")
            print(f"  (Even at our 10% floor, seller would be <10%)")
        
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
    print("║" + " " * 15 + "SUPABASE QUOTE CALCULATOR TEST" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Test connection
    client = test_connection()
    repo = SupabaseRepo(client)
    
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
        print("Live Supabase Integration Verified:")
        print("  ✓ Connection to Supabase successful")
        print("  ✓ Fetched products from public.products")
        print("  ✓ Fetched Buy Box prices from Backfill_test.dynamic_data")
        print("  ✓ Fetched our_price from public.products")
        print("  ✓ Fetched package_weight from public.products")
        print("  ✓ Calculated quote using smooth continuous ROI logic")
        print()
        print("Ready to generate full report with:")
        print("  python generate_quote_report_live.py")
    else:
        print("❌ TESTS FAILED")
        print()
        print("Check the errors above and verify:")
        print("  - Database schema matches expected structure")
        print("  - Tables exist: public.products, Backfill_test.dynamic_data")
        print("  - Columns exist: our_price, package_weight, buy_box_price")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()




