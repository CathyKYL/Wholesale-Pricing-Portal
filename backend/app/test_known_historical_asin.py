"""
Test with a known ASIN that should have historical data
"""
import requests
from datetime import datetime, timedelta
from config import settings

def test_known_historical_asin():
    """Test with a well-known ASIN that should have historical data"""
    
    print("🧪 TESTING KNOWN HISTORICAL ASIN")
    print("=" * 60)
    
    # Test with a very popular book that should have historical data
    test_asins = [
        ('B00I8BICB2', 'US', 1),  # Very popular book
        ('B08N5WRWNW', 'US', 1),  # Another popular book
        ('B07XLKMWZT', 'US', 1),  # One from our catalog
        ('B09B8C4W3L', 'US', 1),  # Another from our catalog
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
                'range': 30
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
            
            # Check basic product info
            title = product.get('title', 'Unknown')
            print(f"   Title: {title[:60]}...")
            
            # Check availability
            is_available = product.get('isAvailable', False)
            print(f"   Is available: {is_available}")
            
            # Check release date
            release_date = product.get('releaseDate')
            if release_date:
                print(f"   Release date: {release_date}")
            
            csv_data = product.get('csv', [])
            print(f"   CSV length: {len(csv_data)}")
            
            # Check price data
            if len(csv_data) > 1 and csv_data[1]:
                new_prices = csv_data[1]
                if len(new_prices) >= 2:
                    keepa_epoch = datetime(2011, 12, 21)
                    
                    # Get all timestamps
                    timestamps = new_prices[::2]
                    dates = []
                    for ts in timestamps:
                        if ts != -1:  # Skip invalid timestamps
                            date = keepa_epoch + timedelta(minutes=ts)
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
                            
                            # Show recent historical dates
                            recent_historical = [d for d in historical_dates if d >= today - timedelta(days=30)]
                            if recent_historical:
                                print(f"   Recent historical: {recent_historical[:5]}")
                            
                            return asin, marketplace  # Return the working ASIN
                        else:
                            print(f"   ❌ No historical dates found")
                            
                            # Check if all timestamps are positive (future)
                            positive_timestamps = [ts for ts in timestamps if ts > 0]
                            negative_timestamps = [ts for ts in timestamps if ts < 0]
                            
                            print(f"   Positive timestamps: {len(positive_timestamps)}")
                            print(f"   Negative timestamps: {len(negative_timestamps)}")
                            
                            if len(negative_timestamps) == 0:
                                print(f"   🤔 All timestamps are positive (future dates)")
                            else:
                                print(f"   🤔 Mixed timestamps")
                    else:
                        print(f"   ❌ No valid dates found")
                else:
                    print(f"   ❌ Insufficient data points")
            else:
                print(f"   ❌ No price data available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n❌ No ASINs with historical data found")
    return None, None

def main():
    working_asin, marketplace = test_known_historical_asin()
    
    if working_asin:
        print(f"\n🎉 FOUND WORKING ASIN!")
        print(f"ASIN: {working_asin} ({marketplace})")
        print(f"This ASIN has historical data, so the issue is ASIN-specific")
    else:
        print(f"\n❌ NO WORKING ASINs FOUND")
        print(f"This suggests a broader issue with our Keepa API setup")

if __name__ == "__main__":
    main()




