"""
Daily Cache Test System
-----------------------
Runs today's daily cache scrape and replaces October 14, 2025 data in backfill_test.dynamic_data.
This allows testing the daily cache functionality with the backfill data.
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

def fetch_daily_cache_data(test=False):
    """Fetch current daily cache data from Keepa API."""
    print("\n" + "=" * 100)
    print(f"📡 FETCHING DAILY CACHE DATA (test={test})")
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
            
            # Daily mode: just current snapshot (cached for 1 hour by Keepa)
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin_string,
                'stats': 1
            }
            
            try:
                start_time = time.time()
                response = requests.get(url, params=params, timeout=60)
                duration_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"      ❌ API Error: {error_msg}")
                    
                    for asin in chunk:
                        log_raw_response(asin, marketplace, 'daily', {}, 'error', error_msg, 0, duration_ms)
                    
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
                    log_raw_response(asin, marketplace, 'daily', product, 'success', None, tokens_used / len(products), duration_ms)
                    
                    # Daily mode: just current snapshot
                    stats = product.get('stats', {})
                    current = stats.get('current', [])
                    
                    # Ensure array has enough elements
                    while len(current) < 34:
                        current.append(-1)
                    
                    def keepa_price_to_decimal(val):
                        """Convert Keepa price (pennies) to Decimal. Returns None if invalid."""
                        if val is None or val == -1:
                            return None
                        return Decimal(str(val / 100.0))
                    
                    # Extract BuyBox price from stats['current'] array
                    buybox_price = keepa_price_to_decimal(current[18]) # Index 18
                    
                    # Enhanced fallback logic for BuyBox price
                    # Priority: BuyBox > NEW > Amazon > Used > Collectible
                    if buybox_price is None:
                        new_price = keepa_price_to_decimal(current[1] if len(current) > 1 else -1)
                        amazon_price = keepa_price_to_decimal(current[0] if len(current) > 0 else -1)
                        used_price = keepa_price_to_decimal(current[2] if len(current) > 2 else -1)
                        collectible_price = keepa_price_to_decimal(current[4] if len(current) > 4 else -1)
                        
                        if new_price is not None:
                            buybox_price = new_price
                            print(f"         🔄 Using New price as fallback: ${buybox_price}")
                        elif amazon_price is not None:
                            buybox_price = amazon_price
                            print(f"         🔄 Using Amazon price as fallback: ${buybox_price}")
                        elif used_price is not None:
                            buybox_price = used_price
                            print(f"         🔄 Using Used price as fallback: ${buybox_price}")
                        elif collectible_price is not None:
                            buybox_price = collectible_price
                            print(f"         🔄 Using Collectible price as fallback: ${buybox_price}")
                    
                    # Extract sales rank from salesRanks dict
                    sales_ranks = product.get('salesRanks', {})
                    root_category = product.get('rootCategory')
                    current_sales_rank = None
                    
                    if root_category and str(root_category) in sales_ranks:
                        rank_history = sales_ranks[str(root_category)]
                        if isinstance(rank_history, list) and len(rank_history) >= 2:
                            current_sales_rank = rank_history[-1] if len(rank_history) % 2 == 1 else rank_history[-2]
                    
                    # Offer count from stats['current'][11]
                    offer_count = current[11] if current[11] and current[11] != -1 else None
                    
                    record = {
                        'asin': asin,
                        'marketplace': marketplace,
                        'fetch_date': datetime.now().date(),
                        'current_buybox_price': buybox_price,
                        'sales_rank_current': current_sales_rank if current_sales_rank and current_sales_rank != -1 else None,
                        'num_sellers': offer_count,
                        'last_updated': datetime.now()
                    }
                    all_records.append(record)
                    print(f"         📦 {asin}: ${buybox_price} (rank: {current_sales_rank})")
                
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
    print(f"📊 DAILY CACHE SUMMARY:")
    print(f"   Total records fetched: {len(df)}")
    print(f"   Total tokens used: {total_tokens}")
    if not df.empty:
        print(f"   Unique ASINs: {df['asin'].nunique()}")
        print(f"   Records with prices: {df['current_buybox_price'].notna().sum()}")
        print(f"   Records with sales rank: {df['sales_rank_current'].notna().sum()}")
    print("=" * 100)
    
    return df

def replace_october_14_data(df):
    """Replace October 14, 2025 data in backfill_test.dynamic_data with daily cache data."""
    if df.empty:
        print("⚠️  No daily cache data to replace with")
        return 0
    
    print(f"\n🔄 REPLACING OCTOBER 14, 2025 DATA")
    print("=" * 60)
    
    # Clean DataFrame
    df = df.replace({pd.NA: None, float('nan'): None})
    df = df.where(pd.notnull(df), None)
    
    replaced_count = 0
    deleted_count = 0
    
    try:
        with engine.connect() as conn:
            # First, delete existing October 14, 2025 data
            print("🗑️  Deleting existing October 14, 2025 data...")
            delete_result = conn.execute(text("""
                DELETE FROM backfill_test.dynamic_data 
                WHERE fetch_date = '2025-10-14'
            """))
            deleted_count = delete_result.rowcount
            print(f"   ✅ Deleted {deleted_count} existing records")
            
            # Insert new daily cache data
            print(f"💾 Inserting {len(df)} new daily cache records...")
            for idx, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO backfill_test.dynamic_data (
                        asin, marketplace, fetch_date,
                        current_buybox_price, sales_rank_current, num_sellers, last_updated
                    ) VALUES (
                        :asin, :marketplace, :fetch_date,
                        :buybox, :rank, :sellers, :updated
                    )
                """), {
                    'asin': row['asin'],
                    'marketplace': row['marketplace'],
                    'fetch_date': row['fetch_date'],
                    'buybox': row.get('current_buybox_price'),
                    'rank': row.get('sales_rank_current'),
                    'sellers': row.get('num_sellers'),
                    'updated': row.get('last_updated', datetime.now())
                })
                replaced_count += 1
            
            conn.commit()
        
        print(f"   ✅ Replaced {replaced_count} records with daily cache data")
        print(f"   📊 Summary: Deleted {deleted_count} old → Inserted {replaced_count} new")
        
        return replaced_count
    
    except Exception as e:
        print(f"   ❌ Error replacing data: {e}")
        return 0

def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description='Daily Cache Test System')
    parser.add_argument('--test', action='store_true', help='Test mode (3 ASINs only)')
    parser.add_argument('--daily', action='store_true', help='Run daily cache and replace October 14 data')
    
    args = parser.parse_args()
    
    if not any([args.test, args.daily]):
        parser.print_help()
        return
    
    if args.daily:
        mode_label = "TEST DAILY CACHE" if args.test else "FULL DAILY CACHE"
        print(f"\n⏳ {mode_label} - REPLACING OCTOBER 14, 2025 DATA")
        
        # Fetch daily cache data
        df = fetch_daily_cache_data(test=args.test)
        
        if not df.empty:
            # Replace October 14, 2025 data
            replaced_count = replace_october_14_data(df)
            
            if replaced_count > 0:
                print(f"\n🎉 DAILY CACHE SUCCESS!")
                print(f"   ✅ Replaced {replaced_count} records with today's data")
                print(f"   📅 Date: {datetime.now().date()}")
                
                if args.test:
                    print("\n📋 Sample daily cache data:")
                    print(df.head())
            else:
                print(f"\n❌ FAILED to replace data")
        else:
            print(f"\n❌ No daily cache data fetched")

if __name__ == "__main__":
    main()




