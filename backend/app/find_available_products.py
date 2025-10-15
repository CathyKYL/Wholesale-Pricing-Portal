"""
Find products in our catalog that are currently available
"""
from sqlalchemy import create_engine, text
from config import settings
import requests
from datetime import datetime, timedelta

def find_available_products():
    """Find products that are currently available and have historical data"""
    
    print("🔍 FINDING AVAILABLE PRODUCTS IN CATALOG")
    print("=" * 60)
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all ASINs from catalog
        catalog_rows = conn.execute(text("""
            SELECT asin, marketplace, title 
            FROM public.catalog_rows 
            ORDER BY asin
        """)).fetchall()
    
    available_products = []
    preorder_products = []
    
    print(f"Testing {len(catalog_rows)} products...")
    print(f"{'ASIN':<15} {'Market':<8} {'Available':<10} {'Has History':<12} {'Status'}")
    print("-" * 70)
    
    for i, row in enumerate(catalog_rows):
        asin = row.asin
        marketplace = row.marketplace
        domain = 1 if marketplace == 'US' else 3
        
        try:
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin,
                'history': 1,
                'range': 360,
                'stats': 365
            }
            
            response = requests.get("https://api.keepa.com/product", 
                                 params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"{asin:<15} {marketplace:<8} {'Error':<10} {'Error':<12} {'HTTP ' + str(response.status_code)}")
                continue
                
            data = response.json()
            
            if 'error' in data:
                print(f"{asin:<15} {marketplace:<8} {'Error':<10} {'Error':<12} {data['error']}")
                continue
            
            products = data.get('products', [])
            if not products:
                print(f"{asin:<15} {marketplace:<8} {'No Data':<10} {'No Data':<12} {'No products'}")
                continue
            
            product = products[0]
            
            # Check availability
            is_available = product.get('isAvailable', False)
            
            # Check for historical data
            csv_data = product.get('csv', [])
            has_historical = False
            
            if len(csv_data) > 1 and csv_data[1]:  # New prices
                new_prices = csv_data[1]
                if len(new_prices) >= 2:
                    keepa_epoch = datetime(2011, 12, 21)
                    
                    # Get all dates
                    dates = []
                    for j in range(0, len(new_prices), 2):
                        if j + 1 < len(new_prices):
                            time_minutes = new_prices[j]
                            date = keepa_epoch + timedelta(minutes=time_minutes)
                            dates.append(date.date())
                    
                    if dates:
                        today = datetime.now().date()
                        historical_dates = [d for d in dates if d <= today]
                        has_historical = len(historical_dates) > 0
            
            # Determine status
            if is_available and has_historical:
                status = "✅ AVAILABLE"
                available_products.append((asin, marketplace, row.title))
            elif is_available:
                status = "⚠️ Available, no history"
            else:
                status = "❌ Pre-order"
                preorder_products.append((asin, marketplace, row.title))
            
            print(f"{asin:<15} {marketplace:<8} {str(is_available):<10} {str(has_historical):<12} {status}")
            
        except Exception as e:
            print(f"{asin:<15} {marketplace:<8} {'Error':<10} {'Error':<12} {str(e)[:20]}")
    
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    print(f"Total products tested: {len(catalog_rows)}")
    print(f"Available with history: {len(available_products)}")
    print(f"Pre-orders: {len(preorder_products)}")
    
    if available_products:
        print(f"\n✅ AVAILABLE PRODUCTS WITH HISTORICAL DATA:")
        print("-" * 60)
        for asin, marketplace, title in available_products:
            print(f"  {asin} ({marketplace}): {title[:50]}...")
    else:
        print(f"\n❌ NO AVAILABLE PRODUCTS FOUND!")
        print(f"   All products in your catalog are pre-orders or unavailable")
        print(f"   You need to add currently available products to get historical data")
    
    if preorder_products:
        print(f"\n📅 PRE-ORDER PRODUCTS:")
        print("-" * 60)
        for asin, marketplace, title in preorder_products[:5]:  # Show first 5
            print(f"  {asin} ({marketplace}): {title[:50]}...")
        if len(preorder_products) > 5:
            print(f"  ... and {len(preorder_products) - 5} more")

def main():
    find_available_products()

if __name__ == "__main__":
    main()




