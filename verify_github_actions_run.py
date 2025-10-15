"""
Verify GitHub Actions Run
--------------------------
Check if the GitHub Actions workflow successfully updated Supabase.
Run this AFTER the GitHub Actions workflow completes.
"""

from sqlalchemy import text
from datetime import date
from db import SessionLocal

print("\n" + "=" * 100)
print("🔍 VERIFYING GITHUB ACTIONS WORKFLOW RESULT")
print("=" * 100)

session = SessionLocal()

# Get today's date
today = date.today()

print(f"\n📅 Today's Date: {today}")

# Check for today's data
print(f"\n1️⃣ Checking if today's data was fetched by GitHub Actions...")

result = session.execute(text("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT asin) as unique_asins,
        MIN(last_updated) as earliest_update,
        MAX(last_updated) as latest_update
    FROM dynamic.keepa_daily_data
    WHERE fetch_date = :today
"""), {'today': today}).fetchone()

if result[0] > 0:
    print(f"   ✅ SUCCESS! Found {result[0]} records for today")
    print(f"   📊 Unique ASINs updated: {result[1]}")
    print(f"   🕐 Update time range: {result[2]} to {result[3]}")
else:
    print(f"   ⚠️  No data found for today yet")
    print(f"   💡 GitHub Actions might still be running, or hasn't run yet")

# Get most recent update
print(f"\n2️⃣ Checking most recent update...")

result = session.execute(text("""
    SELECT 
        fetch_date,
        COUNT(*) as records,
        MAX(last_updated) as last_update_time
    FROM dynamic.keepa_daily_data
    GROUP BY fetch_date
    ORDER BY fetch_date DESC
    LIMIT 1
""")).fetchone()

if result:
    print(f"   📅 Latest data date: {result[0]}")
    print(f"   📊 Records: {result[1]}")
    print(f"   🕐 Last updated: {result[2]}")
    
    if result[0] == today:
        print(f"   ✅ GitHub Actions successfully updated today's data!")
    else:
        print(f"   ⏳ Most recent data is from {result[0]} (waiting for today's run)")

# Overall statistics
print(f"\n3️⃣ Overall database statistics...")

result = session.execute(text("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT asin) as unique_asins,
        MIN(fetch_date) as earliest_date,
        MAX(fetch_date) as latest_date
    FROM dynamic.keepa_daily_data
""")).fetchone()

print(f"   📊 Total records: {result[0]:,}")
print(f"   🔢 Unique ASINs tracked: {result[1]}")
print(f"   📅 Date range: {result[2]} to {result[3]}")

# Sample data
print(f"\n4️⃣ Sample of most recent data...")

result = session.execute(text("""
    SELECT 
        asin,
        marketplace,
        fetch_date,
        current_buybox_price,
        num_sellers,
        sales_rank_current
    FROM dynamic.keepa_daily_data
    WHERE fetch_date = (SELECT MAX(fetch_date) FROM dynamic.keepa_daily_data)
    LIMIT 5
""")).fetchall()

if result:
    print(f"\n   Latest 5 records:")
    for row in result:
        asin, marketplace, fetch_date, price, sellers, rank = row
        print(f"   • {asin} ({marketplace}): ${price if price else 'N/A'} | {sellers if sellers else 'N/A'} sellers | Rank: {rank:,}" if rank else f"   • {asin} ({marketplace}): ${price if price else 'N/A'} | {sellers if sellers else 'N/A'} sellers | Rank: N/A")

session.close()

print("\n" + "=" * 100)
print("✅ VERIFICATION COMPLETE!")
print("=" * 100)
print(f"\n💡 If you don't see today's data yet:")
print(f"   • GitHub Actions might still be running (check Actions tab)")
print(f"   • Scheduled run happens at 3:00 AM UTC daily")
print(f"   • You can manually trigger it from GitHub Actions tab")
print("\n" + "=" * 100 + "\n")





