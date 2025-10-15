"""
Check what products we actually have in our catalog
"""
from sqlalchemy import create_engine, text
from config import settings
import requests
from datetime import datetime, timedelta

def check_catalog_products():
    """Check what products we have and their release status"""
    
    print("📋 CHECKING CATALOG PRODUCTS")
    print("=" * 60)
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all ASINs from catalog
        catalog_rows = conn.execute(text("""
            SELECT asin, marketplace, title 
            FROM public.catalog_rows 
            ORDER BY asin
        """)).fetchall()
        
        print(f"Total ASINs in catalog: {len(catalog_rows)}")
        print(f"{'ASIN':<15} {'Market':<8} {'Title'}")
        print("-" * 80)
        
        for row in catalog_rows:
            print(f"{row.asin:<15} {row.marketplace:<8} {row.title[:50]:<50}")
    
    print(f"\n🧪 TESTING SAMPLE ASINs FOR RELEASE STATUS")
    print("=" * 60)
    
    # Test a few ASINs to check their release status
    test_asins = [
        ('1546103597', 'US', 1),
        ('1637995059', 'US', 1), 
        ('070234236X', 'UK', 3),
        ('0114850003', 'UK', 3),
        ('9124233684', 'UK', 3),  # Try a different one
        ('B0F38CZDDF', 'US', 1),  # Try a different one
    ]
    
    for asin, marketplace, domain in test_asins:
        print(f"\n🔍 Testing ASIN: {asin} ({marketplace})")
        print("-" * 40)
        
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
                                 params=params, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ HTTP Error: {response.status_code}")
                continue
                
            data = response.json()
            
            if 'error' in data:
                print(f"❌ Keepa Error: {data['error']}")
                continue
            
            products = data.get('products', [])
            if not products:
                print(f"❌ No products returned")
                continue
            
            product = products[0]
            
            # Check product info
            title = product.get('title', 'Unknown')
            print(f"   Title: {title[:60]}...")
            
            # Check release date
            release_date = product.get('releaseDate')
            if release_date:
                print(f"   Release date: {release_date}")
                if int(release_date) > 20251014:  # Today's date
                    print(f"   🚨 PRE-ORDER: Releases after today!")
                else:
                    print(f"   ✅ Released: Already available")
            else:
                print(f"   Release date: Not specified")
            
            # Check availability
            availability = product.get('availability', [])
            if availability:
                print(f"   Availability: {availability}")
            
            # Check if it's available for purchase
            is_available = product.get('isAvailable', False)
            print(f"   Is available: {is_available}")
            
            # Check price data
            csv_data = product.get('csv', [])
            if len(csv_data) > 1 and csv_data[1]:
                new_prices = csv_data[1]
                if len(new_prices) >= 2:
                    keepa_epoch = datetime(2011, 12, 21)
                    
                    # Get all dates
                    dates = []
                    for i in range(0, len(new_prices), 2):
                        if i + 1 < len(new_prices):
                            time_minutes = new_prices[i]
                            date = keepa_epoch + timedelta(minutes=time_minutes)
                            dates.append(date.date())
                    
                    if dates:
                        dates.sort()
                        first_date = dates[0]
                        last_date = dates[-1]
                        
                        print(f"   Price data range: {first_date} to {last_date}")
                        
                        # Count future vs historical dates
                        today = datetime.now().date()
                        future_dates = [d for d in dates if d > today]
                        historical_dates = [d for d in dates if d <= today]
                        
                        print(f"   Historical dates: {len(historical_dates)}")
                        print(f"   Future dates: {len(future_dates)}")
                        
                        if historical_dates:
                            print(f"   ✅ Has historical price data!")
                        else:
                            print(f"   ❌ Only future price data (pre-order)")
                    else:
                        print(f"   ❌ No valid price dates")
                else:
                    print(f"   ❌ Insufficient price data")
            else:
                print(f"   ❌ No price data available")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    check_catalog_products()

if __name__ == "__main__":
    main()




