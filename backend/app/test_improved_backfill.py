"""
Test the improved backfill logic with enhanced fallback pricing
"""
import requests
from datetime import datetime, timedelta
from config import settings
from keepa_ingestor import parse_keepa_history

def test_improved_backfill():
    """Test the improved backfill logic"""
    
    print("🧪 TESTING IMPROVED BACKFILL LOGIC")
    print("=" * 60)
    
    test_asins = [
        ('1546103597', 'US', 1),  # One Piece set
        ('1637995059', 'US', 1),  # Jujutsu Kaisen
        ('070234236X', 'UK', 3),  # Hunger Games
    ]
    
    for asin, marketplace, domain in test_asins:
        print(f"\n🔍 Testing ASIN: {asin} ({marketplace})")
        print("-" * 50)
        
        try:
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin,
                'days': 30,
                'buybox': 1,
                'offers': 20
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
            
            print(f"   Title: {product.get('title', 'Unknown')[:60]}...")
            print(f"   Is available: {product.get('isAvailable', False)}")
            
            # Debug: Print data structure
            print(f"\n   🔍 Debug - Product keys: {list(product.keys())}")
            
            if 'data' in product:
                data_keys = list(product['data'].keys()) if product['data'] else []
                print(f"   Data keys in response: {data_keys}")
                
                if not data_keys or not any(key in ['NEW', 'NEW_time', 'BUY_BOX_SHIPPING'] for key in data_keys):
                    print(f"   ⚠️ No historical data arrays found. Check 'days' parameter or Keepa API flags.")
            else:
                print(f"   ⚠️ No 'data' key found in product response")
            
            # Test the improved parsing logic
            print(f"\n   📊 Testing improved parsing logic...")
            records = parse_keepa_history(product, marketplace)
            
            print(f"   Records created: {len(records)}")
            
            if records:
                print(f"   ✅ SUCCESS! Created {len(records)} records")
                
                # Show sample records
                for i, record in enumerate(records[:3]):
                    price = record['current_buybox_price']
                    date = record['fetch_date']
                    rank = record['sales_rank_current']
                    print(f"     {i+1}. {date}: ${price} (rank: {rank})")
                
                # Check if we have valid prices
                valid_prices = [r for r in records if r['current_buybox_price'] is not None]
                print(f"   Records with prices: {len(valid_prices)}/{len(records)}")
                
                if len(valid_prices) > 0:
                    print(f"   ✅ SUCCESS! Found valid prices!")
                else:
                    print(f"   ❌ No valid prices found")
            else:
                print(f"   ❌ No records created")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    test_improved_backfill()

if __name__ == "__main__":
    main()
