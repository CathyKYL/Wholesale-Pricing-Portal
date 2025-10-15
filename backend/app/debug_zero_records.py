"""
Debug why some ASINs get 0 historical records
This script will test the Keepa API response parsing for problematic ASINs
"""
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal
from config import settings

def debug_asin_parsing(asin, marketplace):
    """Debug the parsing for a specific ASIN"""
    print(f"\n🔍 DEBUGGING ASIN: {asin} ({marketplace})")
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
        print(f"📡 Calling Keepa API...")
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return
        
        data = response.json()
        
        if 'error' in data:
            print(f"❌ Keepa API Error: {data['error']}")
            return
        
        print(f"✅ API call successful")
        print(f"   Tokens used: {data.get('tokensConsumed', 'Unknown')}")
        
        products = data.get('products', [])
        if not products:
            print(f"❌ No products returned")
            return
        
        product = products[0]
        print(f"✅ Product found: {product.get('title', 'No title')[:50]}...")
        
        # Check CSV data structure
        csv_data = product.get('csv', [])
        print(f"\n📊 CSV Data Analysis:")
        print(f"   CSV array length: {len(csv_data)}")
        
        if len(csv_data) > 0:
            for i, csv_item in enumerate(csv_data[:20]):  # Check first 20 items
                if isinstance(csv_item, list):
                    print(f"   csv[{i}]: Array with {len(csv_item)} elements")
                    if len(csv_item) > 0:
                        print(f"      First few values: {csv_item[:6]}")
                else:
                    print(f"   csv[{i}]: {type(csv_item)} = {csv_item}")
        
        # Check specific price arrays
        print(f"\n💰 Price Arrays Analysis:")
        
        # Amazon prices (csv[0])
        amazon_csv = csv_data[0] if len(csv_data) > 0 else []
        print(f"   Amazon prices (csv[0]): {len(amazon_csv)} elements")
        if amazon_csv and len(amazon_csv) > 0:
            print(f"      Sample: {amazon_csv[:6]}")
        
        # New prices (csv[1])
        new_csv = csv_data[1] if len(csv_data) > 1 else []
        print(f"   New prices (csv[1]): {len(new_csv)} elements")
        if new_csv and len(new_csv) > 0:
            print(f"      Sample: {new_csv[:6]}")
        
        # Used prices (csv[3])
        used_csv = csv_data[3] if len(csv_data) > 3 else []
        print(f"   Used prices (csv[3]): {len(used_csv)} elements")
        if used_csv and len(used_csv) > 0:
            print(f"      Sample: {used_csv[:6]}")
        
        # BuyBox prices (csv[18])
        buybox_csv = csv_data[18] if len(csv_data) > 18 else []
        print(f"   BuyBox prices (csv[18]): {len(buybox_csv)} elements")
        if buybox_csv and len(buybox_csv) > 0:
            print(f"      Sample: {buybox_csv[:6]}")
        
        # Test the parsing logic
        print(f"\n🧪 Testing Parsing Logic:")
        
        def parse_history_array(history_array, name):
            """Parse Keepa history array and return count of valid entries"""
            if not history_array or not isinstance(history_array, list):
                print(f"   {name}: Empty or not a list")
                return 0
            
            valid_count = 0
            keepa_epoch = datetime(2011, 12, 21)
            
            for i in range(0, len(history_array), 2):
                if i + 1 < len(history_array):
                    time_minutes = history_array[i]
                    value = history_array[i + 1]
                    
                    if time_minutes and value is not None and value != -1:
                        date_obj = keepa_epoch + timedelta(minutes=time_minutes)
                        date_key = date_obj.date()
                        valid_count += 1
            
            print(f"   {name}: {valid_count} valid entries")
            return valid_count
        
        amazon_count = parse_history_array(amazon_csv, "Amazon")
        new_count = parse_history_array(new_csv, "New")
        used_count = parse_history_array(used_csv, "Used")
        buybox_count = parse_history_array(buybox_csv, "BuyBox")
        
        total_entries = max(amazon_count, new_count, used_count, buybox_count)
        print(f"\n📈 Summary:")
        print(f"   Total potential entries: {total_entries}")
        
        if total_entries == 0:
            print(f"   ❌ NO HISTORICAL DATA FOUND!")
            print(f"   This explains why 0 records were created")
        else:
            print(f"   ✅ Historical data exists - parsing should work")
        
        # Check current stats
        print(f"\n📊 Current Stats Analysis:")
        stats = product.get('stats', {})
        current = stats.get('current', [])
        print(f"   stats.current length: {len(current)}")
        
        if len(current) > 18:
            print(f"   Current prices (raw):")
            print(f"     Amazon: {current[0]}")
            print(f"     New: {current[1]}")
            print(f"     Used: {current[3]}")
            print(f"     BuyBox: {current[18]}")
            print(f"     Offer Count: {current[11]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test problematic ASINs"""
    print("🔍 DEBUGGING ZERO HISTORICAL RECORDS")
    print("=" * 60)
    
    # Test the ASINs that had 0 records
    problematic_asins = [
        ('1546103597', 'US'),
        ('1637995059', 'US'),
        ('2067955810', 'US'),
        ('163799673X', 'US'),
        ('163799897X', 'US'),
        ('B0F38CZDDF', 'US'),
        ('B0FCFLLM8L', 'US'),
        ('0114850003', 'UK'),
        ('4027876040', 'UK'),
        ('9124233684', 'UK'),
        ('070234236X', 'UK'),
        ('912424788X', 'UK')
    ]
    
    for asin, marketplace in problematic_asins:
        debug_asin_parsing(asin, marketplace)
        print("\n" + "="*60)

if __name__ == "__main__":
    main()




