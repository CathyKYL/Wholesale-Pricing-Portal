"""
Keepa Data Ingestion System
----------------------------
Dual-phase system for historical backfill and daily updates.

Features:
- Initial backfill of 360 days of historical data
- Daily cached fetches to update each ASIN once a day
- Data persistence in PostgreSQL (static + dynamic schemas)
- Trend computations based on stored data
- Scheduling for automated daily updates

Usage:
    # Test mode (3 ASINs)
    python keepa_ingestor.py --test
    
    # Backfill 360 days
    python keepa_ingestor.py --backfill
    
    # Daily update (cached)
    python keepa_ingestor.py --daily
    
    # Compute trends from stored data
    python keepa_ingestor.py --compute-trends
    
    # Run as scheduled service
    python keepa_ingestor.py --schedule
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
import schedule
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import settings

# ==================== CONFIGURATION ====================

# ASIN lists by marketplace
# Note: Some ASINs need leading zeros to be valid
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
    """
    Log raw Keepa API response to database for debugging.
    
    Args:
        asin: Amazon ASIN
        marketplace: 'US' or 'UK'
        mode: 'backfill' or 'daily'
        raw_response: Raw JSON response from Keepa
        status: 'success', 'partial', or 'error'
        error_msg: Error message if status is 'error'
        tokens_used: Number of Keepa API tokens used
        duration_ms: API call duration in milliseconds
    """
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
    """
    Parse Keepa product history data into daily snapshots.
    
    Keepa returns price history as arrays of timestamps and prices.
    We convert this into daily records for easier analysis.
    
    Args:
        product: Raw product dict from Keepa API
        marketplace: 'US' or 'UK'
    
    Returns:
        List of dictionaries, one per day with available data
    """
    asin = product.get('asin', '')
    
    # Keepa time is in minutes since Keepa epoch (1 Jan 2011)
    # Use the global KEEPA_EPOCH constant
    
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
                        # Keep the last value for each date
                        result[date_key] = value
        
        return result
    
    # Extract price histories from csv array
    csv_data = product.get('csv', [])
    
    # Parse individual price histories
    amazon_prices = parse_history_array(csv_data[0] if len(csv_data) > 0 and csv_data[0] is not None else [])
    new_prices = parse_history_array(csv_data[1] if len(csv_data) > 1 and csv_data[1] is not None else [])
    used_prices = parse_history_array(csv_data[3] if len(csv_data) > 3 and csv_data[3] is not None else [])
    buybox_prices = parse_history_array(csv_data[18] if len(csv_data) > 18 and csv_data[18] is not None else [])
    
    # Extract sales rank history from salesRanks dictionary
    # NOTE: Sales ranks are stored as actual integers, NOT multiplied by 100 like prices
    sales_ranks = {}
    root_category = product.get('rootCategory')
    if root_category:
        rank_history = product.get('salesRanks', {}).get(str(root_category), [])
        # Parse sales rank history WITHOUT price conversion
        for i in range(0, len(rank_history) if isinstance(rank_history, list) else 0, 2):
            if i + 1 < len(rank_history):
                time_minutes = rank_history[i]
                rank_value = rank_history[i + 1]
                
                if time_minutes != -1 and rank_value is not None and rank_value != -1:
                    date_obj = keepa_minutes_to_dt(time_minutes)
                    if date_obj:
                        date_key = date_obj.date()
                        # Sales rank is already an integer, don't convert like prices!
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
        
        # Ensure array has enough elements
        while len(current) < 34:
            current.append(-1)
        
        # Create one record with current values
        buybox_price = keepa_price_to_decimal(current[18] if len(current) > 18 else -1)
        amazon_price_val = keepa_price_to_decimal(current[0] if len(current) > 0 else -1)
        new_price = keepa_price_to_decimal(current[1] if len(current) > 1 else -1)
        used_price_val = keepa_price_to_decimal(current[3] if len(current) > 3 else -1)
        
        # Fallback chain for BuyBox price (use best available price)
        # Priority: BuyBox > NEW > Amazon (NOT using USED - often unreliable)
        if buybox_price is None:
            if new_price is not None:
                buybox_price = new_price
            elif amazon_price_val is not None:
                buybox_price = amazon_price_val
        
        # Get current sales rank
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
    
    # Create records for each date
    # Filter to only keep dates within the last 360 days (no future dates)
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
        
        # Get values for this date (or None if not available)
        amazon_price = keepa_price_to_decimal(amazon_prices.get(date_key))
        new_price = keepa_price_to_decimal(new_prices.get(date_key))
        used_price = keepa_price_to_decimal(used_prices.get(date_key))
        buybox_price = keepa_price_to_decimal(buybox_prices.get(date_key))
        
        # Fallback chain for BuyBox price (use best available price)
        # Priority: BuyBox > NEW > Amazon
        # Note: NOT using USED price as fallback - csv[3] often contains sales rank data instead!
        if buybox_price is None:
            if new_price is not None:
                buybox_price = new_price
            elif amazon_price is not None:
                buybox_price = amazon_price
        
        sales_rank = sales_ranks.get(date_key)
        
        # Ensure sales_rank is valid integer or None (not NaN)
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
    
    # If no records were created (all dates filtered out), fall back to current snapshot
    if not records:
        print(f"      ⚠️  No historical records created, falling back to current snapshot")
        
        stats = product.get('stats', {})
        current = stats.get('current', [])
        
        # Check if current data is available
        if len(current) == 0:
            print(f"      ⚠️  No current data available, using most recent historical data")
            
            # Use the most recent historical data from CSV arrays
            most_recent_date = None
            best_price = None
            best_sales_rank = None
            
            # Check all price arrays for the most recent data
            price_arrays = [
                (csv_data[0], "Amazon price"),
                (csv_data[1], "New price"), 
                (csv_data[2], "Used price"),
                (csv_data[4], "Collectible price"),
            ]
            
            # Add BuyBox price if available
            if len(csv_data) > 18 and csv_data[18]:
                price_arrays.append((csv_data[18], "BuyBox price"))
            
            for price_array, price_type in price_arrays:
                if price_array and len(price_array) >= 2:
                    # Get the most recent price from this array
                    for i in range(len(price_array) - 2, -1, -2):  # Go backwards through timestamps
                        if i + 1 < len(price_array):
                            timestamp = price_array[i]
                            price = price_array[i + 1]
                            
                            if timestamp != -1 and price != -1:
                                date = keepa_minutes_to_dt(timestamp)
                                if date:
                                    # Only use historical dates (not future)
                                    if date.date() <= datetime.now().date():
                                        if most_recent_date is None or date.date() > most_recent_date:
                                            most_recent_date = date.date()
                                            best_price = price
                                            print(f"      📅 Using {price_type} from {most_recent_date}: ${price/100:.2f}")
                                        break
            
            # Convert price to decimal
            if best_price is not None:
                buybox_price = Decimal(str(best_price / 100.0))
            else:
                buybox_price = None
                print(f"      ❌ No valid historical prices found")
            
            # Get most recent sales rank
            if root_category and str(root_category) in product.get('salesRanks', {}):
                rank_history = product.get('salesRanks', {})[str(root_category)]
                if isinstance(rank_history, list) and len(rank_history) >= 2:
                    # Find the most recent historical rank
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
            # Use current data if available
            print(f"      ✅ Using current data")
            
            # Ensure array has enough elements
            while len(current) < 34:
                current.append(-1)
            
            # Extract current prices
            buybox_price = keepa_price_to_decimal(current[18] if len(current) > 18 else -1)
            amazon_price_val = keepa_price_to_decimal(current[0] if len(current) > 0 else -1)
            new_price = keepa_price_to_decimal(current[1] if len(current) > 1 else -1)
            used_price = keepa_price_to_decimal(current[2] if len(current) > 2 else -1)
            collectible_price = keepa_price_to_decimal(current[4] if len(current) > 4 else -1)
            
            # Enhanced fallback chain for BuyBox price
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
            
            # Get current sales rank
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


# ==================== MAIN FUNCTIONS ====================

def fetch_keepa_data(mode="daily", test=False):
    """
    Fetch product data from Keepa API.
    
    Args:
        mode: 'daily' (cached, current snapshot) or 'backfill' (360 days history)
        test: If True, only fetch 3 ASINs (1 US, 2 UK) for testing
    
    Returns:
        pandas DataFrame with product data
    """
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
            
            # Parameters differ based on mode
            params = {
                'key': settings.KEEPA_API_KEY,
                'domain': domain,
                'asin': asin_string,
            }
            
            if mode == 'backfill':
                # Request 360 days of history
                # days=360 requests last 360 days of data
                # buybox=1 enables BuyBox price data
                # offers=20 gets offer count data
                params['days'] = 360
                params['buybox'] = 1
                params['offers'] = 20
            else:
                # Daily mode: just current snapshot (cached for 1 hour by Keepa)
                params['stats'] = 1
            
            try:
                start_time = time.time()
                response = requests.get(url, params=params, timeout=60)
                duration_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"      ❌ API Error: {error_msg}")
                    
                    # Log error
                    for asin in chunk:
                        log_raw_response(asin, marketplace, mode, {}, 'error', error_msg, 0, duration_ms)
                    
                    continue
                
                data = response.json()
                
                # Check for API errors
                if 'error' in data:
                    error_msg = data['error'].get('message', 'Unknown error')
                    print(f"      ❌ Keepa Error: {error_msg}")
                    continue
                
                # Track tokens used
                tokens_used = data.get('tokensConsumed', 0)
                total_tokens += tokens_used
                
                products = data.get('products', [])
                print(f"      ✅ Received {len(products)} products (tokens: {tokens_used}, {duration_ms}ms)")
                
                # Process each product
                for product in products:
                    asin = product.get('asin', '')
                    
                    # Log raw response
                    log_raw_response(asin, marketplace, mode, product, 'success', None, tokens_used / len(products), duration_ms)
                    
                    if mode == 'backfill':
                        # Parse history into daily records
                        records = parse_keepa_history(product, marketplace)
                        all_records.extend(records)
                        print(f"         📦 {asin}: {len(records)} historical records")
                    else:
                        # Daily mode: just current snapshot
                        # Keepa stores prices in 'stats' -> 'current' array
                        # Index mapping: [0]=Amazon, [1]=New, [3]=Used, [11]=OfferCount, [18]=BuyBox
                        
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
                            # salesRanks format: {category_id: [time1, rank1, time2, rank2, ...]}
                            rank_history = sales_ranks[str(root_category)]
                            if isinstance(rank_history, list) and len(rank_history) >= 2:
                                # Get last rank value (last odd-indexed element)
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
                
                # Rate limiting: avoid hammering API
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
    """
    Two-phase fill: Forward-fill first, then backward-fill for remaining gaps.
    
    Keepa only tracks price changes, not every day. To get complete daily prices:
    
    STEP 1 - FORWARD FILL (primary): Carry last known price forward to future dates
    STEP 2 - BACKWARD FILL (cleanup): For dates before first price, fill backwards
    
    Example timeline:
    - Sept 1-14: No price data yet → BACKWARD FILL will fix this
    - Sept 15: First price appears ($29.99)
    - Sept 16-20: No data (price unchanged) → FORWARD FILL carries $29.99
    - Sept 21: Price changed to $27.99
    - Sept 22-30: No data → FORWARD FILL carries $27.99
    
    This ensures NO gaps in pricing data across the entire date range.
    
    Args:
        df: pandas DataFrame with product data
    
    Returns:
        DataFrame with prices filled in both directions per ASIN/marketplace
    """
    if df.empty:
        return df
    
    print(f"\n🔄 Two-phase price fill (Forward → Backward)...")
    
    # Sort by ASIN, marketplace, and date to ensure proper filling
    df = df.sort_values(['asin', 'marketplace', 'fetch_date']).copy()
    
    # Fill BuyBox price within each ASIN/marketplace group
    # This ensures prices don't bleed across different products
    price_column = 'current_buybox_price'
    
    # Count nulls at start
    nulls_before = df[price_column].isna().sum()
    
    # STEP 1: Forward fill (PRIMARY METHOD)
    # Carry last known price forward to all future dates
    df[price_column] = df.groupby(['asin', 'marketplace'])[price_column].ffill()
    nulls_after_ffill = df[price_column].isna().sum()
    ffill_count = nulls_before - nulls_after_ffill
    
    # STEP 2: Backward fill (CLEANUP FOR EARLY DATES)
    # For dates before first price, carry first known price backwards
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
    """
    Save or update records in backfill_test.dynamic_data table.
    
    Uses ON CONFLICT to handle duplicates (upsert).
    
    Args:
        df: pandas DataFrame with product data
    
    Returns:
        Tuple of (saved_count, filled_df) - number of records saved and the forward-filled DataFrame
    """
    if df.empty:
        print("⚠️  No data to save")
        return 0, df
    
    # Forward-fill prices before saving (carry last known price forward)
    df = forward_fill_prices(df)
    
    # Clean DataFrame: replace NaN with None (required for PostgreSQL)
    df = df.replace({pd.NA: None, float('nan'): None})
    # Also use pandas built-in method
    df = df.where(pd.notnull(df), None)
    
    print(f"\n💾 Saving {len(df)} records to backfill_test.dynamic_data...")
    
    saved_count = 0
    
    try:
        with engine.connect() as conn:
            for idx, row in df.iterrows():
                # Upsert: insert or update on conflict
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
        return saved_count, df  # Return both count and filled DataFrame
    
    except Exception as e:
        print(f"   ❌ Error saving to database: {e}")
        # Re-raise the exception so the script fails (important for GitHub Actions)
        raise


def compute_trends():
    """
    Compute rolling trends from stored data in backfill_test.dynamic_data.
    
    Materializes results into backfill_test.keepa_trends table (weekly aggregates).
    Does NOT call Keepa API - uses only stored data.
    
    Returns:
        Number of trend records computed
    """
    print("\n" + "=" * 100)
    print("📈 COMPUTING TRENDS FROM STORED DATA (backfill_test.dynamic_data)")
    print("=" * 100)
    
    try:
        # Read data from database
        query = """
            SELECT 
                asin, marketplace, fetch_date,
                current_buybox_price, sales_rank_current
            FROM backfill_test.dynamic_data
            WHERE fetch_date >= CURRENT_DATE - INTERVAL '360 days'
            ORDER BY asin, marketplace, fetch_date
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("⚠️  No data available to compute trends")
            return 0
        
        print(f"📊 Loaded {len(df)} records from last 360 days")
        
        # Convert fetch_date to datetime
        df['fetch_date'] = pd.to_datetime(df['fetch_date'])
        
        # Group by ASIN and marketplace
        trends_records = []
        
        for (asin, marketplace), group in df.groupby(['asin', 'marketplace']):
            group = group.sort_values('fetch_date')
            
            # Resample to weekly data
            group.set_index('fetch_date', inplace=True)
            
            # Weekly aggregation
            weekly = group.resample('W-MON').agg({
                'current_buybox_price': ['mean', 'min', 'max', 'std'],
                'sales_rank_current': ['mean', 'min', 'max', 'std']
            })
            
            # Flatten column names
            weekly.columns = ['_'.join(col).strip() for col in weekly.columns.values]
            weekly.reset_index(inplace=True)
            
            # Compute trend percentages
            for idx, row in weekly.iterrows():
                week_start = row['fetch_date']
                
                # Skip if week_start is NaT (Not a Time)
                if pd.isna(week_start):
                    continue
                
                # Get 7d and 30d ago data for trend calculation
                data_7d_ago = weekly[weekly['fetch_date'] <= week_start - timedelta(days=7)]
                data_30d_ago = weekly[weekly['fetch_date'] <= week_start - timedelta(days=30)]
                
                price_trend_7d = None
                price_trend_30d = None
                
                # Check if current price exists and is not NaN
                current_price = row['current_buybox_price_mean']
                if pd.notna(current_price) and current_price is not None:
                    # 7-day trend
                    if not data_7d_ago.empty:
                        old_price = data_7d_ago.iloc[-1]['current_buybox_price_mean']
                        if pd.notna(old_price) and old_price is not None and old_price > 0:
                            price_trend_7d = ((current_price - old_price) / old_price * 100)
                    
                    # 30-day trend
                    if not data_30d_ago.empty:
                        old_price = data_30d_ago.iloc[-1]['current_buybox_price_mean']
                        if pd.notna(old_price) and old_price is not None and old_price > 0:
                            price_trend_30d = ((current_price - old_price) / old_price * 100)
                
                trends_records.append({
                    'asin': asin,
                    'marketplace': marketplace,
                    'week_start_date': week_start.date(),
                    'avg_buybox_price': row['current_buybox_price_mean'],
                    'min_buybox_price': row['current_buybox_price_min'],
                    'max_buybox_price': row['current_buybox_price_max'],
                    'price_volatility': row['current_buybox_price_std'],
                    'avg_sales_rank': row['sales_rank_current_mean'],
                    'min_sales_rank': row['sales_rank_current_min'],
                    'max_sales_rank': row['sales_rank_current_max'],
                    'rank_volatility': row['sales_rank_current_std'],
                    'price_trend_7d': price_trend_7d,
                    'price_trend_30d': price_trend_30d,
                    'computed_at': datetime.now()
                })
        
        # Save to backfill_test.keepa_trends
        trends_df = pd.DataFrame(trends_records)
        
        # Clean DataFrame: replace NaN with None (required for PostgreSQL)
        trends_df = trends_df.replace({pd.NA: None, float('nan'): None})
        trends_df = trends_df.where(pd.notnull(trends_df), None)
        
        print(f"💾 Saving {len(trends_df)} weekly trend records to backfill_test.keepa_trends...")
        
        with engine.connect() as conn:
            for idx, row in trends_df.iterrows():
                conn.execute(text("""
                    INSERT INTO backfill_test.keepa_trends (
                        asin, marketplace, week_start_date,
                        avg_buybox_price, min_buybox_price, max_buybox_price, price_volatility,
                        avg_sales_rank, min_sales_rank, max_sales_rank, rank_volatility,
                        price_trend_7d, price_trend_30d, computed_at
                    ) VALUES (
                        :asin, :marketplace, :week,
                        :avg_price, :min_price, :max_price, :price_vol,
                        :avg_rank, :min_rank, :max_rank, :rank_vol,
                        :trend_7d, :trend_30d, :computed
                    )
                    ON CONFLICT (asin, marketplace, week_start_date)
                    DO UPDATE SET
                        avg_buybox_price = EXCLUDED.avg_buybox_price,
                        min_buybox_price = EXCLUDED.min_buybox_price,
                        max_buybox_price = EXCLUDED.max_buybox_price,
                        price_volatility = EXCLUDED.price_volatility,
                        avg_sales_rank = EXCLUDED.avg_sales_rank,
                        min_sales_rank = EXCLUDED.min_sales_rank,
                        max_sales_rank = EXCLUDED.max_sales_rank,
                        rank_volatility = EXCLUDED.rank_volatility,
                        price_trend_7d = EXCLUDED.price_trend_7d,
                        price_trend_30d = EXCLUDED.price_trend_30d,
                        computed_at = EXCLUDED.computed_at
                """), {
                    'asin': row['asin'],
                    'marketplace': row['marketplace'],
                    'week': row['week_start_date'],
                    'avg_price': row.get('avg_buybox_price'),
                    'min_price': row.get('min_buybox_price'),
                    'max_price': row.get('max_buybox_price'),
                    'price_vol': row.get('price_volatility'),
                    'avg_rank': row.get('avg_sales_rank'),
                    'min_rank': row.get('min_sales_rank'),
                    'max_rank': row.get('max_sales_rank'),
                    'rank_vol': row.get('rank_volatility'),
                    'trend_7d': row.get('price_trend_7d'),
                    'trend_30d': row.get('price_trend_30d'),
                    'computed': row.get('computed_at')
                })
            
            conn.commit()
        
        print(f"   ✅ Saved {len(trends_df)} trend records")
        print("=" * 100)
        
        return len(trends_df)
    
    except Exception as e:
        import traceback
        print(f"❌ Error computing trends: {e}")
        print("\n📋 Full error traceback:")
        traceback.print_exc()
        return 0


# ==================== SCHEDULING ====================

def daily_update_job():
    """Daily job to fetch and update current data."""
    print(f"\n⏰ Running daily update job at {datetime.now()}")
    df = fetch_keepa_data(mode="daily", test=False)
    saved_count, filled_df = save_to_postgres(df)
    compute_trends()
    print(f"✅ Daily update complete at {datetime.now()}")


def run_scheduler():
    """Run the scheduler for daily updates at 03:00."""
    print("\n" + "=" * 100)
    print("⏰ STARTING SCHEDULER")
    print("=" * 100)
    print(f"📅 Daily updates scheduled at 03:00")
    print(f"🕐 Current time: {datetime.now()}")
    print(f"⏹️  Press Ctrl+C to stop")
    print("=" * 100)
    
    # Schedule daily job at 03:00
    schedule.every().day.at("03:00").do(daily_update_job)
    
    # Run the scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n⏹️  Scheduler stopped by user")


# ==================== MAIN ====================

def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description='Keepa Data Ingestion System')
    parser.add_argument('--test', action='store_true', help='Test mode (3 ASINs only)')
    parser.add_argument('--backfill', action='store_true', help='Backfill 360 days of history')
    parser.add_argument('--daily', action='store_true', help='Daily cached update')
    parser.add_argument('--compute-trends', action='store_true', help='Compute trends from stored data')
    parser.add_argument('--schedule', action='store_true', help='Run as scheduled service')
    
    args = parser.parse_args()
    
    # If no mode specified, show help
    if not any([args.test, args.backfill, args.daily, args.compute_trends, args.schedule]):
        parser.print_help()
        return
    
    # Execute based on mode
    if args.backfill:
        # Backfill mode: 360 days of history
        mode_label = "TEST BACKFILL" if args.test else "FULL BACKFILL"
        print(f"\n⏳ {mode_label} MODE (360 days)")
        df = fetch_keepa_data(mode="backfill", test=args.test)
        if not df.empty:
            saved_count, filled_df = save_to_postgres(df)
            compute_trends()
            if args.test:
                print("\n📋 Sample historical data (AFTER forward-fill):")
                print(filled_df.head(10))
    
    elif args.test:
        # Test mode (daily snapshot)
        print("\n🧪 TEST MODE (Daily Snapshot)")
        df = fetch_keepa_data(mode="daily", test=True)
        if not df.empty:
            saved_count, filled_df = save_to_postgres(df)
            print("\n📋 Sample data (AFTER forward-fill):")
            print(filled_df.head())
    
    elif args.daily:
        print("\n📅 DAILY UPDATE MODE")
        df = fetch_keepa_data(mode="daily", test=False)
        if not df.empty:
            saved_count, filled_df = save_to_postgres(df)
            compute_trends()
    
    elif args.compute_trends:
        print("\n📈 COMPUTE TRENDS ONLY")
        compute_trends()
    
    elif args.schedule:
        run_scheduler()


if __name__ == "__main__":
    main()

