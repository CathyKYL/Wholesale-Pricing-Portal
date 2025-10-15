"""
Test Keepa API date range parameters to ensure we get historical data correctly
"""
import requests
from datetime import datetime, timedelta
from config import settings

def test_keepa_date_range():
    """Test different Keepa API date range parameters"""
    
    print("🧪 TESTING KEEPA API DATE RANGE PARAMETERS")
    print("=" * 60)
    
    # Test ASIN
    test_asin = '1546103597'
    marketplace = 'US'
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} ({marketplace})")
    print(f"Today: {datetime.now().date()}")
    print(f"Target: 365 days backward from 2025-10-13")
    print(f"Expected range: 2024-10-13 to 2025-10-13")
    
    # Test different parameter combinations
    test_cases = [
        {
            'name': 'Current (range=360)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'range': 360,
                'stats': 365
            }
        },
        {
            'name': 'Current (range=365)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'range': 365,
                'stats': 365
            }
        },
        {
            'name': 'With since parameter (2024-10-13)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'since': 1728777600,  # Unix timestamp for 2024-10-13
                'stats': 365
            }
        },
        {
            'name': 'With since and range',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'since': 1728777600,  # 2024-10-13
                'range': 365,
                'stats': 365
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        
        try:
            response = requests.get("https://api.keepa.com/product", 
                                 params=test_case['params'], 
                                 timeout=30)
            
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
                    
                    print(f"   Date range: {first_date.date()} to {last_date.date()}")
                    print(f"   Data points: {len(new_prices) // 2}")
                    
                    # Check if dates are in the expected range
                    expected_start = datetime(2024, 10, 13).date()
                    expected_end = datetime(2025, 10, 13).date()
                    
                    if first_date.date() >= expected_start and last_date.date() <= expected_end:
                        print(f"   ✅ Dates are within expected range!")
                    else:
                        print(f"   ❌ Dates are outside expected range")
                        print(f"   Expected: {expected_start} to {expected_end}")
                else:
                    print(f"   ❌ Insufficient data points")
            else:
                print(f"   ❌ No price data available")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    test_keepa_date_range()

if __name__ == "__main__":
    main()




