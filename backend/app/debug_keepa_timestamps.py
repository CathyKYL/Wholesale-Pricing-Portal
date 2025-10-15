"""
Debug Keepa timestamp conversion to understand the date issue
"""
import requests
from datetime import datetime, timedelta
from config import settings

def debug_keepa_timestamps():
    """Debug how Keepa timestamps are being converted to dates"""
    
    print("🔍 DEBUGGING KEEPA TIMESTAMP CONVERSION")
    print("=" * 60)
    
    test_asin = '1546103597'  # One Piece set
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} (US)")
    print(f"Today: {datetime.now().date()}")
    
    try:
        # Simple API call
        params = {
            'key': settings.KEEPA_API_KEY,
            'domain': domain,
            'asin': test_asin,
            'history': 1,
            'range': 30
        }
        
        response = requests.get("https://api.keepa.com/product", 
                             params=params, timeout=60)
        
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
        
        # Check what's in the CSV data
        print(f"\n📊 CSV DATA ANALYSIS:")
        print(f"   CSV[0] (Amazon prices): {len(csv_data[0]) if len(csv_data) > 0 and csv_data[0] else 'None'}")
        print(f"   CSV[1] (New prices): {len(csv_data[1]) if len(csv_data) > 1 and csv_data[1] else 'None'}")
        print(f"   CSV[18] (BuyBox prices): {len(csv_data[18]) if len(csv_data) > 18 and csv_data[18] else 'None'}")
        
        # Check the raw timestamp values
        if len(csv_data) > 1 and csv_data[1]:
            new_prices = csv_data[1]
            print(f"\n🕐 RAW TIMESTAMP ANALYSIS:")
            print(f"   Total price points: {len(new_prices)}")
            print(f"   First few timestamps: {new_prices[:10]}")
            
            # Check if timestamps are reasonable
            keepa_epoch = datetime(2011, 12, 21)
            print(f"   Keepa epoch: {keepa_epoch}")
            
            # Convert first few timestamps
            print(f"\n📅 TIMESTAMP CONVERSION:")
            for i in range(min(10, len(new_prices))):
                if i % 2 == 0:  # Only show timestamps, not prices
                    timestamp = new_prices[i]
                    converted_date = keepa_epoch + timedelta(minutes=timestamp)
                    print(f"   Timestamp {timestamp} -> {converted_date.date()}")
            
            # Check if there are any negative timestamps (which would be historical)
            negative_timestamps = [t for t in new_prices[::2] if t < 0]
            if negative_timestamps:
                print(f"\n✅ FOUND NEGATIVE TIMESTAMPS (Historical data):")
                for ts in negative_timestamps[:5]:
                    converted_date = keepa_epoch + timedelta(minutes=ts)
                    print(f"   Timestamp {ts} -> {converted_date.date()}")
            else:
                print(f"\n❌ NO NEGATIVE TIMESTAMPS FOUND")
                print(f"   All timestamps are positive (future dates)")
                
                # Check if this might be a timezone issue
                print(f"\n🌍 CHECKING FOR TIMEZONE ISSUES:")
                print(f"   Current time: {datetime.now()}")
                print(f"   UTC time: {datetime.utcnow()}")
                
                # Try converting with different timezone assumptions
                for i in range(min(5, len(new_prices))):
                    if i % 2 == 0:
                        timestamp = new_prices[i]
                        # Try different epoch dates
                        epochs = [
                            datetime(2011, 12, 21),  # Standard Keepa epoch
                            datetime(1970, 1, 1),    # Unix epoch
                            datetime(2000, 1, 1),    # Alternative epoch
                        ]
                        
                        print(f"   Timestamp {timestamp}:")
                        for epoch in epochs:
                            converted_date = epoch + timedelta(minutes=timestamp)
                            print(f"     Epoch {epoch.date()}: {converted_date.date()}")
        
        # Check if there are other price arrays that might have historical data
        print(f"\n🔍 CHECKING OTHER PRICE ARRAYS:")
        for i, price_array in enumerate(csv_data):
            if price_array and len(price_array) > 0:
                print(f"   CSV[{i}]: {len(price_array)} points")
                if len(price_array) >= 2:
                    # Check first few timestamps
                    timestamps = price_array[::2]
                    if timestamps:
                        keepa_epoch = datetime(2011, 12, 21)
                        first_ts = timestamps[0]
                        last_ts = timestamps[-1]
                        first_date = keepa_epoch + timedelta(minutes=first_ts)
                        last_date = keepa_epoch + timedelta(minutes=last_ts)
                        print(f"     Date range: {first_date.date()} to {last_date.date()}")
                        
                        # Check for negative timestamps
                        negative_count = sum(1 for ts in timestamps if ts < 0)
                        if negative_count > 0:
                            print(f"     ✅ Has {negative_count} historical timestamps!")
                        else:
                            print(f"     ❌ No historical timestamps")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    debug_keepa_timestamps()

if __name__ == "__main__":
    main()




