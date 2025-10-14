"""
Database Setup for Keepa Data Ingestion System
-----------------------------------------------
Creates schemas and tables for static metadata and dynamic Keepa data.

Schemas:
  - static: For publisher metadata, cost tables, etc.
  - dynamic: For daily Keepa data, trends, and raw logs

Tables:
  - dynamic.keepa_daily_data: Daily snapshot data with backfill support
  - dynamic.keepa_trends: Computed rolling 30d averages and trends
  - dynamic.keepa_raw_log: Raw JSON responses from Keepa API for debugging
"""

import sys
from sqlalchemy import create_engine, text
from config import settings

print("\n" + "=" * 100)
print("🏗️  DATABASE SETUP: Keepa Data Ingestion System")
print("=" * 100)

# Create database engine
engine = create_engine(settings.DATABASE_URL, echo=False)

try:
    with engine.connect() as conn:
        # Step 1: Create schemas
        print("\n1️⃣ Creating schemas...")
        
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS static"))
        print("   ✅ Created/verified 'static' schema")
        
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dynamic"))
        print("   ✅ Created/verified 'dynamic' schema")
        
        conn.commit()
        
        # Step 2: Create dynamic.keepa_daily_data table
        print("\n2️⃣ Creating dynamic.keepa_daily_data table...")
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dynamic.keepa_daily_data (
                id SERIAL PRIMARY KEY,
                asin TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                fetch_date DATE NOT NULL,
                
                -- BuyBox price (most important competitive price)
                current_buybox_price NUMERIC(12, 2),
                
                -- Sales rank (from Keepa salesRanks)
                sales_rank_current INTEGER,
                
                -- Seller count (only available in daily mode from stats['current'][11])
                num_sellers INTEGER,
                
                -- Metadata
                last_updated TIMESTAMP DEFAULT NOW(),
                
                -- Ensure one record per ASIN/marketplace/date
                CONSTRAINT unique_asin_marketplace_date 
                    UNIQUE (asin, marketplace, fetch_date)
            )
        """))
        print("   ✅ Created/verified 'dynamic.keepa_daily_data' table")
        
        # Create indexes for performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_keepa_daily_asin 
                ON dynamic.keepa_daily_data(asin)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_keepa_daily_marketplace 
                ON dynamic.keepa_daily_data(marketplace)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_keepa_daily_date 
                ON dynamic.keepa_daily_data(fetch_date)
        """))
        print("   ✅ Created indexes on asin, marketplace, fetch_date")
        
        conn.commit()
        
        # Step 3: Create dynamic.keepa_trends table
        print("\n3️⃣ Creating dynamic.keepa_trends table...")
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dynamic.keepa_trends (
                id SERIAL PRIMARY KEY,
                asin TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                week_start_date DATE NOT NULL,
                
                -- Weekly aggregates (last 360 days, by week)
                avg_buybox_price NUMERIC(12, 2),
                min_buybox_price NUMERIC(12, 2),
                max_buybox_price NUMERIC(12, 2),
                avg_sales_rank INTEGER,
                min_sales_rank INTEGER,
                max_sales_rank INTEGER,
                
                -- Trend indicators
                price_trend_7d NUMERIC(8, 2),  -- % change over last 7 days
                price_trend_30d NUMERIC(8, 2),  -- % change over last 30 days
                sales_rank_trend_7d NUMERIC(8, 2),
                sales_rank_trend_30d NUMERIC(8, 2),
                
                -- Volatility metrics
                price_volatility NUMERIC(8, 2),  -- Standard deviation
                rank_volatility NUMERIC(12, 2),  -- Standard deviation (can be large for ranks)
                
                -- Metadata
                computed_at TIMESTAMP DEFAULT NOW(),
                
                -- Ensure one record per ASIN/marketplace/week
                CONSTRAINT unique_asin_marketplace_week 
                    UNIQUE (asin, marketplace, week_start_date)
            )
        """))
        print("   ✅ Created/verified 'dynamic.keepa_trends' table")
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_keepa_trends_asin 
                ON dynamic.keepa_trends(asin)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_keepa_trends_week 
                ON dynamic.keepa_trends(week_start_date)
        """))
        print("   ✅ Created indexes on asin, week_start_date")
        
        conn.commit()
        
        # Step 4: Create dynamic.keepa_raw_log table
        print("\n4️⃣ Creating dynamic.keepa_raw_log table...")
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dynamic.keepa_raw_log (
                id SERIAL PRIMARY KEY,
                asin TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                fetch_timestamp TIMESTAMP DEFAULT NOW(),
                fetch_mode TEXT,  -- 'backfill' or 'daily'
                
                -- Raw response data
                raw_response JSONB NOT NULL,
                
                -- Status tracking
                status TEXT,  -- 'success', 'partial', 'error'
                error_message TEXT,
                tokens_used INTEGER,
                
                -- Metadata
                api_call_duration_ms INTEGER,
                
                -- Index for debugging by date
                fetch_date DATE GENERATED ALWAYS AS (fetch_timestamp::DATE) STORED
            )
        """))
        print("   ✅ Created/verified 'dynamic.keepa_raw_log' table")
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_keepa_raw_asin 
                ON dynamic.keepa_raw_log(asin)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_keepa_raw_timestamp 
                ON dynamic.keepa_raw_log(fetch_timestamp)
        """))
        print("   ✅ Created indexes on asin, fetch_timestamp")
        
        conn.commit()
        
        # Step 5: Verify table creation
        print("\n5️⃣ Verifying tables...")
        
        result = conn.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema IN ('static', 'dynamic')
            ORDER BY table_schema, table_name
        """))
        
        tables = result.fetchall()
        for schema, table in tables:
            print(f"   ✅ {schema}.{table}")
        
        # Count rows in each table
        print("\n6️⃣ Checking row counts...")
        
        result = conn.execute(text("SELECT COUNT(*) FROM dynamic.keepa_daily_data"))
        daily_count = result.fetchone()[0]
        print(f"   📊 dynamic.keepa_daily_data: {daily_count} rows")
        
        result = conn.execute(text("SELECT COUNT(*) FROM dynamic.keepa_trends"))
        trends_count = result.fetchone()[0]
        print(f"   📊 dynamic.keepa_trends: {trends_count} rows")
        
        result = conn.execute(text("SELECT COUNT(*) FROM dynamic.keepa_raw_log"))
        log_count = result.fetchone()[0]
        print(f"   📊 dynamic.keepa_raw_log: {log_count} rows")
        
        print("\n" + "=" * 100)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 100)
        print("\nSchemas and tables created successfully.")
        print("\nNext step: Run keepa_ingestor.py to populate data")
        print("=" * 100 + "\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)

