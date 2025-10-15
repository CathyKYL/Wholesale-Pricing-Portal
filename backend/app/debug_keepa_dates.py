"""
Debug why Keepa is returning future dates
"""
import requests
from datetime import datetime, timedelta
from config import settings

def debug_keepa_dates():
    """Debug the Keepa API date behavior"""
    
    print("🔍 DEBUGGING KEEPA DATE BEHAVIOR")
    print("=" * 60)
    
    test_asin = '1546103597'
    marketplace = 'US'
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} ({marketplace})")
    print(f"Today: {datetime.now().date()}")
    
    # Test different approaches
    approaches = [
        {
            'name': 'Current approach (since parameter)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'since': int((datetime.now() - timedelta(days=360)).timestamp()),
                'stats': 365
            }
        },
        {
            'name': 'Range parameter (last 360 days)',
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
            'name': 'No date restrictions',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'stats': 365
            }
        }
    ]
    
    for approach in approaches:
        print(f"\n🧪 Testing: {approach['name']}")
        print("-" * 50)
        
        try:
            response = requests.get("https://api.keepa.com/product", 
                                 params=approach['params'], timeout=60)
            
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
            
            # Analyze the date ranges
            if len(csv_data) > 1 and csv_data[1]:  # New prices
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
                        
                        print(f"   Date range: {first_date} to {last_date}")
                        print(f"   Total data points: {len(dates)}")
                        
                        # Count future vs historical dates
                        today = datetime.now().date()
                        future_dates = [d for d in dates if d > today]
                        historical_dates = [d for d in dates if d <= today]
                        
                        print(f"   Historical dates: {len(historical_dates)}")
                        print(f"   Future dates: {len(future_dates)}")
                        
                        if future_dates:
                            print(f"   Future date range: {min(future_dates)} to {max(future_dates)}")
                        
                        if historical_dates:
                            print(f"   Historical date range: {min(historical_dates)} to {max(historical_dates)}")
                            
                            # Check if we have good historical coverage
                            historical_span = (max(historical_dates) - min(historical_dates)).days
                            print(f"   Historical span: {historical_span} days")
                            
                            if historical_span > 300:
                                print(f"   ✅ Good historical coverage!")
                            else:
                                print(f"   ⚠️  Limited historical coverage")
                        else:
                            print(f"   ❌ No historical dates found!")
                    else:
                        print(f"   ❌ No valid dates found")
                else:
                    print(f"   ❌ Insufficient data points")
            else:
                print(f"   ❌ No price data available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    debug_keepa_dates()

if __name__ == "__main__":
    main()




