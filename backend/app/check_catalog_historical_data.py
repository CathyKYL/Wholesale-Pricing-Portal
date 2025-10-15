"""
Check if any of our catalog ASINs have historical data with different approaches
"""
from sqlalchemy import create_engine, text
from config import settings
import requests
from datetime import datetime, timedelta

def check_catalog_historical_data():
    """Check if any catalog ASINs have historical data"""
    
    print("🔍 CHECKING CATALOG ASINs FOR HISTORICAL DATA")
    print("=" * 60)
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all ASINs from catalog
        catalog_rows = conn.execute(text("""
            SELECT asin, marketplace, title 
            FROM public.catalog_rows 
            ORDER BY asin
        """)).fetchall()
    
    print(f"Testing {len(catalog_rows)} catalog ASINs...")
    
    historical_asins = []
    preorder_asins = []
    error_asins = []
    
    for i, row in enumerate(catalog_rows):
        asin = row.asin
        marketplace = row.marketplace
        domain = 1 if marketplace == 'US' else 3
        
        print(f"\n🔍 {i+1}/{len(catalog_rows)}: {asin} ({marketplace})")
        
        try:
            # Try multiple approaches
            approaches = [
                {'name': 'Basic history', 'params': {'history': 1}},
                {'name': 'History + range 30', 'params': {'history': 1, 'range': 30}},
                {'name': 'History + range 90', 'params': {'history': 1, 'range': 90}},
                {'name': 'History + range 365', 'params': {'history': 1, 'range': 365}},
                {'name': 'History + since 30d', 'params': {'history': 1, 'since': int((datetime.now() - timedelta(days=30)).timestamp())}},
                {'name': 'History + since 90d', 'params': {'history': 1, 'since': int((datetime.now() - timedelta(days=90)).timestamp())}},
            ]
            
            best_result = None
            best_historical_count = 0
            
            for approach in approaches:
                try:
                    params = {
                        'key': settings.KEEPA_API_KEY,
                        'domain': domain,
                        'asin': asin,
                        **approach['params']
                    }
                    
                    response = requests.get("https://api.keepa.com/product", 
                                         params=params, timeout=30)
                    
                    if response.status_code != 200:
                        continue
                        
                    data = response.json()
                    
                    if 'error' in data:
                        continue
                    
                    products = data.get('products', [])
                    if not products:
                        continue
                    
                    product = products[0]
                    csv_data = product.get('csv', [])
                    
                    if len(csv_data) > 1 and csv_data[1]:
                        new_prices = csv_data[1]
                        if len(new_prices) >= 2:
                            keepa_epoch = datetime(2011, 12, 21)
                            
                            # Get all timestamps
                            timestamps = new_prices[::2]
                            dates = []
                            for ts in timestamps:
                                if ts != -1:
                                    date = keepa_epoch + timedelta(minutes=ts)
                                    dates.append(date.date())
                            
                            if dates:
                                today = datetime.now().date()
                                historical_dates = [d for d in dates if d <= today]
                                
                                if len(historical_dates) > best_historical_count:
                                    best_historical_count = len(historical_dates)
                                    best_result = {
                                        'approach': approach['name'],
                                        'total_dates': len(dates),
                                        'historical_dates': len(historical_dates),
                                        'future_dates': len(dates) - len(historical_dates),
                                        'date_range': f"{min(dates)} to {max(dates)}" if dates else "None"
                                    }
                
                except Exception as e:
                    continue
            
            if best_result:
                print(f"   Best result: {best_result['approach']}")
                print(f"   Total dates: {best_result['total_dates']}")
                print(f"   Historical: {best_result['historical_dates']}")
                print(f"   Future: {best_result['future_dates']}")
                print(f"   Range: {best_result['date_range']}")
                
                if best_result['historical_dates'] > 0:
                    historical_asins.append((asin, marketplace, best_result))
                    print(f"   ✅ HAS HISTORICAL DATA!")
                else:
                    preorder_asins.append((asin, marketplace, best_result))
                    print(f"   ❌ Pre-order (no historical data)")
            else:
                error_asins.append((asin, marketplace, "No data returned"))
                print(f"   ❌ No data returned")
                
        except Exception as e:
            error_asins.append((asin, marketplace, str(e)))
            print(f"   ❌ Error: {str(e)[:50]}...")
    
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    print(f"Total ASINs tested: {len(catalog_rows)}")
    print(f"ASINs with historical data: {len(historical_asins)}")
    print(f"Pre-order ASINs: {len(preorder_asins)}")
    print(f"Error ASINs: {len(error_asins)}")
    
    if historical_asins:
        print(f"\n✅ ASINs WITH HISTORICAL DATA:")
        print("-" * 60)
        for asin, marketplace, result in historical_asins:
            print(f"  {asin} ({marketplace}): {result['historical_dates']} historical dates")
    
    if preorder_asins:
        print(f"\n📅 PRE-ORDER ASINs:")
        print("-" * 60)
        for asin, marketplace, result in preorder_asins[:10]:  # Show first 10
            print(f"  {asin} ({marketplace}): {result['future_dates']} future dates")
        if len(preorder_asins) > 10:
            print(f"  ... and {len(preorder_asins) - 10} more")
    
    if error_asins:
        print(f"\n❌ ERROR ASINs:")
        print("-" * 60)
        for asin, marketplace, error in error_asins[:5]:  # Show first 5
            print(f"  {asin} ({marketplace}): {error}")
        if len(error_asins) > 5:
            print(f"  ... and {len(error_asins) - 5} more")
    
    return historical_asins, preorder_asins, error_asins

def main():
    historical_asins, preorder_asins, error_asins = check_catalog_historical_data()
    
    if historical_asins:
        print(f"\n🎉 FOUND {len(historical_asins)} ASINs WITH HISTORICAL DATA!")
        print(f"We can now run backfill for these ASINs")
    else:
        print(f"\n❌ NO ASINs WITH HISTORICAL DATA FOUND")
        print(f"All catalog ASINs appear to be pre-orders")

if __name__ == "__main__":
    main()




