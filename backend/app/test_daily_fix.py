"""
Test the daily update fix for Buy Box prices
"""
import sys
import os
from datetime import datetime
from decimal import Decimal
import pandas as pd
import requests
import time
from sqlalchemy import create_engine, text
from config import settings

# Import the fixed functions
from keepa_ingestor import fetch_keepa_data, save_to_postgres

def test_daily_fix():
    """Test the daily update with Buy Box price fallback fix"""
    
    print("🧪 TESTING DAILY UPDATE FIX")
    print("=" * 60)
    
    # Test with a few problematic ASINs
    test_asins = ['1546103597', '070234236X', 'B0F38CZDDF', '0114850003']
    
    print(f"Testing ASINs: {test_asins}")
    
    # Temporarily modify ASIN lists for testing
    from keepa_ingestor import ASINS_US, ASINS_UK
    
    # Create test data
    all_records = []
    
    for asin in test_asins:
        # Determine marketplace
        marketplace = 'US' if asin in ASINS_US else 'UK'
        
        print(f"\n📡 Testing {asin} ({marketplace})...")
        
        # Keepa domain mapping
        KEEPA_DOMAINS = {'US': 1, 'UK': 2}
        domain = KEEPA_DOMAINS[marketplace]
        
        # API call
        url = "https://api.keepa.com/product"
        params = {
            'key': settings.KEEPA_API_KEY,
            'domain': domain,
            'asin': asin,
            'stats': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if 'error' in data:
                print(f"   ❌ API Error: {data['error']}")
                continue
                
            products = data.get('products', [])
            if not products:
                print(f"   ❌ No product data")
                continue
                
            product = products[0]
            stats = product.get('stats', {})
            current = stats.get('current', [])
            
            # Ensure array has enough elements
            while len(current) < 34:
                current.append(-1)
            
            def keepa_price_to_decimal(val):
                if val is None or val == -1:
                    return None
                return Decimal(str(val / 100.0))
            
            # Extract BuyBox price with fallback logic
            buybox_price = keepa_price_to_decimal(current[18])
            
            # Apply fallback logic
            if buybox_price is None:
                new_price = keepa_price_to_decimal(current[1])
                amazon_price = keepa_price_to_decimal(current[0])
                
                if new_price is not None:
                    buybox_price = new_price
                    print(f"   ✅ Using NEW price as fallback: {buybox_price}")
                elif amazon_price is not None:
                    buybox_price = amazon_price
                    print(f"   ✅ Using AMAZON price as fallback: {buybox_price}")
                else:
                    print(f"   ❌ No fallback price available")
            else:
                print(f"   ✅ BuyBox price found: {buybox_price}")
            
            # Create record
            record = {
                'asin': asin,
                'marketplace': marketplace,
                'fetch_date': datetime.now().date(),
                'current_buybox_price': buybox_price,
                'sales_rank_current': None,  # Simplified for test
                'num_sellers': current[11] if current[11] != -1 else None,
                'last_updated': datetime.now()
            }
            
            all_records.append(record)
            print(f"   ✅ Record created with price: {buybox_price}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    if all_records:
        print(f"\n💾 Saving {len(all_records)} test records...")
        
        # Convert to DataFrame and save
        df = pd.DataFrame(all_records)
        saved_count, filled_df = save_to_postgres(df)
        
        print(f"✅ Saved {saved_count} records")
        
        # Verify the data
        print(f"\n🔍 Verifying saved data...")
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            for asin in test_asins:
                result = conn.execute(text("""
                    SELECT asin, marketplace, current_buybox_price, fetch_date
                    FROM dynamic.keepa_daily_data
                    WHERE asin = :asin
                    ORDER BY fetch_date DESC
                    LIMIT 1
                """), {'asin': asin}).fetchone()
                
                if result:
                    asin_val, marketplace, price, date = result
                    print(f"   {asin}: {price} ({marketplace}) on {date}")
                else:
                    print(f"   {asin}: NOT FOUND")
        
        engine.dispose()
        
        print(f"\n🎉 Test completed! Check if Buy Box prices are now populated.")
    else:
        print(f"\n❌ No records created - test failed")

if __name__ == "__main__":
    test_daily_fix()




