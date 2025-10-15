"""
Test the date filtering logic specifically
"""
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from config import settings

def test_date_filtering(asin, marketplace):
    """Test date filtering logic"""
    print(f"\n🔍 TESTING DATE FILTERING: {asin} ({marketplace})")
    print("=" * 60)
    
    # Keepa domain mapping
    KEEPA_DOMAINS = {'US': 1, 'UK': 2}
    domain = KEEPA_DOMAINS[marketplace]
    
    # API call
    url = "https://api.keepa.com/product"
    params = {
        'key': settings.KEEPA_API_KEY,
        'domain': domain,
        'asin': asin,
        'history': 1,
        'range': 365,
        'stats': 365
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        data = response.json()
        product = data.get('products', [])[0]
        
        # Parse CSV data manually
        csv_data = product.get('csv', [])
        
        def parse_history_array(history_array):
            result = {}
            if not history_array or not isinstance(history_array, list):
                return result
            
            keepa_epoch = datetime(2011, 12, 21)
            for i in range(0, len(history_array), 2):
                if i + 1 < len(history_array):
                    time_minutes = history_array[i]
                    value = history_array[i + 1]
                    
                    if time_minutes and value is not None and value != -1:
                        date_obj = keepa_epoch + timedelta(minutes=time_minutes)
                        date_key = date_obj.date()
                        result[date_key] = value
            return result
        
        # Parse price arrays
        amazon_prices = parse_history_array(csv_data[0] if len(csv_data) > 0 and csv_data[0] is not None else [])
        new_prices = parse_history_array(csv_data[1] if len(csv_data) > 1 and csv_data[1] is not None else [])
        used_prices = parse_history_array(csv_data[3] if len(csv_data) > 3 and csv_data[3] is not None else [])
        buybox_prices = parse_history_array(csv_data[18] if len(csv_data) > 18 and csv_data[18] is not None else [])
        
        # Get all dates
        all_dates = set()
        all_dates.update(amazon_prices.keys())
        all_dates.update(new_prices.keys())
        all_dates.update(used_prices.keys())
        all_dates.update(buybox_prices.keys())
        
        print(f"📅 Total dates found: {len(all_dates)}")
        
        if all_dates:
            sorted_dates = sorted(all_dates)
            print(f"   Earliest date: {sorted_dates[0]}")
            print(f"   Latest date: {sorted_dates[-1]}")
            print(f"   Sample dates: {sorted_dates[:5]}")
            print(f"   Sample dates (end): {sorted_dates[-5:]}")
        
        # Test date filtering
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=400)
        future_cutoff = today + timedelta(days=30)
        
        print(f"\n📊 Date filtering test:")
        print(f"   Today: {today}")
        print(f"   Cutoff (400 days ago): {cutoff_date}")
        print(f"   Future cutoff (+30 days): {future_cutoff}")
        
        filtered_dates = []
        for date_key in sorted(all_dates):
            if date_key < cutoff_date:
                print(f"   ❌ {date_key}: Too old (< {cutoff_date})")
            elif date_key > future_cutoff:
                print(f"   ❌ {date_key}: Too far in future (> {future_cutoff})")
            else:
                filtered_dates.append(date_key)
                print(f"   ✅ {date_key}: Within range")
        
        print(f"\n📈 Filtering results:")
        print(f"   Original dates: {len(all_dates)}")
        print(f"   Filtered dates: {len(filtered_dates)}")
        
        if len(filtered_dates) == 0:
            print(f"   ❌ ALL DATES FILTERED OUT!")
            print(f"   This explains why 0 records are created")
            
            # Check if we should use current snapshot
            print(f"\n🔄 Checking current snapshot fallback...")
            stats = product.get('stats', {})
            current = stats.get('current', [])
            
            if current and len(current) > 18:
                print(f"   Current stats available: {len(current)} elements")
                
                def keepa_price_to_decimal(val):
                    if val is None or val == -1:
                        return None
                    return Decimal(str(val / 100.0))
                
                buybox_price = keepa_price_to_decimal(current[18])
                new_price = keepa_price_to_decimal(current[1])
                amazon_price = keepa_price_to_decimal(current[0])
                
                print(f"   Current prices:")
                print(f"     BuyBox: {buybox_price}")
                print(f"     New: {new_price}")
                print(f"     Amazon: {amazon_price}")
                
                # Apply fallback
                if buybox_price is None:
                    if new_price is not None:
                        buybox_price = new_price
                        print(f"   ✅ Using NEW as fallback: {buybox_price}")
                    elif amazon_price is not None:
                        buybox_price = amazon_price
                        print(f"   ✅ Using AMAZON as fallback: {buybox_price}")
                
                if buybox_price is not None:
                    print(f"   ✅ Should create 1 current record")
                else:
                    print(f"   ❌ No current price available")
        else:
            print(f"   ✅ Should create {len(filtered_dates)} records")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test problematic ASINs"""
    test_date_filtering('1546103597', 'US')

if __name__ == "__main__":
    main()




