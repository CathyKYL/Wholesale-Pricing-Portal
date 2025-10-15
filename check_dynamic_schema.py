"""Check dynamic.keepa_daily_data table"""
import os
import psycopg2

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
print("🔍 CHECKING dynamic.keepa_daily_data TABLE")
print("=" * 80)
print()

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Check if table exists and count
try:
    cursor.execute("SELECT COUNT(*) FROM dynamic.keepa_daily_data")
    count = cursor.fetchone()[0]
    print(f"📊 Total records in dynamic.keepa_daily_data: {count}")
    print()
    
    if count > 0:
        cursor.execute("""
            SELECT asin, marketplace, fetch_date, current_buybox_price, last_updated
            FROM dynamic.keepa_daily_data
            ORDER BY last_updated DESC
            LIMIT 5
        """)
        
        recent = cursor.fetchall()
        print("🕐 Most Recent Records:")
        for asin, marketplace, fetch_date, price, last_updated in recent:
            print(f"   {asin} ({marketplace}): ${price if price else 'N/A'} - Updated: {last_updated}")
    else:
        print("⚠️  Table is EMPTY")
        
except Exception as e:
    print(f"❌ Error: {e}")

conn.close()

print()
print("=" * 80)

