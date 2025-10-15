"""Check for data from GitHub Actions run at 06:19:52 UTC on Oct 15"""
import os
import psycopg2
from datetime import datetime, timedelta

# Load .env
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

database_url = os.getenv("DATABASE_URL")

print("=" * 80)
print("🔍 CHECKING FOR GITHUB ACTIONS DATA (Oct 15 @ 06:19 UTC)")
print("=" * 80)
print()

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# GitHub Actions ran at 06:19:52 UTC
# Let's check for data updated between 06:00 and 06:30 UTC
github_actions_start = datetime(2025, 10, 15, 6, 0, 0)
github_actions_end = datetime(2025, 10, 15, 6, 30, 0)

cursor.execute("""
    SELECT COUNT(*), MIN(last_updated), MAX(last_updated)
    FROM backfill_test.dynamic_data
    WHERE last_updated >= %s AND last_updated <= %s
""", (github_actions_start, github_actions_end))

count, min_time, max_time = cursor.fetchone()

print(f"📊 Records updated between {github_actions_start} and {github_actions_end} UTC:")
print(f"   Count: {count}")
if count > 0:
    print(f"   Time range: {min_time} to {max_time}")
    print()
    
    # Show sample records
    cursor.execute("""
        SELECT asin, marketplace, fetch_date, current_buybox_price, last_updated
        FROM backfill_test.dynamic_data
        WHERE last_updated >= %s AND last_updated <= %s
        ORDER BY last_updated DESC
        LIMIT 10
    """, (github_actions_start, github_actions_end))
    
    records = cursor.fetchall()
    print("   Sample records:")
    for asin, marketplace, fetch_date, price, last_updated in records:
        print(f"      {asin} ({marketplace}): ${price} - Updated: {last_updated}")
else:
    print(f"   ⚠️  NO RECORDS FOUND!")
    print()
    print("   This means GitHub Actions reported success but didn't save data.")

print()
print("-" * 80)
print()

# Now check ALL Oct 15 data to see what we have
cursor.execute("""
    SELECT 
        DATE(last_updated AT TIME ZONE 'UTC') as update_date,
        EXTRACT(HOUR FROM last_updated AT TIME ZONE 'UTC') as update_hour,
        COUNT(*) as record_count
    FROM backfill_test.dynamic_data
    WHERE DATE(last_updated AT TIME ZONE 'UTC') = '2025-10-15'
    GROUP BY update_date, update_hour
    ORDER BY update_hour
""")

hourly_data = cursor.fetchall()

print("📅 All Oct 15 data grouped by hour (UTC):")
print()
if hourly_data:
    for update_date, update_hour, record_count in hourly_data:
        print(f"   Hour {int(update_hour):02d}:00 UTC - {record_count} records")
else:
    print("   ⚠️  No data found for Oct 15")

conn.close()

print()
print("=" * 80)

