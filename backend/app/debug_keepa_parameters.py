"""
Debug Keepa API parameters to match what SellerAmp is using
"""
import requests
from datetime import datetime, timedelta
from config import settings

def debug_keepa_parameters():
    """Test different Keepa API parameter combinations"""
    
    print("🔍 DEBUGGING KEEPA API PARAMETERS")
    print("=" * 60)
    
    test_asin = '1546103597'  # One Piece set
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} (US)")
    print(f"Today: {datetime.now().date()}")
    
    # Test different parameter combinations
    test_cases = [
        {
            'name': 'Basic history request',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1
            }
        },
        {
            'name': 'History with stats only',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'stats': 1
            }
        },
        {
            'name': 'History with range 30 days',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'range': 30
            }
        },
        {
            'name': 'History with range 90 days',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'range': 90
            }
        },
        {
            'name': 'History with range 180 days',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'range': 180
            }
        },
        {
            'name': 'History with range 365 days',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'range': 365
            }
        },
        {
            'name': 'History with since parameter (30 days ago)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'since': int((datetime.now() - timedelta(days=30)).timestamp())
            }
        },
        {
            'name': 'History with since parameter (90 days ago)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'since': int((datetime.now() - timedelta(days=90)).timestamp())
            }
        },
        {
            'name': 'History with since parameter (180 days ago)',
            'params': {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': test_asin,
                'history': 1,
                'since': int((datetime.now() - timedelta(days=180)).timestamp())
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            response = requests.get("https://api.keepa.com/product", 
                                 params=test_case['params'], timeout=60)
            
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
            
            # Check if we have price data
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
                        
                        if historical_dates:
                            historical_span = (max(historical_dates) - min(historical_dates)).days
                            print(f"   Historical span: {historical_span} days")
                            print(f"   ✅ SUCCESS! Found historical data!")
                            
                            # Show sample historical dates
                            recent_historical = [d for d in historical_dates if d >= today - timedelta(days=30)]
                            if recent_historical:
                                print(f"   Recent historical dates: {recent_historical[:5]}")
                            
                            return test_case['params']  # Return the working parameters
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
    working_params = debug_keepa_parameters()
    
    if working_params:
        print(f"\n🎉 FOUND WORKING PARAMETERS!")
        print(f"Working parameters: {working_params}")
        print(f"\nNow we can update the backfill code to use these parameters")
    else:
        print(f"\n❌ No working parameters found")
        print(f"Need to investigate further")

if __name__ == "__main__":
    main()




