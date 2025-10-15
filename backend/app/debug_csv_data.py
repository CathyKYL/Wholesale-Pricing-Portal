"""
Debug the CSV data to understand why we're not finding valid prices
"""
import requests
from datetime import datetime, timedelta
from config import settings

def debug_csv_data():
    """Debug the CSV data structure and date filtering"""
    
    print("🔍 DEBUGGING CSV DATA")
    print("=" * 60)
    
    test_asin = '1546103597'  # One Piece set
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} (US)")
    print(f"Today: {datetime.now().date()}")
    
    try:
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
        print(f"   CSV length: {len(csv_data)}")
        
        # Check each price array
        price_arrays = [
            (0, "Amazon price"),
            (1, "New price"), 
            (2, "Used price"),
            (4, "Collectible price"),
            (18, "BuyBox price")
        ]
        
        keepa_epoch = datetime(2011, 12, 21)
        today = datetime.now().date()
        
        print(f"\n📊 PRICE ARRAY ANALYSIS:")
        print(f"   Keepa epoch: {keepa_epoch}")
        print(f"   Today: {today}")
        
        for array_idx, price_type in price_arrays:
            if array_idx < len(csv_data) and csv_data[array_idx]:
                price_array = csv_data[array_idx]
                print(f"\n   {price_type} (CSV[{array_idx}]): {len(price_array)} points")
                
                if len(price_array) >= 2:
                    # Check first few timestamps and prices
                    print(f"     First 10 values: {price_array[:10]}")
                    
                    # Find valid historical prices
                    historical_prices = []
                    future_prices = []
                    
                    for i in range(0, len(price_array), 2):
                        if i + 1 < len(price_array):
                            timestamp = price_array[i]
                            price = price_array[i + 1]
                            
                            if timestamp != -1 and price != -1:
                                date = keepa_epoch + timedelta(minutes=timestamp)
                                
                                if date.date() <= today:
                                    historical_prices.append((date.date(), price))
                                else:
                                    future_prices.append((date.date(), price))
                    
                    print(f"     Historical prices: {len(historical_prices)}")
                    print(f"     Future prices: {len(future_prices)}")
                    
                    if historical_prices:
                        # Show most recent historical prices
                        historical_prices.sort(key=lambda x: x[0], reverse=True)
                        print(f"     Most recent historical:")
                        for date, price in historical_prices[:5]:
                            print(f"       {date}: ${price/100:.2f}")
                    else:
                        print(f"     ❌ No historical prices found")
                        
                        # Show what dates we have
                        if future_prices:
                            future_prices.sort(key=lambda x: x[0])
                            print(f"     Future dates range: {future_prices[0][0]} to {future_prices[-1][0]}")
                            
                            # Check if any are close to today
                            close_to_today = [p for p in future_prices if (p[0] - today).days <= 7]
                            if close_to_today:
                                print(f"     Close to today (within 7 days): {len(close_to_today)}")
                                for date, price in close_to_today[:3]:
                                    print(f"       {date}: ${price/100:.2f}")
            else:
                print(f"\n   {price_type} (CSV[{array_idx}]): Not available")
        
        # Test the date filtering logic
        print(f"\n🧪 TESTING DATE FILTERING LOGIC:")
        
        # Check New prices (CSV[1]) which should have the most data
        if len(csv_data) > 1 and csv_data[1]:
            new_prices = csv_data[1]
            print(f"   New prices array: {len(new_prices)} points")
            
            if len(new_prices) >= 2:
                # Get all dates
                all_dates = set()
                for i in range(0, len(new_prices), 2):
                    if i + 1 < len(new_prices):
                        timestamp = new_prices[i]
                        if timestamp != -1:
                            date = keepa_epoch + timedelta(minutes=timestamp)
                            all_dates.add(date.date())
                
                print(f"   All dates found: {len(all_dates)}")
                
                if all_dates:
                    sorted_dates = sorted(all_dates)
                    print(f"   Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
                    
                    # Apply our filtering logic
                    cutoff_date = today - timedelta(days=400)
                    future_cutoff = today
                    
                    filtered_dates = [d for d in sorted_dates if d >= cutoff_date and d <= future_cutoff]
                    future_dates = [d for d in sorted_dates if d > future_cutoff]
                    
                    print(f"   Dates after filtering: {len(filtered_dates)}")
                    print(f"   Future dates filtered out: {len(future_dates)}")
                    
                    if filtered_dates:
                        print(f"   Filtered date range: {filtered_dates[0]} to {filtered_dates[-1]}")
                    else:
                        print(f"   ❌ All dates filtered out!")
                        print(f"   Cutoff date: {cutoff_date}")
                        print(f"   Future cutoff: {future_cutoff}")
                        
                        # Check if we should relax the filtering
                        if future_dates:
                            closest_future = min(future_dates)
                            days_ahead = (closest_future - today).days
                            print(f"   Closest future date: {closest_future} ({days_ahead} days ahead)")
                            
                            if days_ahead <= 30:
                                print(f"   🤔 Maybe we should allow dates up to 30 days in the future?")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    debug_csv_data()

if __name__ == "__main__":
    main()




