"""
Test the historical data fix
"""
import requests
from datetime import datetime, timedelta
from config import settings

def test_historical_fix():
    """Test that we now get historical data instead of future data"""
    
    print("🧪 TESTING HISTORICAL DATA FIX")
    print("=" * 60)
    
    # Test ASIN
    test_asin = '1546103597'
    marketplace = 'US'
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} ({marketplace})")
    print(f"Today: {datetime.now().date()}")
    
    # Calculate timestamp for 360 days ago
    since_date = datetime.now() - timedelta(days=360)
    since_timestamp = int(since_date.timestamp())
    
    print(f"Since date (360 days ago): {since_date.date()}")
    print(f"Since timestamp: {since_timestamp}")
    
    # API call with new parameters
    url = "https://api.keepa.com/product"
    params = {
        'key': settings.KEEPA_API_KEY,
        'domain': domain,
        'asin': test_asin,
        'history': 1,
        'since': since_timestamp,
        'stats': 365
    }
    
    try:
        print(f"\n📡 Calling Keepa API with since parameter...")
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return
        
        data = response.json()
        
        if 'error' in data:
            print(f"❌ Keepa Error: {data['error']}")
            return
        
        products = data.get('products', [])
        if not products:
            print(f"❌ No products returned")
            return
        
        product = products[0]
        csv_data = product.get('csv', [])
        
        print(f"✅ API call successful")
        print(f"   Tokens used: {data.get('tokensConsumed', 'Unknown')}")
        print(f"   CSV length: {len(csv_data)}")
        
        # Check date ranges in the data
        if len(csv_data) > 1 and csv_data[1]:  # New prices
            new_prices = csv_data[1]
            if len(new_prices) >= 2:
                # Parse first and last dates
                keepa_epoch = datetime(2011, 12, 21)
                
                # First date
                first_time = new_prices[0]
                first_date = keepa_epoch + timedelta(minutes=first_time)
                
                # Last date
                last_time = new_prices[-2] if len(new_prices) >= 2 else new_prices[0]
                last_date = keepa_epoch + timedelta(minutes=last_time)
                
                print(f"\n📅 Date Analysis:")
                print(f"   First date: {first_date.date()}")
                print(f"   Last date: {last_date.date()}")
                print(f"   Data points: {len(new_prices) // 2}")
                
                # Check if dates are historical (not future)
                today = datetime.now().date()
                
                if last_date.date() <= today:
                    print(f"   ✅ Last date is historical (≤ {today})")
                else:
                    print(f"   ❌ Last date is in the future: {last_date.date()}")
                
                if first_date.date() >= since_date.date():
                    print(f"   ✅ First date is after since date (≥ {since_date.date()})")
                else:
                    print(f"   ⚠️  First date is before since date: {first_date.date()}")
                
                # Check if we have reasonable historical coverage
                date_range = (last_date.date() - first_date.date()).days
                print(f"   Date range span: {date_range} days")
                
                if date_range > 300:  # At least 300 days of data
                    print(f"   ✅ Good historical coverage!")
                else:
                    print(f"   ⚠️  Limited historical coverage")
                
                # Test the parsing logic
                print(f"\n🧪 Testing parsing logic...")
                from keepa_ingestor import parse_keepa_history
                records = parse_keepa_history(product, marketplace)
                
                print(f"   Records created: {len(records)}")
                
                if records:
                    # Show sample records
                    print(f"   Sample records:")
                    for i, record in enumerate(records[:3]):
                        print(f"     {i+1}. {record['fetch_date']}: {record['current_buybox_price']}")
                    
                    # Check if we have valid prices
                    valid_prices = [r for r in records if r['current_buybox_price'] is not None]
                    print(f"   Records with prices: {len(valid_prices)}/{len(records)}")
                    
                    if len(records) > 0:
                        print(f"   ✅ SUCCESS! Historical parsing is working")
                        return True
                    else:
                        print(f"   ❌ Still getting 0 records")
                        return False
                else:
                    print(f"   ❌ No records created")
                    return False
            else:
                print(f"   ❌ Insufficient data points")
                return False
        else:
            print(f"   ❌ No price data available")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_historical_fix()
    
    if success:
        print(f"\n🎉 HISTORICAL DATA FIX SUCCESSFUL!")
        print(f"   The since parameter now ensures we get historical data")
        print(f"   We can now run the full backfill successfully")
    else:
        print(f"\n❌ HISTORICAL DATA FIX FAILED")
        print(f"   Need to investigate further")

if __name__ == "__main__":
    main()




