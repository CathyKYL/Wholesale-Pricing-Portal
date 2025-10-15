"""
Test what pricing options are available in Keepa responses
"""
import requests
from datetime import datetime, timedelta
from config import settings

def test_pricing_options():
    """Test what pricing options are available for our ASINs"""
    
    print("🧪 TESTING PRICING OPTIONS")
    print("=" * 60)
    
    test_asins = [
        ('1546103597', 'US', 1),  # One Piece set
        ('1637995059', 'US', 1),  # Jujutsu Kaisen
        ('070234236X', 'UK', 3),  # Hunger Games
    ]
    
    for asin, marketplace, domain in test_asins:
        print(f"\n🔍 Testing ASIN: {asin} ({marketplace})")
        print("-" * 50)
        
        try:
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin,
                'history': 1,
                'range': 30
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
            
            # Check basic product info
            title = product.get('title', 'Unknown')
            print(f"   Title: {title[:60]}...")
            
            # Check availability
            is_available = product.get('isAvailable', False)
            print(f"   Is available: {is_available}")
            
            # Check CSV data structure
            csv_data = product.get('csv', [])
            print(f"   CSV length: {len(csv_data)}")
            
            # Show what's in each CSV array
            print(f"\n📊 CSV DATA ANALYSIS:")
            for i, price_array in enumerate(csv_data):
                if price_array and len(price_array) > 0:
                    print(f"   CSV[{i}]: {len(price_array)} points")
                    if len(price_array) >= 2:
                        # Check first few values
                        sample_values = price_array[:6]
                        print(f"     Sample values: {sample_values}")
            
            # Check current stats
            stats = product.get('stats', {})
            current = stats.get('current', [])
            print(f"\n📈 CURRENT STATS:")
            print(f"   Current array length: {len(current)}")
            if len(current) > 0:
                print(f"   Current values: {current[:20]}...")  # First 20 values
                
                # Map known price indices
                price_mapping = {
                    0: "Amazon price",
                    1: "New price", 
                    2: "Used price",
                    3: "Used price (alternative)",
                    4: "Collectible price",
                    5: "Refurbished price",
                    6: "Rental price",
                    7: "Trade-in price",
                    8: "Trade-in price (alternative)",
                    9: "Rental price (alternative)",
                    10: "Rental price (alternative 2)",
                    11: "Number of sellers",
                    12: "Number of offers",
                    13: "Number of offers (alternative)",
                    14: "Number of offers (alternative 2)",
                    15: "Number of offers (alternative 3)",
                    16: "Number of offers (alternative 4)",
                    17: "Number of offers (alternative 5)",
                    18: "BuyBox price",
                    19: "BuyBox price (alternative)",
                    20: "BuyBox price (alternative 2)",
                    21: "BuyBox price (alternative 3)",
                    22: "BuyBox price (alternative 4)",
                    23: "BuyBox price (alternative 5)",
                    24: "BuyBox price (alternative 6)",
                    25: "BuyBox price (alternative 7)",
                    26: "BuyBox price (alternative 8)",
                    27: "BuyBox price (alternative 9)",
                    28: "BuyBox price (alternative 10)",
                    29: "BuyBox price (alternative 11)",
                    30: "BuyBox price (alternative 12)",
                    31: "BuyBox price (alternative 13)",
                    32: "BuyBox price (alternative 14)",
                    33: "BuyBox price (alternative 15)"
                }
                
                print(f"\n💰 PRICE BREAKDOWN:")
                for i in range(min(34, len(current))):
                    if current[i] != -1 and current[i] is not None:
                        price_cents = current[i]
                        price_dollars = price_cents / 100.0
                        price_type = price_mapping.get(i, f"Unknown price type {i}")
                        print(f"   {i:2d}: {price_type:<30} = ${price_dollars:.2f}")
            
            # Check if there are any other price-related fields
            print(f"\n🔍 OTHER PRICE FIELDS:")
            for key, value in product.items():
                if 'price' in key.lower() or 'cost' in key.lower():
                    print(f"   {key}: {value}")
            
            # Check offers
            offers = product.get('offers', [])
            if offers:
                print(f"\n🛒 OFFERS:")
                print(f"   Number of offers: {len(offers)}")
                for i, offer in enumerate(offers[:3]):  # Show first 3 offers
                    print(f"   Offer {i+1}: {offer}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    test_pricing_options()

if __name__ == "__main__":
    main()




