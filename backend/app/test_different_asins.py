"""
Test different ASINs to see if the future date issue is ASIN-specific
"""
import requests
from datetime import datetime, timedelta
from config import settings

def test_different_asins():
    """Test multiple ASINs to see if future dates are ASIN-specific"""
    
    print("🧪 TESTING DIFFERENT ASINS")
    print("=" * 60)
    
    # Test different ASINs from our list
    test_asins = [
        ('1546103597', 'US', 1),  # The problematic one
        ('1637995059', 'US', 1),  # Another US ASIN
        ('0114850003', 'UK', 3),  # UK ASIN
        ('070234236X', 'UK', 3),  # Another UK ASIN
    ]
    
    for asin, marketplace, domain in test_asins:
        print(f"\n🔍 Testing ASIN: {asin} ({marketplace})")
        print("-" * 40)
        
        try:
            # Use simple parameters
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
            csv_data = product.get('csv', [])
            
            print(f"✅ API call successful")
            print(f"   Tokens used: {data.get('tokensConsumed', 'Unknown')}")
            print(f"   CSV length: {len(csv_data)}")
            
            # Check if product has basic info
            title = product.get('title', 'Unknown')
            print(f"   Title: {title[:50]}...")
            
            # Check availability
            availability = product.get('availability', [])
            if availability:
                print(f"   Availability: {availability}")
            
            # Check if it's a pre-order or future release
            release_date = product.get('releaseDate')
            if release_date:
                print(f"   Release date: {release_date}")
            
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
                        
                        if historical_dates:
                            historical_span = (max(historical_dates) - min(historical_dates)).days
                            print(f"   Historical span: {historical_span} days")
                            
                            if historical_span > 300:
                                print(f"   ✅ Good historical coverage!")
                            else:
                                print(f"   ⚠️  Limited historical coverage")
                        else:
                            print(f"   ❌ No historical dates found!")
                            
                            # Check if this might be a pre-order
                            if release_date:
                                print(f"   🤔 This might be a pre-order (release: {release_date})")
                            else:
                                print(f"   🤔 No release date info - might be data issue")
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
    test_different_asins()

if __name__ == "__main__":
    main()




