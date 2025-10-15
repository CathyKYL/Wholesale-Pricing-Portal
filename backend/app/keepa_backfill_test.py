"""
Keepa Backfill Test System
--------------------------
Modified version of keepa_ingestor.py that saves to backfill_test schema tables.
This allows safe testing of the backfill process without affecting production data.

Usage:
    # Test backfill (3 ASINs)
    python keepa_backfill_test.py --test --backfill
    
    # Full backfill (all ASINs)
    python keepa_backfill_test.py --backfill
"""

import sys
import os
import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import time
import json

import pandas as pd
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import settings

# ==================== CONFIGURATION ====================

# ASIN lists by marketplace
ASINS_UK = [
    '0076697940', '0114850003', '1529032172', '4027876040', '5103973863',
    '9123464127', '9124086843', '9124191604', '9124229466', '9124233684',
    '9766704961', '070234236X', '143914995X', '409537263X', '912424788X',
    'B0B2V9GK32'
]

ASINS_US = [
    '1529032172', '1546103597', '1637995059', '2067955810', '9123760915',
    '9124221546', '9124231983', '9124350893', '9124357294', '9766704961',
    '143914995X', '163799673X', '163799897X', '912434981X', 'B07XLKMWZT',
    'B09B8C4W3L', 'B09KQJNLP2', 'B0B3DB4Q75', 'B0B5N1DCJ2', 'B0CLF3H95P',
    'B0F38CZDDF', 'B0FCFLLM8L'
]

# Keepa domain mapping
KEEPA_DOMAINS = {
    'US': 1,
    'UK': 2
}

# Database engine
engine = create_engine(settings.DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

# ==================== HELPER FUNCTIONS ====================

# Keepa epoch: 2011-01-01 00:00:00 UTC
KEEPA_EPOCH = datetime(2011, 1, 1, tzinfo=timezone.utc)

def keepa_minutes_to_dt(minutes):
    """Convert Keepa timestamp (minutes since 2011-01-01) to datetime."""
    if minutes == -1 or minutes is None:
        return None
    return KEEPA_EPOCH + timedelta(minutes=minutes)

def log_raw_response(asin, marketplace, mode, raw_response, status='success', error_msg=None, tokens_used=0, duration_ms=0):
    """Log raw Keepa API response to backfill_test.keepa_raw_log table."""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO backfill_test.keepa_raw_log 
                (asin, marketplace, mode, raw_response, status, error_message, tokens_consumed, duration_ms)
                VALUES (:asin, :marketplace, :mode, :raw_response, :status, :error_msg, :tokens, :duration)
            """), {
                'asin': asin,
                'marketplace': marketplace,
                'mode': mode,
                'raw_response': json.dumps(raw_response),
                'status': status,
                'error_msg': error_msg,
                'tokens': tokens_used,
                'duration': duration_ms
            })
            conn.commit()
    except Exception as e:
        print(f"      ⚠️  Failed to log raw response: {e}")

def parse_keepa_history(product, marketplace):
    """Parse Keepa product history data into daily snapshots."""
    asin = product.get('asin', '')
    
    def keepa_price_to_decimal(val):
        """Convert Keepa price (pennies) to Decimal. Returns None if invalid."""
        if val is None or val == -1:
            return None
        return Decimal(str(val / 100.0))
    
    def parse_history_array(history_array):
        """Parse Keepa history array [time1, val1, time2, val2, ...] into dict {date: value}"""
        result = {}
        if not history_array or not isinstance(history_array, list):
            return result
        
        for i in range(0, len(history_array), 2):
            if i + 1 < len(history_array):
                time_minutes = history_array[i]
                value = history_array[i + 1]
                
                if time_minutes != -1 and value is not None and value != -1:
                    date_obj = keepa_minutes_to_dt(time_minutes)
                    if date_obj:
                        date_key = date_obj.date()
                        result[date_key] = value
        
        return result
    
    # Extract price histories from csv array
    csv_data = product.get('csv', [])
    
    # Parse individual price histories
    amazon_prices = parse_history_array(csv_data[0] if len(csv_data) > 0 and csv_data[0] is not None else [])
    new_prices = parse_history_array(csv_data[1] if len(csv_data) > 1 and csv_data[1] is not None else [])
    used_prices = parse_history_array(csv_data[3] if len(csv_data) > 3 and csv_data[3] is not None else [])
    buybox_prices = parse_history_array(csv_data[18] if len(csv_data) > 18 and csv_data[18] is not None else [])
    
    # Extract sales rank history
    sales_ranks = {}
    root_category = product.get('rootCategory')
    if root_category:
        rank_history = product.get('salesRanks', {}).get(str(root_category), [])
        for i in range(0, len(rank_history) if isinstance(rank_history, list) else 0, 2):
            if i + 1 < len(rank_history):
                time_minutes = rank_history[i]
                rank_value = rank_history[i + 1]
                
                if time_minutes != -1 and rank_value is not None and rank_value != -1:
                    date_obj = keepa_minutes_to_dt(time_minutes)
                    if date_obj:
                        date_key = date_obj.date()
                        sales_ranks[date_key] = int(rank_value)
    
    # Get all unique dates from all histories
    all_dates = set()
    all_dates.update(amazon_prices.keys())
    all_dates.update(new_prices.keys())
    all_dates.update(used_prices.keys())
    all_dates.update(buybox_prices.keys())
    all_dates.update(sales_ranks.keys())
    
    # If no historical data, try to get current snapshot
    if not all_dates:
        stats = product.get('stats', {})
        current = stats.get('current', [])
        
        while len(current) < 34:
            current.append(-1)
        
        buybox_price = keepa_price_to_decimal(current[18] if len(current) > 18 else -1)
        amazon_price_val = keepa_price_to_decimal(current[0] if len(current) > 0 else -1)
        new_price = keepa_price_to_decimal(current[1] if len(current) > 1 else -1)
        
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
    
    # Filter to only historical dates within the last 360 days
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=360)
    
    # Sanity check: ensure no future dates
    future_dates = [d for d in all_dates if d > today]
    if future_dates:
        print(f"      ⚠️  WARNING: Found {len(future_dates)} future dates, filtering them out")
        print(f"         Future date range: {min(future_dates)} to {max(future_dates)}")
    
    # Filter to only historical dates within 360 days
    historical_dates = [d for d in all_dates if d >= cutoff_date and d <= today]
    
    print(f"      📊 Date filtering: {len(all_dates)} total → {len(historical_dates)} historical (last 360 days)")
    if historical_dates:
        print(f"      ✅ 360d window: {min(historical_dates)} → {max(historical_dates)} ({len(historical_dates)} points, future=0)")
    
    records = []
    for date_key in sorted(historical_dates):
        # Get values for this date
        amazon_price = keepa_price_to_decimal(amazon_prices.get(date_key))
        new_price = keepa_price_to_decimal(new_prices.get(date_key))
        used_price = keepa_price_to_decimal(used_prices.get(date_key))
        buybox_price = keepa_price_to_decimal(buybox_prices.get(date_key))
        
        # Fallback chain for BuyBox price
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
            'num_sellers': None,
            'last_updated': datetime.now()
        })
    
    # If no records were created, fall back to current snapshot
    if not records:
        print(f"      ⚠️  No historical records created, falling back to current snapshot")
        
        stats = product.get('stats', {})
        current = stats.get('current', [])
        
        if len(current) == 0:
            print(f"      ⚠️  No current data available, using most recent historical data")
            
            most_recent_date = None
            best_price = None
            best_sales_rank = None
            
            price_arrays = [
                (csv_data[0], "Amazon price"),
                (csv_data[1], "New price"), 
                (csv_data[2], "Used price"),
                (csv_data[4], "Collectible price"),
            ]
            
            if len(csv_data) > 18 and csv_data[18]:
                price_arrays.append((csv_data[18], "BuyBox price"))
            
            for price_array, price_type in price_arrays:
                if price_array and len(price_array) >= 2:
                    for i in range(len(price_array) - 2, -1, -2):
                        if i + 1 < len(price_array):
                            timestamp = price_array[i]
                            price = price_array[i + 1]
                            
                            if timestamp != -1 and price != -1:
                                date = keepa_minutes_to_dt(timestamp)
                                if date:
                                    if date.date() <= datetime.now().date():
                                        if most_recent_date is None or date.date() > most_recent_date:
                                            most_recent_date = date.date()
                                            best_price = price
                                            print(f"      📅 Using {price_type} from {most_recent_date}: ${price/100:.2f}")
                                        break
            
            if best_price is not None:
                buybox_price = Decimal(str(best_price / 100.0))
            else:
                buybox_price = None
                print(f"      ❌ No valid historical prices found")
            
            if root_category and str(root_category) in product.get('salesRanks', {}):
                rank_history = product.get('salesRanks', {})[str(root_category)]
                if isinstance(rank_history, list) and len(rank_history) >= 2:
                    for i in range(len(rank_history) - 2, -1, -2):
                        if i + 1 < len(rank_history):
                            timestamp = rank_history[i]
                            rank = rank_history[i + 1]
                            
                            if timestamp != -1 and rank != -1:
                                date = keepa_minutes_to_dt(timestamp)
                                if date and date.date() <= datetime.now().date():
                                    best_sales_rank = rank
                                    break
            
            current_rank = best_sales_rank if best_sales_rank and best_sales_rank != -1 else None
            num_sellers = None
            
        else:
            print(f"      ✅ Using current data")
            
            while len(current) < 34:
                current.append(-1)
            
            buybox_price = keepa_price_to_decimal(current[18] if len(current) > 18 else -1)
            amazon_price_val = keepa_price_to_decimal(current[0] if len(current) > 0 else -1)
            new_price = keepa_price_to_decimal(current[1] if len(current) > 1 else -1)
            used_price = keepa_price_to_decimal(current[2] if len(current) > 2 else -1)
            collectible_price = keepa_price_to_decimal(current[4] if len(current) > 4 else -1)
            
            if buybox_price is None:
                if new_price is not None:
                    buybox_price = new_price
                    print(f"      🔄 Using New price as fallback: ${buybox_price}")
                elif amazon_price_val is not None:
                    buybox_price = amazon_price_val
                    print(f"      🔄 Using Amazon price as fallback: ${buybox_price}")
                elif used_price is not None:
                    buybox_price = used_price
                    print(f"      🔄 Using Used price as fallback: ${buybox_price}")
                elif collectible_price is not None:
                    buybox_price = collectible_price
                    print(f"      🔄 Using Collectible price as fallback: ${buybox_price}")
            
            current_rank = None
            if root_category and str(root_category) in product.get('salesRanks', {}):
                rank_history = product.get('salesRanks', {})[str(root_category)]
                if isinstance(rank_history, list) and len(rank_history) >= 2:
                    current_rank = rank_history[-1] if len(rank_history) % 2 == 1 else rank_history[-2]
            
            num_sellers = current[11] if len(current) > 11 and current[11] != -1 else None
        
        records.append({
            'asin': asin,
            'marketplace': marketplace,
            'fetch_date': most_recent_date if 'most_recent_date' in locals() and most_recent_date else datetime.now().date(),
            'current_buybox_price': buybox_price,
            'sales_rank_current': current_rank if current_rank and current_rank != -1 else None,
            'num_sellers': num_sellers,
            'last_updated': datetime.now()
        })
    
    return records

def fetch_keepa_data(mode="backfill", test=False):
    """Fetch product data from Keepa API."""
    print("\n" + "=" * 100)
    print(f"📡 FETCHING KEEPA DATA (mode={mode.upper()}, test={test})")
    print("=" * 100)
    
    if not settings.KEEPA_API_KEY:
        print("❌ ERROR: KEEPA_API_KEY not found in environment")
        return pd.DataFrame()
    
    # Determine ASINs to fetch
    if test:
        asins_to_fetch = {
            'US': [ASINS_US[0]],  # 1 US ASIN
            'UK': ASINS_UK[:2]     # 2 UK ASINs
        }
        print(f"🧪 TEST MODE: Fetching 3 ASINs (1 US, 2 UK)")
    else:
        asins_to_fetch = {
            'US': ASINS_US,
            'UK': ASINS_UK
        }
        print(f"📊 FULL MODE: Fetching {len(ASINS_US)} US + {len(ASINS_UK)} UK ASINs")
    
    all_records = []
    total_tokens = 0
    
    for marketplace, asins in asins_to_fetch.items():
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
                'days': 360,
                'buybox': 1,
                'offers': 20
            }
            
            try:
                start_time = time.time()
                response = requests.get(url, params=params, timeout=60)
                duration_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"      ❌ API Error: {error_msg}")
                    
                    for asin in chunk:
                        log_raw_response(asin, marketplace, mode, {}, 'error', error_msg, 0, duration_ms)
                    
                    continue
                
                data = response.json()
                
                if 'error' in data:
                    error_msg = data['error'].get('message', 'Unknown error')
                    print(f"      ❌ Keepa Error: {error_msg}")
                    continue
                
                tokens_used = data.get('tokensConsumed', 0)
                total_tokens += tokens_used
                
                products = data.get('products', [])
                print(f"      ✅ Received {len(products)} products (tokens: {tokens_used}, {duration_ms}ms)")
                
                # Process each product
                for product in products:
                    asin = product.get('asin', '')
                    
                    # Log raw response
                    log_raw_response(asin, marketplace, mode, product, 'success', None, tokens_used / len(products), duration_ms)
                    
                    # Parse history into daily records
                    records = parse_keepa_history(product, marketplace)
                    all_records.extend(records)
                    print(f"         📦 {asin}: {len(records)} historical records")
                
                # Rate limiting
                time.sleep(1)
            
            except requests.exceptions.Timeout:
                print(f"      ⏱️  Timeout after 60s")
                continue
            except Exception as e:
                print(f"      ❌ Error: {e}")
                continue
    
    # Convert to DataFrame
    df = pd.DataFrame(all_records)
    
    print(f"\n" + "=" * 100)
    print(f"📊 FETCH SUMMARY:")
    print(f"   Total records fetched: {len(df)}")
    print(f"   Total tokens used: {total_tokens}")
    if not df.empty:
        print(f"   Unique ASINs: {df['asin'].nunique()}")
        print(f"   Date range: {df['fetch_date'].min()} to {df['fetch_date'].max()}")
    print("=" * 100)
    
    return df

def forward_fill_prices(df):
    """Two-phase fill: Forward-fill first, then backward-fill for remaining gaps."""
    if df.empty:
        return df
    
    print(f"\n🔄 Two-phase price fill (Forward → Backward)...")
    
    df = df.sort_values(['asin', 'marketplace', 'fetch_date']).copy()
    price_column = 'current_buybox_price'
    
    nulls_before = df[price_column].isna().sum()
    
    # STEP 1: Forward fill
    df[price_column] = df.groupby(['asin', 'marketplace'])[price_column].ffill()
    nulls_after_ffill = df[price_column].isna().sum()
    ffill_count = nulls_before - nulls_after_ffill
    
    # STEP 2: Backward fill
    df[price_column] = df.groupby(['asin', 'marketplace'])[price_column].bfill()
    nulls_after_bfill = df[price_column].isna().sum()
    bfill_count = nulls_after_ffill - nulls_after_bfill
    
    total_filled = ffill_count + bfill_count
    
    if total_filled > 0:
        if bfill_count > 0:
            print(f"   ✅ BuyBox Price: Filled {ffill_count} (forward) + {bfill_count} (backward) = {total_filled} total")
        else:
            print(f"   ✅ BuyBox Price: Filled {ffill_count} (forward only)")
    else:
        print(f"   📊 No gaps found - all prices already complete!")
    
    return df

def save_to_postgres(df):
    """Save records to backfill_test.dynamic_data table."""
    if df.empty:
        print("⚠️  No data to save")
        return 0, df
    
    # Forward-fill prices before saving
    df = forward_fill_prices(df)
    
    # Clean DataFrame
    df = df.replace({pd.NA: None, float('nan'): None})
    df = df.where(pd.notnull(df), None)
    
    print(f"\n💾 Saving {len(df)} records to backfill_test.dynamic_data...")
    
    saved_count = 0
    
    try:
        with engine.connect() as conn:
            for idx, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO backfill_test.dynamic_data (
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
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description='Keepa Backfill Test System')
    parser.add_argument('--test', action='store_true', help='Test mode (3 ASINs only)')
    parser.add_argument('--backfill', action='store_true', help='Backfill 360 days of history')
    
    args = parser.parse_args()
    
    if not any([args.test, args.backfill]):
        parser.print_help()
        return
    
    if args.backfill:
        mode_label = "TEST BACKFILL" if args.test else "FULL BACKFILL"
        print(f"\n⏳ {mode_label} MODE (360 days) - SAVING TO backfill_test.dynamic_data")
        df = fetch_keepa_data(mode="backfill", test=args.test)
        if not df.empty:
            saved_count, filled_df = save_to_postgres(df)
            if args.test:
                print("\n📋 Sample historical data (AFTER forward-fill):")
                print(filled_df.head(10))

if __name__ == "__main__":
    main()




