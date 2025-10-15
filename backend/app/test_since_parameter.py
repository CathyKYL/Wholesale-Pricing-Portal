"""
Test using the 'since' parameter instead of 'days' to get historical data
"""
import requests
from datetime import datetime, timedelta
from config import settings

def test_since_parameter():
    """Test using the 'since' parameter to get historical data"""
    
    print("🧪 TESTING 'SINCE' PARAMETER")
    print("=" * 60)
    
    test_asin = '1546103597'  # One Piece set
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} (US)")
    print(f"Today: {datetime.now().date()}")
    
    # Test different approaches
    approaches = [
        {
            'name': 'days=30 (current)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'days': 30,
                'buybox': 1,
                'offers': 20
            }
        },
        {
            'name': 'since=30 days ago',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'since': int((datetime.now() - timedelta(days=30)).timestamp()),
                'buybox': 1,
                'offers': 20
            }
        },
        {
            'name': 'since=90 days ago',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'since': int((datetime.now() - timedelta(days=90)).timestamp()),
                'buybox': 1,
                'offers': 20
            }
        },
        {
            'name': 'since=180 days ago',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'since': int((datetime.now() - timedelta(days=180)).timestamp()),
                'buybox': 1,
                'offers': 20
            }
        },
        {
            'name': 'since=365 days ago',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'since': int((datetime.now() - timedelta(days=365)).timestamp()),
                'buybox': 1,
                'offers': 20
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
            
            # Check the most recent price change
            last_price_change = product.get('lastPriceChange')
            if last_price_change:
                keepa_epoch = datetime(2011, 12, 21)
                change_date = keepa_epoch + timedelta(minutes=last_price_change)
                days_ago = (datetime.now().date() - change_date.date()).days
                print(f"   Last price change: {change_date.date()} ({days_ago} days ago)")
            
            # Check CSV[1] (New prices) for date range
            if len(csv_data) > 1 and csv_data[1]:
                new_prices = csv_data[1]
                if len(new_prices) >= 2:
                    keepa_epoch = datetime(2011, 12, 21)
                    
                    # Get all dates
                    dates = []
                    for i in range(0, len(new_prices), 2):
                        if i + 1 < len(new_prices):
                            timestamp = new_prices[i]
                            if timestamp != -1:
                                date = keepa_epoch + timedelta(minutes=timestamp)
                                dates.append(date.date())
                    
                    if dates:
                        dates.sort()
                        first_date = dates[0]
                        last_date = dates[-1]
                        
                        print(f"   New prices date range: {first_date} to {last_date}")
                        print(f"   Total data points: {len(dates)}")
                        
                        # Count future vs historical dates
                        today = datetime.now().date()
                        future_dates = [d for d in dates if d > today]
                        historical_dates = [d for d in dates if d <= today]
                        
                        print(f"   Historical dates: {len(historical_dates)}")
                        print(f"   Future dates: {len(future_dates)}")
                        
                        if historical_dates:
                            historical_span = (max(historical_dates) - min(historical_dates)).days
                            print(f"   Historical span: {historical_span} days")
                            print(f"   ✅ SUCCESS! Found historical data!")
                            
                            # Show recent historical dates
                            recent_historical = [d for d in historical_dates if d >= today - timedelta(days=30)]
                            if recent_historical:
                                print(f"   Recent historical: {recent_historical[:5]}")
                            
                            return approach['params']  # Return the working parameters
                        else:
                            print(f"   ❌ No historical dates found")
                    else:
                        print(f"   ❌ No valid dates found")
                else:
                    print(f"   ❌ Insufficient data points")
            else:
                print(f"   ❌ No price data available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n❌ No working parameter combination found")
    return None

def main():
    working_params = test_since_parameter()
    
    if working_params:
        print(f"\n🎉 FOUND WORKING PARAMETERS!")
        print(f"Working parameters: {working_params}")
    else:
        print(f"\n❌ No working parameters found")

if __name__ == "__main__":
    main()




