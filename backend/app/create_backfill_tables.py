"""
Create new tables for backfill testing
"""
from sqlalchemy import create_engine, text
from config import settings

def create_backfill_tables():
    """Create new tables for backfill testing"""
    
    print("🏗️  CREATING NEW BACKFILL TABLES")
    print("=" * 60)
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Create new schema for backfill testing
            print("📋 Creating backfill_test schema...")
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS backfill_test"))
            conn.commit()
            
            # Create dynamic_data table
            print("📋 Creating backfill_test.dynamic_data table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS backfill_test.dynamic_data (
                    id SERIAL PRIMARY KEY,
                    asin VARCHAR(20) NOT NULL,
                    marketplace VARCHAR(10) NOT NULL,
                    fetch_date DATE NOT NULL,
                    current_buybox_price DECIMAL(10,2),
                    sales_rank_current INTEGER,
                    num_sellers INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asin, marketplace, fetch_date)
                )
            """))
            conn.commit()
            
            # Create keepa_trends table
            print("📋 Creating backfill_test.keepa_trends table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS backfill_test.keepa_trends (
                    id SERIAL PRIMARY KEY,
                    asin VARCHAR(20) NOT NULL,
                    marketplace VARCHAR(10) NOT NULL,
                    week_start_date DATE NOT NULL,
                    avg_buybox_price DECIMAL(10,2),
                    min_buybox_price DECIMAL(10,2),
                    max_buybox_price DECIMAL(10,2),
                    price_volatility DECIMAL(10,2),
                    avg_sales_rank DECIMAL(15,2),
                    min_sales_rank INTEGER,
                    max_sales_rank INTEGER,
                    rank_volatility DECIMAL(15,2),
                    price_trend_7d DECIMAL(5,2),
                    price_trend_30d DECIMAL(5,2),
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asin, marketplace, week_start_date)
                )
            """))
            conn.commit()
            
            # Create keepa_raw_log table
            print("📋 Creating backfill_test.keepa_raw_log table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS backfill_test.keepa_raw_log (
                    id SERIAL PRIMARY KEY,
                    asin VARCHAR(20) NOT NULL,
                    marketplace VARCHAR(10) NOT NULL,
                    mode VARCHAR(20) NOT NULL,
                    raw_response JSONB,
                    status VARCHAR(20) DEFAULT 'success',
                    error_message TEXT,
                    tokens_consumed INTEGER DEFAULT 0,
                    duration_ms INTEGER DEFAULT 0,
                    fetch_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            
            # Create indexes for better performance
            print("📋 Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_backfill_dynamic_data_asin 
                ON backfill_test.dynamic_data(asin, marketplace, fetch_date)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_backfill_trends_asin 
                ON backfill_test.keepa_trends(asin, marketplace, week_start_date)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_backfill_raw_log_asin 
                ON backfill_test.keepa_raw_log(asin, marketplace, fetch_timestamp)
            """))
            
            conn.commit()
            
            print("✅ All tables created successfully!")
            print("\n📊 Table Summary:")
            print("   - backfill_test.dynamic_data (for daily price data)")
            print("   - backfill_test.keepa_trends (for weekly trend analysis)")
            print("   - backfill_test.keepa_raw_log (for API response logging)")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

def main():
    create_backfill_tables()

if __name__ == "__main__":
    main()
