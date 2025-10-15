"""
Targeted backfill for specific ASINs
This script runs backfill only for the problematic ASINs to test the fix
"""
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import requests
import time
import json
from sqlalchemy import create_engine, text
from config import settings

# Target ASINs from the user's list
TARGET_ASINS = {
    'US': ['1546103597', '1637995059', '163799673X', '163799897X', '2067955810', 'B0F38CZDDF', 'B0FCFLLM8L'],
    'UK': ['0114850003', '070234236X', '4027876040', '9124233684', '912424788X']
}

KEEPA_DOMAINS = {'US': 1, 'UK': 2}

def keepa_price_to_decimal(val):
    """Convert Keepa price (pennies) to Decimal. Returns None if invalid."""
    if val is None or val == -1:
        return None
    return Decimal(str(val / 100.0))

def parse_keepa_history(product, marketplace):
    """Parse Keepa product history data into daily snapshots with Buy Box fallback"""
    asin = product.get('asin', '')
    
    # Keepa time is in minutes since Keepa epoch (21 Dec 2011)
    keepa_epoch = datetime(2011, 12, 21)
    
    def parse_history_array(history_array):
        """Parse Keepa history array [time1, val1, time2, val2, ...] into dict {date: value}"""
        result = {}
        if not history_array or not isinstance(history_array, list):
            return result
        
        for i in range(0, len(history_array), 2):
            if i + 1 < len(history_array):
                time_minutes = history_array[i]
                value = history_array[i + 1]
                
                if time_minutes and value is not None and value != -1:
                    date_obj = keepa_epoch + timedelta(minutes=time_minutes)
                    date_key = date_obj.date()
                    result[date_key] = value
        
        return result
    
    # Extract price histories from csv array
    csv_data = product.get('csv', [])
    
    # Parse individual price histories
    amazon_prices = parse_history_array(csv_data[0] if len(csv_data) > 0 else [])
    new_prices = parse_history_array(csv_data[1] if len(csv_data) > 1 else [])
    used_prices = parse_history_array(csv_data[3] if len(csv_data) > 3 else [])
    buybox_prices = parse_history_array(csv_data[18] if len(csv_data) > 18 else [])
    
    # Extract sales rank history
    sales_ranks = {}
    root_category = product.get('rootCategory')
    if root_category:
        rank_history = product.get('salesRanks', {}).get(str(root_category), [])
        for i in range(0, len(rank_history) if isinstance(rank_history, list) else 0, 2):
            if i + 1 < len(rank_history):
                time_minutes = rank_history[i]
                rank_value = rank_history[i + 1]
                
                if time_minutes and rank_value is not None and rank_value != -1:
                    date_obj = keepa_epoch + timedelta(minutes=time_minutes)
                    date_key = date_obj.date()
                    sales_ranks[date_key] = int(rank_value)
    
    # Get all unique dates
    all_dates = set()
    all_dates.update(amazon_prices.keys())
    all_dates.update(new_prices.keys())
    all_dates.update(used_prices.keys())
    all_dates.update(buybox_prices.keys())
    all_dates.update(sales_ranks.keys())
    
    # If no historical data, try current snapshot
    if not all_dates:
        stats = product.get('stats', {})
        current = stats.get('current', [])
        
        while len(current) < 34:
            current.append(-1)
        
        buybox_price = keepa_price_to_decimal(current[18] if len(current) > 18 else -1)
        amazon_price_val = keepa_price_to_decimal(current[0] if len(current) > 0 else -1)
        new_price = keepa_price_to_decimal(current[1] if len(current) > 1 else -1)
        
        # Apply fallback logic
        if buybox_price is None:
            if new_price is not None:
                buybox_price = new_price
            elif amazon_price_val is not None:
                buybox_price = amazon_price_val
        
        current_rank = None
        if root_category and str(root_category) in product.get('salesRanks', {}):
            rank_history = product.get('salesRanks', {})[str(root_category)]
            if isinstance(rank_history, list) and len(rank_history) >= 2:
                current_rank = rank_history[-1] if len(rank_history) % 2 == 1 else rank_history[-2]
        
        return [{
            'asin': asin,
            'marketplace': marketplace,
            'fetch_date': datetime.now().date(),
            'current_buybox_price': buybox_price,
            'sales_rank_current': current_rank if current_rank and current_rank != -1 else None,
            'num_sellers': current[11] if len(current) > 11 and current[11] != -1 else None,
            'last_updated': datetime.now()
        }]
    
    # Create records for each date with fallback logic
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=400)
    
    records = []
    for date_key in sorted(all_dates):
        if date_key < cutoff_date or date_key > today:
            continue
        
        amazon_price = keepa_price_to_decimal(amazon_prices.get(date_key))
        new_price = keepa_price_to_decimal(new_prices.get(date_key))
        used_price = keepa_price_to_decimal(used_prices.get(date_key))
        buybox_price = keepa_price_to_decimal(buybox_prices.get(date_key))
        
        # Apply fallback logic for BuyBox price
        if buybox_price is None:
            if new_price is not None:
                buybox_price = new_price
            elif amazon_price is not None:
                buybox_price = amazon_price
        
        sales_rank = sales_ranks.get(date_key)
        if sales_rank is not None and sales_rank != -1:
            try:
                sales_rank = int(sales_rank)
            except (ValueError, TypeError):
                sales_rank = None
        else:
            sales_rank = None
        
        records.append({
            'asin': asin,
            'marketplace': marketplace,
            'fetch_date': date_key,
            'current_buybox_price': buybox_price,
            'sales_rank_current': sales_rank,
            'num_sellers': None,  # Not available in historical data
            'last_updated': datetime.now()
        })
    
    return records

def fetch_targeted_data():
    """Fetch data for target ASINs only"""
    print("🎯 TARGETED BACKFILL FOR PROBLEMATIC ASINS")
    print("=" * 60)
    
    all_records = []
    total_tokens = 0
    
    for marketplace, asins in TARGET_ASINS.items():
        if not asins:
            continue
        
        print(f"\n📍 Processing {marketplace} marketplace ({len(asins)} ASINs)...")
        domain = KEEPA_DOMAINS[marketplace]
        
        # Keepa allows max 100 ASINs per request
        chunks = [asins[i:i+100] for i in range(0, len(asins), 100)]
        
        for chunk_num, chunk in enumerate(chunks, 1):
            print(f"   Chunk {chunk_num}/{len(chunks)}: {len(chunk)} ASINs...")
            
            asin_string = ",".join(chunk)
            url = "https://api.keepa.com/product"
            
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin_string,
                'history': 1,
                'range': 365,
                'stats': 365
            }
            
            try:
                start_time = time.time()
                response = requests.get(url, params=params, timeout=60)
                duration_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code != 200:
                    print(f"      ❌ API Error: {response.status_code}")
                    continue
                
                data = response.json()
                
                if 'error' in data:
                    print(f"      ❌ Keepa Error: {data['error']}")
                    continue
                
                tokens_used = data.get('tokensConsumed', 0)
                total_tokens += tokens_used
                
                products = data.get('products', [])
                print(f"      ✅ Received {len(products)} products (tokens: {tokens_used})")
                
                for product in products:
                    asin = product.get('asin', '')
                    records = parse_keepa_history(product, marketplace)
                    all_records.extend(records)
                    print(f"         📦 {asin}: {len(records)} historical records")
                
                time.sleep(1)  # Rate limiting
            
            except Exception as e:
                print(f"      ❌ Error: {e}")
                continue
    
    df = pd.DataFrame(all_records)
    print(f"\n📊 FETCH SUMMARY:")
    print(f"   Total records: {len(df)}")
    print(f"   Total tokens: {total_tokens}")
    if not df.empty:
        print(f"   Unique ASINs: {df['asin'].nunique()}")
        print(f"   Date range: {df['fetch_date'].min()} to {df['fetch_date'].max()}")
    
    return df

def forward_fill_prices(df):
    """Apply forward and backward fill to prices"""
    if df.empty:
        return df
    
    print(f"\n🔄 Applying price fill...")
    df = df.sort_values(['asin', 'marketplace', 'fetch_date']).copy()
    
    price_column = 'current_buybox_price'
    nulls_before = df[price_column].isna().sum()
    
    # Forward fill
    df[price_column] = df.groupby(['asin', 'marketplace'])[price_column].ffill()
    nulls_after_ffill = df[price_column].isna().sum()
    ffill_count = nulls_before - nulls_after_ffill
    
    # Backward fill
    df[price_column] = df.groupby(['asin', 'marketplace'])[price_column].bfill()
    nulls_after_bfill = df[price_column].isna().sum()
    bfill_count = nulls_after_ffill - nulls_after_bfill
    
    total_filled = ffill_count + bfill_count
    print(f"   ✅ Filled {total_filled} price gaps ({ffill_count} forward + {bfill_count} backward)")
    
    return df

def save_to_postgres(df):
    """Save records to database"""
    if df.empty:
        print("⚠️  No data to save")
        return 0, df
    
    df = forward_fill_prices(df)
    df = df.replace({pd.NA: None, float('nan'): None})
    df = df.where(pd.notnull(df), None)
    
    print(f"\n💾 Saving {len(df)} records to PostgreSQL...")
    
    engine = create_engine(settings.DATABASE_URL, echo=False)
    saved_count = 0
    
    try:
        with engine.connect() as conn:
            for idx, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO dynamic.keepa_daily_data (
                        asin, marketplace, fetch_date,
                        current_buybox_price, sales_rank_current, num_sellers, last_updated
                    ) VALUES (
                        :asin, :marketplace, :fetch_date,
                        :buybox, :rank, :sellers, :updated
                    )
                    ON CONFLICT (asin, marketplace, fetch_date)
                    DO UPDATE SET
                        current_buybox_price = EXCLUDED.current_buybox_price,
                        sales_rank_current = EXCLUDED.sales_rank_current,
                        num_sellers = EXCLUDED.num_sellers,
                        last_updated = EXCLUDED.last_updated
                """), {
                    'asin': row['asin'],
                    'marketplace': row['marketplace'],
                    'fetch_date': row['fetch_date'],
                    'buybox': row.get('current_buybox_price'),
                    'rank': row.get('sales_rank_current'),
                    'sellers': row.get('num_sellers'),
                    'updated': row.get('last_updated', datetime.now())
                })
                saved_count += 1
            
            conn.commit()
        
        print(f"   ✅ Saved/updated {saved_count} records")
        return saved_count, df
    
    except Exception as e:
        print(f"   ❌ Error saving to database: {e}")
        return 0, df

def main():
    """Main function"""
    print("🚀 Starting targeted backfill...")
    
    # Fetch data
    df = fetch_targeted_data()
    
    if not df.empty:
        # Save to database
        saved_count, filled_df = save_to_postgres(df)
        
        print(f"\n🎉 TARGETED BACKFILL COMPLETE!")
        print(f"   Records saved: {saved_count}")
        
        # Verify results
        print(f"\n🔍 Verifying results...")
        engine = create_engine(settings.DATABASE_URL, echo=False)
        with engine.connect() as conn:
            for asin in [item for sublist in TARGET_ASINS.values() for item in sublist]:
                result = conn.execute(text("""
                    SELECT COUNT(*) as total, 
                           COUNT(CASE WHEN current_buybox_price IS NOT NULL THEN 1 END) as with_price,
                           MIN(fetch_date) as first_date,
                           MAX(fetch_date) as last_date
                    FROM dynamic.keepa_daily_data
                    WHERE asin = :asin
                """), {'asin': asin}).fetchone()
                
                if result:
                    total, with_price, first_date, last_date = result
                    print(f"   {asin}: {total} rows, {with_price} with prices, {first_date} to {last_date}")
        
        engine.dispose()
    else:
        print("❌ No data fetched - backfill failed")

if __name__ == "__main__":
    main()




