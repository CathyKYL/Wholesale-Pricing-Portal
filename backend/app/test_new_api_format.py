"""
Test the new Keepa API format to understand the data structure
"""
import requests
from datetime import datetime, timedelta
from config import settings
import json

def test_new_api_format():
    """Test the new Keepa API format"""
    
    print("🧪 TESTING NEW KEEPA API FORMAT")
    print("=" * 60)
    
    test_asin = '1546103597'  # One Piece set
    domain = 1  # US
    
    print(f"Testing ASIN: {test_asin} (US)")
    
    try:
        params = {
            'key': settings.KEEPA_API_KEY,
            'domain': domain,
            'asin': test_asin,
            'days': 30,
            'buybox': 1,
            'offers': 20
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
        
        print(f"✅ API call successful")
        print(f"   Title: {product.get('title', 'Unknown')[:60]}...")
        print(f"   Is available: {product.get('isAvailable', False)}")
        
        # Check what's in the CSV data
        csv_data = product.get('csv', [])
        print(f"\n📊 CSV DATA STRUCTURE:")
        print(f"   CSV length: {len(csv_data)}")
        
        for i, array in enumerate(csv_data):
            if array and len(array) > 0:
                print(f"   CSV[{i}]: {len(array)} points")
                if len(array) <= 10:
                    print(f"     Values: {array}")
                else:
                    print(f"     First 10: {array[:10]}")
                    print(f"     Last 10: {array[-10:]}")
        
        # Check if there are other data structures
        print(f"\n🔍 OTHER DATA STRUCTURES:")
        
        # Check for price-related fields
        price_fields = ['lastPriceChange', 'newPriceIsMAP', 'offers', 'buyBoxEligibleOfferCounts']
        for field in price_fields:
            if field in product:
                value = product[field]
                print(f"   {field}: {value}")
        
        # Check offers
        offers = product.get('offers', [])
        if offers:
            print(f"\n🛒 OFFERS:")
            print(f"   Number of offers: {len(offers)}")
            for i, offer in enumerate(offers[:3]):  # Show first 3
                print(f"   Offer {i+1}: {offer}")
        
        # Check if there's a different data structure
        print(f"\n🔍 LOOKING FOR ALTERNATIVE DATA STRUCTURES:")
        
        # Check for arrays that might contain price data
        for key, value in product.items():
            if isinstance(value, list) and len(value) > 0:
                if any(isinstance(x, (int, float)) for x in value[:5]):
                    print(f"   {key}: {len(value)} numeric values")
                    if len(value) <= 10:
                        print(f"     Values: {value}")
                    else:
                        print(f"     First 10: {value[:10]}")
        
        # Check for nested data structures
        for key, value in product.items():
            if isinstance(value, dict) and len(value) > 0:
                print(f"   {key}: dict with keys {list(value.keys())[:10]}")
                
                # Check if it contains price data
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, list) and len(subvalue) > 0:
                        if any(isinstance(x, (int, float)) for x in subvalue[:5]):
                            print(f"     {subkey}: {len(subvalue)} numeric values")
                            if len(subvalue) <= 5:
                                print(f"       Values: {subvalue}")
        
        # Check if there's a 'data' field that we missed
        if 'data' in product:
            print(f"\n📊 DATA FIELD FOUND:")
            data = product['data']
            print(f"   Data type: {type(data)}")
            if isinstance(data, dict):
                print(f"   Data keys: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"   Data length: {len(data)}")
                if len(data) <= 10:
                    print(f"   Data values: {data}")
        
        # Check the most recent price change
        last_price_change = product.get('lastPriceChange')
        if last_price_change:
            print(f"\n💰 LAST PRICE CHANGE:")
            print(f"   Timestamp: {last_price_change}")
            
            # Convert to date
            keepa_epoch = datetime(2011, 12, 21)
            change_date = keepa_epoch + timedelta(minutes=last_price_change)
            print(f"   Date: {change_date.date()}")
            print(f"   Days ago: {(datetime.now().date() - change_date.date()).days}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    test_new_api_format()

if __name__ == "__main__":
    main()




