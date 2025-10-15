"""
Deep debug of the parsing logic
"""
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from config import settings

def debug_parsing_deep(asin, marketplace):
    """Deep debug of parsing logic"""
    print(f"\n🔍 DEEP DEBUG: {asin} ({marketplace})")
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
        
        print(f"✅ Product: {product.get('title', 'No title')[:50]}...")
        
        # Check CSV data
        csv_data = product.get('csv', [])
        print(f"📊 CSV length: {len(csv_data)}")
        
        # Check each price array
        price_arrays = [
            (0, "Amazon"),
            (1, "New"), 
            (3, "Used"),
            (18, "BuyBox")
        ]
        
        all_dates = set()
        
        for idx, name in price_arrays:
            if idx < len(csv_data) and csv_data[idx] is not None:
                array = csv_data[idx]
                print(f"   {name} (csv[{idx}]): {len(array)} elements")
                
                # Parse this array manually
                keepa_epoch = datetime(2011, 12, 21)
                valid_dates = 0
                
                for i in range(0, len(array), 2):
                    if i + 1 < len(array):
                        time_minutes = array[i]
                        value = array[i + 1]
                        
                        if time_minutes and value is not None and value != -1:
                            date_obj = keepa_epoch + timedelta(minutes=time_minutes)
                            date_key = date_obj.date()
                            all_dates.add(date_key)
                            valid_dates += 1
                
                print(f"      Valid entries: {valid_dates}")
                
                # Show sample dates
                if valid_dates > 0:
                    sample_dates = sorted(list(all_dates))[:5]
                    print(f"      Sample dates: {sample_dates}")
            else:
                print(f"   {name} (csv[{idx}]): None or missing")
        
        print(f"\n📅 Total unique dates found: {len(all_dates)}")
        
        if len(all_dates) == 0:
            print(f"❌ NO DATES FOUND - This is why 0 records are created")
            
            # Check if we should fall back to current snapshot
            print(f"\n🔄 Checking current snapshot fallback...")
            stats = product.get('stats', {})
            current = stats.get('current', [])
            
            if current and len(current) > 18:
                print(f"   Current stats available: {len(current)} elements")
                print(f"   Current BuyBox: {current[18]}")
                print(f"   Current New: {current[1]}")
                print(f"   Current Amazon: {current[0]}")
                
                # Test fallback logic
                def keepa_price_to_decimal(val):
                    if val is None or val == -1:
                        return None
                    return Decimal(str(val / 100.0))
                
                buybox_price = keepa_price_to_decimal(current[18])
                new_price = keepa_price_to_decimal(current[1])
                amazon_price = keepa_price_to_decimal(current[0])
                
                print(f"   Converted prices:")
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
                    else:
                        print(f"   ❌ No fallback price available")
                
                if buybox_price is not None:
                    print(f"   ✅ Should create 1 current record with price: {buybox_price}")
                else:
                    print(f"   ❌ Still no price available")
            else:
                print(f"   ❌ No current stats available")
        else:
            print(f"✅ Should create {len(all_dates)} historical records")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test problematic ASINs"""
    problematic_asins = [
        ('1546103597', 'US'),
        ('1637995059', 'US'),
        ('0114850003', 'UK')
    ]
    
    for asin, marketplace in problematic_asins:
        debug_parsing_deep(asin, marketplace)

if __name__ == "__main__":
    main()




