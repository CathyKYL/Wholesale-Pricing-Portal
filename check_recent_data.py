"""Check for recent data in backfill_test.dynamic_data"""
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
print("🔍 CHECKING FOR RECENT DATA IN backfill_test.dynamic_data")
print("=" * 80)
print()

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Check total count
cursor.execute("SELECT COUNT(*) FROM backfill_test.dynamic_data")
total_count = cursor.fetchone()[0]
print(f"📊 Total records in backfill_test.dynamic_data: {total_count}")
print()

# Check most recent updates
cursor.execute("""
    SELECT asin, marketplace, fetch_date, current_buybox_price, last_updated
    FROM backfill_test.dynamic_data
    ORDER BY last_updated DESC
    LIMIT 10
""")

recent_records = cursor.fetchall()

if recent_records:
    print("🕐 Most Recently Updated Records:")
    print()
    for asin, marketplace, fetch_date, price, last_updated in recent_records:
        print(f"   ASIN: {asin} ({marketplace})")
        print(f"   Fetch Date: {fetch_date}")
        print(f"   Price: ${price if price else 'N/A'}")
        print(f"   Last Updated: {last_updated}")
        print()
else:
    print("⚠️  No records found in backfill_test.dynamic_data")
    print()

# Check for today's data
today = datetime.now().date()
cursor.execute("""
    SELECT COUNT(*) 
    FROM backfill_test.dynamic_data
    WHERE fetch_date = %s
""", (today,))

today_count = cursor.fetchone()[0]
print(f"📅 Records with today's fetch_date ({today}): {today_count}")
print()

# Check data updated in last 24 hours
yesterday = datetime.now() - timedelta(hours=24)
cursor.execute("""
    SELECT COUNT(*) 
    FROM backfill_test.dynamic_data
    WHERE last_updated >= %s
""", (yesterday,))

recent_count = cursor.fetchone()[0]
print(f"🆕 Records updated in last 24 hours: {recent_count}")

conn.close()

print()
print("=" * 80)

