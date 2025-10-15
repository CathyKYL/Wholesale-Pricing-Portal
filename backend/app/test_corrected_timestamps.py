"""
Test corrected Keepa timestamp decoding with proper epoch
"""
import requests
from datetime import datetime, timedelta, timezone
from config import settings

# Keepa epoch: 2011-01-01 00:00:00 UTC
KEEPA_EPOCH = datetime(2011, 1, 1, tzinfo=timezone.utc)

def keepa_minutes_to_dt(minutes):
    """Convert Keepa timestamp (minutes since 2011-01-01) to datetime."""
    if minutes == -1 or minutes is None:
        return None
    return KEEPA_EPOCH + timedelta(minutes=minutes)

def test_corrected_timestamps():
    """Test corrected timestamp decoding"""
    
    print("🧪 TESTING CORRECTED KEEPA TIMESTAMP DECODING")
    print("=" * 60)
    print(f"Keepa epoch: {KEEPA_EPOCH}")
    print(f"Today: {datetime.now().date()}")
    
    # Test ASINs from the spreadsheet
    test_asins = [
        ('1546103597', 'US', 1),  # One Piece set
        ('1637995059', 'US', 1),  # Jujutsu Kaisen
        ('070234236X', 'UK', 3),  # Hunger Games
    ]
    
    for asin, marketplace, domain in test_asins:
        print(f"\n🔍 Testing ASIN: {asin} ({marketplace})")
        print("-" * 50)
        
        try:
            # Correct Keepa API parameters
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin,
                'days': 360,
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
            
            # Check data structure
            csv_data = product.get('csv', [])
            print(f"   CSV length: {len(csv_data)}")
            
            # Analyze historical data from CSV arrays
            today = datetime.now().date()
            cutoff_date = today - timedelta(days=360)
            
            print(f"\n   📊 HISTORICAL DATA ANALYSIS:")
            print(f"   360 days ago: {cutoff_date}")
            
            # Check different price arrays for historical data
            price_arrays = [
                (0, "Amazon price"),
                (1, "New price"),
                (2, "Used price"),
                (4, "Collectible price"),
                (18, "BuyBox price")
            ]
            
            best_historical_data = None
            best_historical_count = 0
            best_date_range = None
            
            for array_idx, price_type in price_arrays:
                if array_idx < len(csv_data) and csv_data[array_idx]:
                    price_array = csv_data[array_idx]
                    if len(price_array) >= 2:
                        # Parse timestamps and prices
                        timestamps = price_array[::2]
                        prices = price_array[1::2]
                        
                        # Convert timestamps to dates using corrected epoch
                        dates = []
                        valid_prices = []
                        
                        for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
                            if timestamp != -1 and price != -1:
                                date_obj = keepa_minutes_to_dt(timestamp)
                                if date_obj:
                                    dates.append(date_obj.date())
                                    valid_prices.append(price)
                        
                        if dates:
                            dates.sort()
                            first_date = dates[0]
                            last_date = dates[-1]
                            
                            # Filter to only historical dates (last 360 days)
                            historical_dates = [d for d in dates if d >= cutoff_date and d <= today]
                            future_dates = [d for d in dates if d > today]
                            
                            print(f"     {price_type}: {len(dates)} total points")
                            print(f"       Date range: {first_date} to {last_date}")
                            print(f"       Historical: {len(historical_dates)} points")
                            print(f"       Future: {len(future_dates)} points")
                            
                            # Sanity checks
                            if future_dates:
                                print(f"       ⚠️  WARNING: {len(future_dates)} future dates found!")
                                print(f"         Future range: {min(future_dates)} to {max(future_dates)}")
                            
                            # Check date range span
                            if len(dates) > 1:
                                span_days = (max(dates) - min(dates)).days
                                if span_days > 366:
                                    print(f"       ⚠️  WARNING: Date span {span_days} days > 366 days")
                            
                            if len(historical_dates) > best_historical_count:
                                best_historical_count = len(historical_dates)
                                best_historical_data = price_type
                                best_date_range = (min(historical_dates), max(historical_dates))
            
            # Summary
            if best_historical_data:
                print(f"\n   ✅ BEST HISTORICAL DATA: {best_historical_data}")
                print(f"   📅 360d window: {best_date_range[0]} → {best_date_range[1]} ({best_historical_count} points, future=0)")
                
                # Check if we have good coverage
                if best_historical_count > 100:
                    print(f"   🎉 EXCELLENT: {best_historical_count} historical points!")
                elif best_historical_count > 50:
                    print(f"   ✅ GOOD: {best_historical_count} historical points")
                elif best_historical_count > 10:
                    print(f"   ⚠️  LIMITED: {best_historical_count} historical points")
                else:
                    print(f"   ❌ POOR: Only {best_historical_count} historical points")
            else:
                print(f"\n   ❌ NO HISTORICAL DATA FOUND")
                print(f"   This ASIN may be a pre-order or have no price history")
            
            # Check offers for current pricing
            offers = product.get('offers', [])
            if offers:
                print(f"\n   🛒 CURRENT OFFERS: {len(offers)}")
                for i, offer in enumerate(offers[:2]):  # Show first 2 offers
                    offer_csv = offer.get('offerCSV', [])
                    if offer_csv and len(offer_csv) >= 2:
                        # Get most recent price from offer
                        latest_price = offer_csv[-1] if offer_csv[-1] != 0 else offer_csv[-2]
                        if latest_price and latest_price != -1:
                            print(f"     Offer {i+1}: ${latest_price/100:.2f}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    test_corrected_timestamps()

if __name__ == "__main__":
    main()




