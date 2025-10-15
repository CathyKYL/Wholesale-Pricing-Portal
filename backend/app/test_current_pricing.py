"""
Test current pricing from offers data for pre-order products
"""
import requests
from datetime import datetime, timedelta
from config import settings

def test_current_pricing():
    """Test getting current pricing from offers data"""
    
    print("🧪 TESTING CURRENT PRICING FROM OFFERS")
    print("=" * 60)
    
    # Test ASINs from the spreadsheet
    test_asins = [
        ('1546103597', 'US', 1),  # One Piece set
        ('1637995059', 'US', 1),  # Jujutsu Kaisen
        ('070234236X', 'UK', 3),  # Hunger Games
        ('B0F38CZDDF', 'US', 1),  # Hunger Games Deluxe
        ('B0FCFLLM8L', 'US', 1),  # Demon Slayer
    ]
    
    for asin, marketplace, domain in test_asins:
        print(f"\n🔍 Testing ASIN: {asin} ({marketplace})")
        print("-" * 50)
        
        try:
            # Use offers parameter to get current pricing
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin,
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
            
            # Check offers for current pricing
            offers = product.get('offers', [])
            if offers:
                print(f"\n   🛒 CURRENT OFFERS: {len(offers)}")
                
                # Analyze offers
                fba_offers = []
                amazon_offers = []
                other_offers = []
                
                for offer in offers:
                    is_fba = offer.get('isFBA', False)
                    is_amazon = offer.get('isAmazon', False)
                    is_preorder = offer.get('isPreorder', False)
                    condition = offer.get('condition', 0)
                    
                    # Get current price from offerCSV
                    offer_csv = offer.get('offerCSV', [])
                    if offer_csv and len(offer_csv) >= 2:
                        # Get most recent price (last non-zero price)
                        current_price = None
                        for i in range(len(offer_csv) - 1, 0, -2):
                            if offer_csv[i] != 0 and offer_csv[i] != -1:
                                current_price = offer_csv[i] / 100.0
                                break
                        
                        if current_price:
                            offer_info = {
                                'price': current_price,
                                'condition': condition,
                                'is_fba': is_fba,
                                'is_amazon': is_amazon,
                                'is_preorder': is_preorder,
                                'seller_id': offer.get('sellerId', 'Unknown')
                            }
                            
                            if is_amazon:
                                amazon_offers.append(offer_info)
                            elif is_fba:
                                fba_offers.append(offer_info)
                            else:
                                other_offers.append(offer_info)
                
                # Sort by price
                all_offers = sorted(amazon_offers + fba_offers + other_offers, key=lambda x: x['price'])
                
                print(f"     Amazon offers: {len(amazon_offers)}")
                print(f"     FBA offers: {len(fba_offers)}")
                print(f"     Other offers: {len(other_offers)}")
                
                if all_offers:
                    print(f"\n   💰 PRICE RANGE:")
                    print(f"     Lowest: ${all_offers[0]['price']:.2f} ({all_offers[0]['seller_id']})")
                    print(f"     Highest: ${all_offers[-1]['price']:.2f} ({all_offers[-1]['seller_id']})")
                    
                    # Show best offers
                    print(f"\n   🏆 BEST OFFERS:")
                    for i, offer in enumerate(all_offers[:5]):  # Top 5
                        seller_type = "Amazon" if offer['is_amazon'] else "FBA" if offer['is_fba'] else "Other"
                        preorder_text = " (Pre-order)" if offer['is_preorder'] else ""
                        print(f"     {i+1}. ${offer['price']:.2f} - {seller_type}{preorder_text}")
                    
                    # Use the best offer as current price
                    best_offer = all_offers[0]
                    current_price = best_offer['price']
                    
                    print(f"\n   ✅ CURRENT PRICE: ${current_price:.2f}")
                    print(f"   📅 Status: {'Pre-order' if best_offer['is_preorder'] else 'Available'}")
                    print(f"   🏪 Seller: {best_offer['seller_id']}")
                    
                    # This is the price we should use for the backfill
                    print(f"   💾 This price should be used for historical data")
                    
                else:
                    print(f"   ❌ No valid offers found")
            else:
                print(f"   ❌ No offers available")
            
            # Check if there's any historical data in CSV
            csv_data = product.get('csv', [])
            if len(csv_data) > 1 and csv_data[1]:  # New prices
                new_prices = csv_data[1]
                if len(new_prices) >= 2:
                    keepa_epoch = datetime(2011, 12, 21)
                    
                    # Get all dates
                    dates = []
                    for i in range(0, len(new_prices), 2):
                        if i + 1 < len(new_prices):
                            timestamp = new_prices[i]
                            if timestamp != -1:
                                date = keepa_epoch + timedelta(minutes=timestamp)
                                dates.append(date.date())
                    
                    if dates:
                        dates.sort()
                        today = datetime.now().date()
                        historical_dates = [d for d in dates if d <= today]
                        future_dates = [d for d in dates if d > today]
                        
                        print(f"\n   📊 CSV DATA SUMMARY:")
                        print(f"     Total price points: {len(dates)}")
                        print(f"     Historical: {len(historical_dates)}")
                        print(f"     Future: {len(future_dates)}")
                        
                        if future_dates:
                            print(f"     Future date range: {min(future_dates)} to {max(future_dates)}")
                        
                        if historical_dates:
                            print(f"     Historical date range: {min(historical_dates)} to {max(historical_dates)}")
                        else:
                            print(f"     ⚠️  No historical data - this is a pre-order product")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    test_current_pricing()

if __name__ == "__main__":
    main()




