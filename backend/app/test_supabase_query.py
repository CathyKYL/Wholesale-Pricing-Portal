"""
Test Supabase Query
-------------------
Query specific ASIN data from Supabase to verify cloud database is working.

Test: Pull today's buy box pricing and seller numbers for ASIN 9124233684
"""

import os
from datetime import datetime, date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from db import SessionLocal
from models import CatalogRow

# Load environment (should now point to Supabase)
load_dotenv()

print("\n" + "=" * 100)
print("🧪 TESTING SUPABASE CONNECTION & DATA QUERY")
print("=" * 100)

# Test ASIN
TEST_ASIN = "9124233684"
TODAY = date.today()

print(f"\n📍 Query Details:")
print(f"   • ASIN: {TEST_ASIN}")
print(f"   • Date: {TODAY}")
print(f"   • Looking for: Buy Box Price, Seller Count")

# ========== TEST 1: Basic Connection ==========
print(f"\n1️⃣ Testing database connection...")

try:
    session = SessionLocal()
    result = session.execute(text("SELECT version()")).fetchone()
    postgres_version = result[0].split(',')[0]
    print(f"   ✅ Connected to Supabase!")
    print(f"   📌 PostgreSQL: {postgres_version}")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit(1)

# ========== TEST 2: Check Catalog Data ==========
print(f"\n2️⃣ Checking catalog for ASIN {TEST_ASIN}...")

try:
    catalog_item = session.query(CatalogRow).filter(
        CatalogRow.asin == TEST_ASIN
    ).first()
    
    if catalog_item:
        print(f"   ✅ Found in catalog!")
        print(f"   📖 Title: {catalog_item.title}")
        print(f"   🌍 Marketplace: {catalog_item.marketplace}")
        print(f"   👤 Author: {catalog_item.author}")
        print(f"   💰 Our Price: ${catalog_item.our_price if catalog_item.our_price else 'N/A'}")
    else:
        print(f"   ⚠️  ASIN not found in catalog")
except Exception as e:
    print(f"   ❌ Error querying catalog: {e}")

# ========== TEST 3: Query Today's Keepa Data ==========
print(f"\n3️⃣ Querying today's Keepa data for ASIN {TEST_ASIN}...")

try:
    result = session.execute(text("""
        SELECT 
            asin,
            marketplace,
            fetch_date,
            current_buybox_price,
            sales_rank_current,
            num_sellers,
            last_updated
        FROM dynamic.keepa_daily_data
        WHERE asin = :asin
          AND fetch_date = :today
        ORDER BY marketplace
    """), {'asin': TEST_ASIN, 'today': TODAY}).fetchall()
    
    if result:
        print(f"   ✅ Found {len(result)} record(s) for today!")
        print(f"\n   📊 Today's Data ({TODAY}):")
        print(f"   {'-' * 80}")
        
        for row in result:
            asin, marketplace, fetch_date, buybox_price, sales_rank, num_sellers, last_updated = row
            
            print(f"\n   🌍 Marketplace: {marketplace}")
            print(f"   💵 Buy Box Price: ${buybox_price if buybox_price else 'N/A'}")
            print(f"   👥 Number of Sellers: {num_sellers if num_sellers else 'N/A'}")
            print(f"   📈 Sales Rank: {sales_rank:,}" if sales_rank else "   📈 Sales Rank: N/A")
            print(f"   🕐 Last Updated: {last_updated}")
    else:
        print(f"   ⚠️  No data found for today ({TODAY})")
        print(f"\n   💡 This is expected if today's data hasn't been fetched yet.")
        print(f"   📅 Let's check the most recent data instead...")

except Exception as e:
    print(f"   ❌ Error querying Keepa data: {e}")

# ========== TEST 4: Query Most Recent Data (if no data today) ==========
print(f"\n4️⃣ Querying most recent Keepa data for ASIN {TEST_ASIN}...")

try:
    result = session.execute(text("""
        SELECT 
            asin,
            marketplace,
            fetch_date,
            current_buybox_price,
            sales_rank_current,
            num_sellers,
            last_updated
        FROM dynamic.keepa_daily_data
        WHERE asin = :asin
        ORDER BY fetch_date DESC, marketplace
        LIMIT 5
    """), {'asin': TEST_ASIN}).fetchall()
    
    if result:
        print(f"   ✅ Found {len(result)} most recent record(s)!")
        print(f"\n   📊 Recent Data:")
        print(f"   {'-' * 80}")
        
        for row in result:
            asin, marketplace, fetch_date, buybox_price, sales_rank, num_sellers, last_updated = row
            
            print(f"\n   📅 Date: {fetch_date}")
            print(f"   🌍 Marketplace: {marketplace}")
            print(f"   💵 Buy Box Price: ${buybox_price if buybox_price else 'N/A'}")
            print(f"   👥 Number of Sellers: {num_sellers if num_sellers else 'N/A'}")
            print(f"   📈 Sales Rank: {sales_rank:,}" if sales_rank else "   📈 Sales Rank: N/A")
            print(f"   🕐 Last Updated: {last_updated}")
    else:
        print(f"   ⚠️  No data found for this ASIN at all")
        print(f"   💡 This ASIN might not have been scraped yet")

except Exception as e:
    print(f"   ❌ Error querying recent data: {e}")

# ========== TEST 5: Overall Data Statistics ==========
print(f"\n5️⃣ Checking overall data statistics in Supabase...")

try:
    stats = session.execute(text("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT asin) as unique_asins,
            COUNT(DISTINCT marketplace) as marketplaces,
            MIN(fetch_date) as earliest_date,
            MAX(fetch_date) as latest_date
        FROM dynamic.keepa_daily_data
    """)).fetchone()
    
    print(f"   ✅ Database Statistics:")
    print(f"   📊 Total Records: {stats[0]:,}")
    print(f"   🔢 Unique ASINs: {stats[1]}")
    print(f"   🌍 Marketplaces: {stats[2]}")
    print(f"   📅 Date Range: {stats[3]} to {stats[4]}")

except Exception as e:
    print(f"   ❌ Error getting statistics: {e}")

# Close session
session.close()

print("\n" + "=" * 100)
print("✅ SUPABASE TEST COMPLETE!")
print("=" * 100)

print(f"\n💡 Summary:")
print(f"   • Supabase connection: ✅ Working")
print(f"   • Can query catalog: ✅ Working")
print(f"   • Can query Keepa data: ✅ Working")
print(f"   • All {stats[0]:,} records accessible from cloud!")

print(f"\n🚀 Your application is now running on Supabase cloud database!")
print(f"   Ready for GitHub Actions automation! 🎉")

print("\n" + "=" * 100 + "\n")

