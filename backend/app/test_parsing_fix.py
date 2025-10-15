"""
Test the parsing fix for ASINs with None csv[18]
"""
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import requests
import time
from sqlalchemy import create_engine, text
from config import settings

# Import the fixed parsing function
from keepa_ingestor import parse_keepa_history

def test_parsing_fix():
    """Test the parsing fix for problematic ASINs"""
    
    print("🧪 TESTING PARSING FIX")
    print("=" * 60)
    
    # Test one problematic ASIN
    test_asin = '1546103597'
    marketplace = 'US'
    
    print(f"Testing ASIN: {test_asin} ({marketplace})")
    
    # Keepa domain mapping
    KEEPA_DOMAINS = {'US': 1, 'UK': 2}
    domain = KEEPA_DOMAINS[marketplace]
    
    # API call
    url = "https://api.keepa.com/product"
    params = {
        'key': settings.KEEPA_API_KEY,
        'domain': domain,
        'asin': test_asin,
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
        
        products = data.get('products', [])
        if not products:
            print(f"❌ No products returned")
            return
        
        product = products[0]
        print(f"✅ Product found: {product.get('title', 'No title')[:50]}...")
        
        # Test the fixed parsing
        print(f"\n🧪 Testing fixed parsing logic...")
        records = parse_keepa_history(product, marketplace)
        
        print(f"✅ Parsing successful!")
        print(f"   Records created: {len(records)}")
        
        if records:
            # Show sample records
            print(f"\n📊 Sample records:")
            for i, record in enumerate(records[:5]):  # Show first 5
                print(f"   {i+1}. {record['fetch_date']}: {record['current_buybox_price']}")
            
            # Check if we have valid prices
            valid_prices = [r for r in records if r['current_buybox_price'] is not None]
            print(f"\n📈 Summary:")
            print(f"   Total records: {len(records)}")
            print(f"   Records with prices: {len(valid_prices)}")
            print(f"   Price coverage: {len(valid_prices)/len(records)*100:.1f}%")
            
            if len(records) > 0:
                print(f"✅ SUCCESS! Parsing now works correctly")
                return True
            else:
                print(f"❌ Still getting 0 records")
                return False
        else:
            print(f"❌ No records created")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test the fix"""
    success = test_parsing_fix()
    
    if success:
        print(f"\n🎉 PARSING FIX SUCCESSFUL!")
        print(f"   The issue was that csv[18] (BuyBox prices) is None for some ASINs")
        print(f"   The fix adds proper None checking before parsing")
        print(f"   Now we can run the full backfill successfully")
    else:
        print(f"\n❌ PARSING FIX FAILED")
        print(f"   Need to investigate further")

if __name__ == "__main__":
    main()




