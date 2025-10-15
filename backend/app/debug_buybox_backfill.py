"""
🧭 Buy Box Backfill Diagnostic Script
=====================================
This script diagnoses why specific ASINs are missing backfill data or have NULL buybox_price values.

Purpose:
- Check if backfill was executed for affected ASINs
- Verify data exists in dynamic.keepa_daily_data table
- Identify NULL buybox_price patterns
- Analyze Keepa API response logs
- Provide root cause analysis and recommendations

Usage:
    python debug_buybox_backfill.py
"""

import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from config import settings

# ==================== CONFIGURATION ====================

# ASINs reported as problematic by user
# Based on the Excel screenshot and user query
AFFECTED_ASINS = [
    '0114850003',     # UK - Row 2 in screenshot (FIXED: added leading 0)
    '070234236X',     # UK - Row 4
    '1546103597',     # US - Row 6
    '1637995059',     # US - Row 10
    '163799673X',     # US - Row 11
    '163799897X',     # US - Row 12
    '2067955810',     # US - Row 13
    '4027876040',     # UK - Row 14 (FIXED: this is UK, not US)
    '9124233684',     # UK - Row 24
    '912424788X',     # UK - Row 25
    'B0F38CZDDF',     # US - Row 38
    'B0FCFLLM8L'      # US - Row 39 (note: L at end, not 8)
]

# Expected backfill range
BACKFILL_DAYS = 365
TODAY = datetime.now().date()
EXPECTED_START_DATE = TODAY - timedelta(days=BACKFILL_DAYS)

# ==================== DATABASE CONNECTION ====================

print("\n" + "=" * 100)
print("🧭 BUY BOX BACKFILL DIAGNOSTIC REPORT")
print("=" * 100)
print(f"📅 Report Date: {TODAY}")
print(f"🔍 Investigating {len(AFFECTED_ASINS)} ASINs")
print(f"📊 Expected backfill range: {EXPECTED_START_DATE} to {TODAY} ({BACKFILL_DAYS} days)")
print("=" * 100)

try:
    # Create database engine
    engine = create_engine(settings.DATABASE_URL, echo=False)
    print("\n✅ Database connection established")
    
except Exception as e:
    print(f"\n❌ ERROR: Could not connect to database")
    print(f"   Details: {e}")
    sys.exit(1)

# ==================== DIAGNOSTIC CHECKS ====================

print("\n" + "=" * 100)
print("SECTION 1: ASIN EXISTENCE CHECK")
print("=" * 100)
print("\nChecking if ASINs exist in database and their data coverage...\n")

with engine.connect() as conn:
    # Check each ASIN
    asin_results = []
    
    for asin in AFFECTED_ASINS:
        result = conn.execute(text("""
            SELECT 
                asin,
                marketplace,
                COUNT(*) as total_rows,
                MIN(fetch_date) as first_date,
                MAX(fetch_date) as last_date,
                COUNT(CASE WHEN current_buybox_price IS NULL THEN 1 END) as null_buybox,
                COUNT(CASE WHEN current_buybox_price IS NOT NULL THEN 1 END) as has_buybox,
                COUNT(CASE WHEN sales_rank_current IS NULL THEN 1 END) as null_rank,
                COUNT(CASE WHEN num_sellers IS NULL THEN 1 END) as null_sellers
            FROM dynamic.keepa_daily_data
            WHERE asin = :asin
            GROUP BY asin, marketplace
            ORDER BY marketplace
        """), {'asin': asin}).fetchall()
        
        if result:
            for row in result:
                asin_results.append(row)
        else:
            # ASIN not found in database at all
            asin_results.append((asin, 'UNKNOWN', 0, None, None, 0, 0, 0, 0))
    
    # Display results in table format
    print(f"{'ASIN':<15} {'Market':<8} {'Rows':<6} {'First Date':<12} {'Last Date':<12} {'NULL BB':<9} {'Has BB':<8} {'Status':<20}")
    print("-" * 100)
    
    issues_found = []
    
    for row in asin_results:
        asin, marketplace, total_rows, first_date, last_date, null_buybox, has_buybox, null_rank, null_sellers = row
        
        # Determine status
        if total_rows == 0:
            status = "❌ NO DATA"
            issues_found.append((asin, marketplace, "NO_DATA", "ASIN not found in database"))
        elif total_rows < 30:
            status = "⚠️  INSUFFICIENT DATA"
            issues_found.append((asin, marketplace, "INSUFFICIENT", f"Only {total_rows} rows (expected ~{BACKFILL_DAYS})"))
        elif null_buybox == total_rows:
            status = "❌ ALL NULL PRICES"
            issues_found.append((asin, marketplace, "ALL_NULL", "All buybox prices are NULL"))
        elif null_buybox > 0:
            pct = (null_buybox / total_rows) * 100
            status = f"⚠️  {null_buybox} NULL ({pct:.1f}%)"
            issues_found.append((asin, marketplace, "PARTIAL_NULL", f"{null_buybox}/{total_rows} rows have NULL buybox"))
        else:
            status = "✅ OK"
        
        first_str = str(first_date) if first_date else "N/A"
        last_str = str(last_date) if last_date else "N/A"
        
        print(f"{asin:<15} {marketplace:<8} {total_rows:<6} {first_str:<12} {last_str:<12} {null_buybox:<9} {has_buybox:<8} {status:<20}")

print("\n" + "=" * 100)
print("SECTION 2: BACKFILL EXECUTION ANALYSIS")
print("=" * 100)
print("\nChecking Keepa API logs to see if backfill was attempted for these ASINs...\n")

with engine.connect() as conn:
    # Check raw log table for backfill attempts
    log_results = conn.execute(text("""
        SELECT 
            asin,
            marketplace,
            mode,
            status,
            error_message,
            tokens_consumed,
            fetch_timestamp
        FROM dynamic.keepa_raw_log
        WHERE asin = ANY(:asins)
          AND mode = 'backfill'
        ORDER BY fetch_timestamp DESC
    """), {'asins': AFFECTED_ASINS}).fetchall()
    
    if log_results:
        print(f"Found {len(log_results)} backfill API call records:\n")
        print(f"{'ASIN':<15} {'Market':<8} {'Mode':<10} {'Status':<10} {'Tokens':<8} {'Date':<20} {'Error'}")
        print("-" * 100)
        
        for row in log_results:
            asin, marketplace, mode, status, error, tokens, created = row
            error_str = error if error else ""
            if len(error_str) > 40:
                error_str = error_str[:37] + "..."
            print(f"{asin:<15} {marketplace:<8} {mode:<10} {status:<10} {tokens:<8} {str(created):<20} {error_str}")
    else:
        print("⚠️  NO BACKFILL LOGS FOUND for these ASINs!")
        print("\n🔍 Checking if backfill was ever run...\n")
        
        # Check if backfill exists for ANY ASIN
        any_backfill = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM dynamic.keepa_raw_log
            WHERE mode = 'backfill'
        """)).fetchone()
        
        if any_backfill[0] == 0:
            print("❌ NO BACKFILL has ever been executed!")
            print("   ROOT CAUSE: Backfill task has never run for any ASIN")
        else:
            print(f"✅ Backfill exists for other ASINs ({any_backfill[0]} records)")
            print("   ROOT CAUSE: These specific ASINs were NOT included in backfill")

print("\n" + "=" * 100)
print("SECTION 3: DAILY CACHE VS BACKFILL COMPARISON")
print("=" * 100)
print("\nComparing daily cache records vs backfill records...\n")

with engine.connect() as conn:
    # Get daily cache records (recent dates)
    daily_records = conn.execute(text("""
        SELECT asin, marketplace, COUNT(*) as count, MAX(fetch_date) as latest
        FROM dynamic.keepa_daily_data
        WHERE asin = ANY(:asins)
          AND fetch_date >= CURRENT_DATE - 7
        GROUP BY asin, marketplace
    """), {'asins': AFFECTED_ASINS}).fetchall()
    
    print(f"{'ASIN':<15} {'Market':<8} {'Recent Rows':<12} {'Latest Date':<12} {'Status'}")
    print("-" * 70)
    
    for row in daily_records:
        asin, marketplace, count, latest = row
        if count > 0:
            status = "✅ Daily cache working"
        else:
            status = "❌ No recent data"
        print(f"{asin:<15} {marketplace:<8} {count:<12} {str(latest):<12} {status}")
    
    if not daily_records:
        print("⚠️  No recent daily cache records found")

print("\n" + "=" * 100)
print("SECTION 4: ASIN CONFIGURATION CHECK")
print("=" * 100)
print("\nVerifying if ASINs are in the configuration (keepa_ingestor.py)...\n")

# Import ASIN lists from keepa_ingestor
try:
    from keepa_ingestor import ASINS_UK, ASINS_US
    
    print(f"UK ASINs configured: {len(ASINS_UK)}")
    print(f"US ASINs configured: {len(ASINS_US)}")
    print()
    
    missing_from_config = []
    
    for asin in AFFECTED_ASINS:
        in_uk = asin in ASINS_UK
        in_us = asin in ASINS_US
        
        # Check with leading zero
        asin_with_zero = '0' + asin if not asin.startswith('0') and not asin.startswith('B') else asin
        in_uk_zero = asin_with_zero in ASINS_UK
        in_us_zero = asin_with_zero in ASINS_US
        
        if not (in_uk or in_us or in_uk_zero or in_us_zero):
            missing_from_config.append(asin)
            print(f"❌ {asin:<15} NOT FOUND in configuration")
        else:
            marketplace = "UK" if (in_uk or in_uk_zero) else "US"
            actual_asin = asin if (in_uk or in_us) else asin_with_zero
            print(f"✅ {actual_asin:<15} Found in {marketplace} configuration")
    
    if missing_from_config:
        print(f"\n⚠️  {len(missing_from_config)} ASINs are missing from configuration!")
        print("   ROOT CAUSE: These ASINs will be skipped by backfill and daily updates")
    
except ImportError as e:
    print(f"❌ Could not import ASIN configuration: {e}")

print("\n" + "=" * 100)
print("SECTION 5: KEEPA API RESPONSE SAMPLE")
print("=" * 100)
print("\nChecking recent Keepa API responses for these ASINs...\n")

with engine.connect() as conn:
    # Get most recent raw response
    sample_response = conn.execute(text("""
        SELECT asin, marketplace, raw_response, status, error_message
        FROM dynamic.keepa_raw_log
        WHERE asin = ANY(:asins)
        ORDER BY fetch_timestamp DESC
        LIMIT 3
    """), {'asins': AFFECTED_ASINS}).fetchall()
    
    if sample_response:
        import json
        
        for idx, (asin, marketplace, raw_json, status, error) in enumerate(sample_response, 1):
            print(f"\n--- Sample {idx}: {asin} ({marketplace}) ---")
            print(f"Status: {status}")
            
            if error:
                print(f"Error: {error}")
            
            if raw_json:
                try:
                    data = json.loads(raw_json)
                    
                    # Check for BuyBox price in response
                    if 'stats' in data:
                        current = data['stats'].get('current', [])
                        if len(current) > 18:
                            bb_price = current[18]
                            print(f"BuyBox Price (raw): {bb_price} (converted: {bb_price / 100 if bb_price != -1 else 'NULL'})")
                        else:
                            print("⚠️  stats.current array too short")
                    
                    # Check for historical data
                    if 'csv' in data:
                        csv_data = data['csv']
                        if len(csv_data) > 18 and csv_data[18]:
                            print(f"Historical BuyBox data points: {len(csv_data[18]) // 2}")
                        else:
                            print("⚠️  No historical BuyBox data in csv[18]")
                    
                except json.JSONDecodeError:
                    print("⚠️  Could not parse JSON response")
    else:
        print("⚠️  No API responses found in logs")

print("\n" + "=" * 100)
print("SUMMARY & ROOT CAUSE ANALYSIS")
print("=" * 100)
print("\n📋 ISSUES DETECTED:\n")

if issues_found:
    for asin, marketplace, issue_type, description in issues_found:
        print(f"  • {asin} ({marketplace}): {description}")
else:
    print("  ✅ No issues detected - all ASINs have complete data")

print("\n" + "=" * 100)
print("RECOMMENDATIONS")
print("=" * 100)
print("""
Based on the diagnostic results above, here are the recommended actions:

1️⃣  IF ASINS ARE MISSING FROM CONFIGURATION:
   → Add them to ASINS_UK or ASINS_US in backend/app/keepa_ingestor.py
   → Re-run backfill: python keepa_ingestor.py --backfill

2️⃣  IF BACKFILL WAS NEVER EXECUTED:
   → Run: python keepa_ingestor.py --backfill
   → This will populate 365 days of history for all configured ASINs

3️⃣  IF BACKFILL RAN BUT SOME ASINS HAVE NULL PRICES:
   → Check Keepa API responses in Section 5
   → Verify these products actually have BuyBox price history on Amazon
   → Some products may legitimately have no BuyBox (out of stock, discontinued)

4️⃣  IF DAILY CACHE HAS NULL PRICES:
   → Check if products are currently available on Amazon
   → Verify Keepa API key has sufficient permissions
   → Check for rate limiting or API errors in logs

5️⃣  IF ASIN FORMATTING IS INCORRECT:
   → Some ASINs need leading zeros (e.g., '114850003' → '0114850003')
   → Check catalog_rows table for correct ASIN format
   → Update configuration with correct format

6️⃣  TO RE-RUN BACKFILL FOR SPECIFIC ASINS:
   → Option A: Update configuration and run full backfill
   → Option B: Manually call Keepa API for missing ASINs (requires custom script)

""")

print("=" * 100)
print("🏁 DIAGNOSTIC COMPLETE")
print("=" * 100)
print()

# Close connection
engine.dispose()

