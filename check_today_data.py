"""
Check if today's Keepa data has been fetched
"""
import os
from datetime import datetime, date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print("\n" + "=" * 100)
print("📅 CHECKING TODAY'S KEEPA DATA FETCH")
print("=" * 100)

# Get today's date
today = date.today()
print(f"\n🗓️  Today's Date: {today.strftime('%Y-%m-%d (%A)')}")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if we have any data for today
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as record_count,
                MIN(last_updated) as first_update,
                MAX(last_updated) as last_update
            FROM backfill_test.dynamic_data
            WHERE fetch_date = :today
        """), {"today": today}).fetchone()
        
        record_count = result[0]
        first_update = result[1]
        last_update = result[2]
        
        print(f"\n📊 Results for {today}:")
        print("-" * 100)
        
        if record_count > 0:
            print(f"✅ TODAY'S DATA FOUND!")
            print(f"   📈 Total Records: {record_count}")
            print(f"   ⏰ First Update: {first_update}")
            print(f"   ⏰ Last Update:  {last_update}")
            
            # Get sample of today's data
            sample = conn.execute(text("""
                SELECT 
                    asin,
                    marketplace,
                    current_buybox_price,
                    sales_rank_current,
                    num_sellers,
                    last_updated
                FROM backfill_test.dynamic_data
                WHERE fetch_date = :today
                ORDER BY last_updated DESC
                LIMIT 5
            """), {"today": today}).fetchall()
            
            print(f"\n📋 Sample of Today's Data (first 5 records):")
            print("-" * 100)
            for row in sample:
                print(f"   ASIN: {row[0]} | Market: {row[1]} | Price: ${row[2]:.2f} | Rank: {row[3]:,} | Sellers: {row[4]} | Updated: {row[5]}")
                
        else:
            print(f"❌ NO DATA FOUND FOR TODAY ({today})")
            print(f"\n💡 Possible reasons:")
            print(f"   • Daily update hasn't run yet (scheduled for 3 AM UTC)")
            print(f"   • GitHub Action may have failed")
            print(f"   • Manual trigger needed")
            
        # Check most recent data
        print(f"\n📅 Most Recent Data in Database:")
        print("-" * 100)
        
        recent = conn.execute(text("""
            SELECT 
                fetch_date,
                COUNT(*) as record_count,
                MAX(last_updated) as last_update
            FROM backfill_test.dynamic_data
            GROUP BY fetch_date
            ORDER BY fetch_date DESC
            LIMIT 7
        """)).fetchall()
        
        for row in recent:
            fetch_date = row[0]
            count = row[1]
            last_upd = row[2]
            
            # Highlight today
            if fetch_date == today:
                print(f"   🔵 {fetch_date} | Records: {count:4d} | Last Update: {last_upd} ← TODAY")
            else:
                print(f"      {fetch_date} | Records: {count:4d} | Last Update: {last_upd}")
        
        # Check if we're up to date
        print(f"\n🕐 Current Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕐 Current Time (Local): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        current_hour_utc = datetime.utcnow().hour
        
        if record_count > 0:
            print(f"\n✅ STATUS: Database is UP TO DATE with today's data!")
        elif current_hour_utc < 3:
            print(f"\n⏳ STATUS: Daily update hasn't run yet (runs at 3 AM UTC)")
            print(f"   Current UTC time: {datetime.utcnow().strftime('%H:%M')} - Update pending")
        else:
            print(f"\n⚠️  STATUS: Daily update may have failed or not triggered")
            print(f"   Current UTC time: {datetime.utcnow().strftime('%H:%M')} - Update should have run")
            print(f"\n💡 Action: Check GitHub Actions workflow status")
            
except Exception as e:
    print(f"\n❌ Error checking database: {str(e)}")

print("\n" + "=" * 100 + "\n")


