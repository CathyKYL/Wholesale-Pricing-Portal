"""
Test Buy Box price parsing from Keepa API
This script tests the API connectivity and Buy Box price extraction
"""
import requests
import json
from decimal import Decimal
from config import settings

def test_keepa_api_single_asin(asin, marketplace):
    """Test Keepa API for a single ASIN and check Buy Box price parsing"""
    
    print(f"\n🧪 Testing ASIN: {asin} ({marketplace})")
    print("=" * 60)
    
    # Keepa domain mapping
    KEEPA_DOMAINS = {'US': 1, 'UK': 2}
    domain = KEEPA_DOMAINS[marketplace]
    
    # API parameters
    url = "https://api.keepa.com/product"
    params = {
        'key': settings.KEEPA_API_KEY,
        'domain': domain,
        'asin': asin,
        'stats': 1  # Current snapshot only
    }
    
    try:
        print(f"📡 Calling Keepa API...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
        
        data = response.json()
        
        if 'error' in data:
            print(f"❌ Keepa API Error: {data['error']}")
            return False
        
        print(f"✅ API call successful")
        print(f"   Tokens used: {data.get('tokensConsumed', 'Unknown')}")
        
        products = data.get('products', [])
        if not products:
            print(f"❌ No products returned for ASIN {asin}")
            return False
        
        product = products[0]
        print(f"✅ Product found: {product.get('title', 'No title')[:50]}...")
        
        # Check Buy Box price extraction
        stats = product.get('stats', {})
        current = stats.get('current', [])
        
        print(f"\n📊 Price Analysis:")
        print(f"   stats.current array length: {len(current)}")
        
        if len(current) > 18:
            # Index mapping: [0]=Amazon, [1]=New, [3]=Used, [11]=OfferCount, [18]=BuyBox
            amazon_price = current[0] if len(current) > 0 else -1
            new_price = current[1] if len(current) > 1 else -1
            used_price = current[3] if len(current) > 3 else -1
            offer_count = current[11] if len(current) > 11 else -1
            buybox_price_raw = current[18] if len(current) > 18 else -1
            
            print(f"   Raw prices (in pennies):")
            print(f"     Amazon: {amazon_price}")
            print(f"     New: {new_price}")
            print(f"     Used: {used_price}")
            print(f"     BuyBox: {buybox_price_raw}")
            print(f"     Offer Count: {offer_count}")
            
            # Convert to decimal
            def keepa_price_to_decimal(val):
                if val is None or val == -1:
                    return None
                return Decimal(str(val / 100.0))
            
            buybox_decimal = keepa_price_to_decimal(buybox_price_raw)
            amazon_decimal = keepa_price_to_decimal(amazon_price)
            new_decimal = keepa_price_to_decimal(new_price)
            
            print(f"\n💰 Converted prices:")
            print(f"     Amazon: {amazon_decimal}")
            print(f"     New: {new_decimal}")
            print(f"     BuyBox: {buybox_decimal}")
            
            # Check fallback logic
            if buybox_decimal is None:
                print(f"\n⚠️  BuyBox price is NULL, checking fallback...")
                if new_decimal is not None:
                    print(f"   ✅ Using NEW price as fallback: {new_decimal}")
                elif amazon_decimal is not None:
                    print(f"   ✅ Using AMAZON price as fallback: {amazon_decimal}")
                else:
                    print(f"   ❌ No fallback price available")
            else:
                print(f"   ✅ BuyBox price is valid: {buybox_decimal}")
            
            return buybox_decimal is not None
            
        else:
            print(f"❌ stats.current array too short (need at least 19 elements)")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ API timeout after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Test multiple ASINs"""
    print("🧪 KEEPA API BUY BOX PRICE PARSING TEST")
    print("=" * 60)
    
    # Test ASINs from the problematic list
    test_asins = [
        ('1546103597', 'US'),
        ('070234236X', 'UK'),
        ('B0F38CZDDF', 'US'),
        ('0114850003', 'UK')
    ]
    
    success_count = 0
    
    for asin, marketplace in test_asins:
        if test_keepa_api_single_asin(asin, marketplace):
            success_count += 1
            print(f"✅ {asin} ({marketplace}): SUCCESS")
        else:
            print(f"❌ {asin} ({marketplace}): FAILED")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Successful: {success_count}/{len(test_asins)}")
    print(f"   Success rate: {(success_count/len(test_asins)*100):.1f}%")
    
    if success_count == len(test_asins):
        print(f"\n🎉 All tests passed! Buy Box parsing is working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. There may be API connectivity or parsing issues.")

if __name__ == "__main__":
    main()




