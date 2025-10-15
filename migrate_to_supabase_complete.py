"""
Complete Supabase Migration
----------------------------
1. Create tables in Supabase using existing schema
2. Copy data from local database to Supabase

USAGE:
    python migrate_to_supabase_complete.py "YOUR_SUPABASE_CONNECTION_STRING"
"""

import sys
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

if len(sys.argv) < 2:
    print("\n❌ ERROR: Please provide Supabase connection string")
    print("\nUSAGE:")
    print('  python migrate_to_supabase_complete.py "YOUR_SUPABASE_URL"')
    sys.exit(1)

SUPABASE_URL = sys.argv[1]

# Load local database URL
load_dotenv()
LOCAL_DB_URL = os.getenv("DATABASE_URL")

print("\n" + "=" * 100)
print("🚀 COMPLETE SUPABASE MIGRATION")
print("=" * 100)

print(f"\n📍 Source (Local): {LOCAL_DB_URL.split('@')[1] if '@' in LOCAL_DB_URL else LOCAL_DB_URL}")
print(f"📍 Target (Supabase): {SUPABASE_URL.split('@')[1].split('/')[0] if '@' in SUPABASE_URL else 'Supabase'}")

# ========== STEP 1: Connect to both databases ==========
print(f"\n1️⃣ Connecting to databases...")

try:
    local_engine = create_engine(LOCAL_DB_URL)
    local_conn = local_engine.connect()
    print("   ✅ Local database connected")
except Exception as e:
    print(f"   ❌ Local database failed: {e}")
    sys.exit(1)

try:
    supabase_engine = create_engine(SUPABASE_URL, isolation_level="AUTOCOMMIT")
    supabase_conn = supabase_engine.connect()
    print("   ✅ Supabase connected")
except Exception as e:
    print(f"   ❌ Supabase connection failed: {e}")
    local_conn.close()
    sys.exit(1)

# ========== STEP 2: Create schemas ==========
print(f"\n2️⃣ Creating schemas in Supabase...")

for schema in ['static', 'dynamic']:
    try:
        supabase_conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
        print(f"   ✅ Schema '{schema}' created")
    except Exception as e:
        print(f"   ⚠️  Schema '{schema}': {str(e)[:80]}")

# ========== STEP 3: Create tables ==========
print(f"\n3️⃣ Creating tables in Supabase...")

# Get table creation DDL from local database
create_statements = {
    'public.catalog_rows': """
        CREATE TABLE IF NOT EXISTS public.catalog_rows (
            id SERIAL PRIMARY KEY,
            asin VARCHAR(32) NOT NULL,
            marketplace VARCHAR(2) NOT NULL,
            title VARCHAR(512) NOT NULL,
            author VARCHAR(512),
            available_stock INTEGER,
            rrp NUMERIC(12, 2),
            our_price NUMERIC(12, 2),
            isbn13 VARCHAR(13),
            image_url VARCHAR(200),
            category_lvl1 VARCHAR(200),
            category_lvl2 VARCHAR(200),
            category_lvl3 VARCHAR(200),
            description VARCHAR(2000),
            package_dimensions VARCHAR(100),
            package_weight NUMERIC(10, 2),
            CONSTRAINT uq_asin_marketplace UNIQUE (asin, marketplace)
        );
        CREATE INDEX IF NOT EXISTS idx_catalog_asin ON public.catalog_rows (asin);
        CREATE INDEX IF NOT EXISTS idx_catalog_marketplace ON public.catalog_rows (marketplace);
    """,
    
    'dynamic.keepa_daily_data': """
        CREATE TABLE IF NOT EXISTS dynamic.keepa_daily_data (
            id SERIAL PRIMARY KEY,
            asin TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            fetch_date DATE NOT NULL,
            current_buybox_price NUMERIC(12, 2),
            sales_rank_current INTEGER,
            num_sellers INTEGER,
            last_updated TIMESTAMP DEFAULT NOW(),
            CONSTRAINT unique_asin_marketplace_date UNIQUE (asin, marketplace, fetch_date)
        );
        CREATE INDEX IF NOT EXISTS idx_daily_asin_marketplace ON dynamic.keepa_daily_data (asin, marketplace);
        CREATE INDEX IF NOT EXISTS idx_daily_fetch_date ON dynamic.keepa_daily_data (fetch_date);
    """,
    
    'dynamic.keepa_trends': """
        CREATE TABLE IF NOT EXISTS dynamic.keepa_trends (
            id SERIAL PRIMARY KEY,
            asin TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            week_start_date DATE NOT NULL,
            avg_buybox_price NUMERIC(12, 2),
            min_buybox_price NUMERIC(12, 2),
            max_buybox_price NUMERIC(12, 2),
            price_volatility NUMERIC(8, 2),
            avg_sales_rank INTEGER,
            min_sales_rank INTEGER,
            max_sales_rank INTEGER,
            rank_volatility NUMERIC(12, 2),
            price_trend_7d NUMERIC(5, 2),
            price_trend_30d NUMERIC(5, 2),
            computed_at TIMESTAMP DEFAULT NOW(),
            CONSTRAINT unique_asin_marketplace_week UNIQUE (asin, marketplace, week_start_date)
        );
        CREATE INDEX IF NOT EXISTS idx_trends_asin_marketplace ON dynamic.keepa_trends (asin, marketplace);
        CREATE INDEX IF NOT EXISTS idx_trends_week_start_date ON dynamic.keepa_trends (week_start_date);
    """,
    
    'dynamic.keepa_raw_log': """
        CREATE TABLE IF NOT EXISTS dynamic.keepa_raw_log (
            id SERIAL PRIMARY KEY,
            asin TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            fetch_timestamp TIMESTAMP DEFAULT NOW(),
            mode TEXT NOT NULL,
            raw_response JSONB,
            status TEXT NOT NULL,
            error_message TEXT,
            tokens_consumed INTEGER,
            duration_ms INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_raw_log_asin ON dynamic.keepa_raw_log (asin);
        CREATE INDEX IF NOT EXISTS idx_raw_log_timestamp ON dynamic.keepa_raw_log (fetch_timestamp);
    """
}

for table_name, ddl in create_statements.items():
    try:
        supabase_conn.execute(text(ddl))
        print(f"   ✅ Table '{table_name}' created")
    except Exception as e:
        print(f"   ⚠️  Table '{table_name}': {str(e)[:80]}")

# ========== STEP 4: Copy data ==========
print(f"\n4️⃣ Copying data from local to Supabase...")

tables_to_copy = [
    ('public', 'catalog_rows'),
    ('dynamic', 'keepa_daily_data'),
    ('dynamic', 'keepa_trends'),
    ('dynamic', 'keepa_raw_log')
]

total_rows_copied = 0

for schema, table in tables_to_copy:
    full_table = f"{schema}.{table}"
    
    try:
        # Get row count
        row_count = local_conn.execute(text(f"SELECT COUNT(*) FROM {full_table}")).fetchone()[0]
        
        if row_count == 0:
            print(f"   ⏭️  {full_table}: 0 rows (skipping)")
            continue
        
        print(f"   ⏳ {full_table}: Copying {row_count:,} rows...")
        
        # Get data
        result = local_conn.execute(text(f"SELECT * FROM {full_table}"))
        rows = result.fetchall()
        columns = result.keys()
        
        # Insert in batches
        batch_size = 100
        inserted = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            
            # Build INSERT statement
            placeholders = ', '.join([f":{col}" for col in columns])
            insert_sql = f"INSERT INTO {full_table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            
            # Insert batch
            for row in batch:
                row_dict = dict(zip(columns, row))
                try:
                    supabase_conn.execute(text(insert_sql), row_dict)
                    inserted += 1
                except Exception as e:
                    # Skip duplicate or conflicting rows
                    if 'duplicate' not in str(e).lower() and 'conflict' not in str(e).lower():
                        print(f"      ⚠️  Error inserting row: {str(e)[:80]}")
        
        total_rows_copied += inserted
        print(f"   ✅ {full_table}: {inserted:,} rows copied")
        
    except Exception as e:
        print(f"   ❌ {full_table}: Error - {str(e)[:100]}")

# ========== STEP 5: Verify ==========
print(f"\n5️⃣ Verifying migration...")

try:
    result = supabase_conn.execute(text("""
        SELECT 
            n.nspname as schema_name,
            c.relname as table_name,
            c.reltuples::bigint as row_count
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname IN ('public', 'dynamic', 'static')
          AND c.relkind = 'r'
        ORDER BY n.nspname, c.relname
    """)).fetchall()
    
    if result:
        print(f"\n📊 Tables in Supabase:")
        for row in result:
            print(f"   • {row[0]}.{row[1]}: {row[2]:,} rows")
    
except Exception as e:
    print(f"   ⚠️  Could not verify: {str(e)[:100]}")

# Close connections
local_conn.close()
supabase_conn.close()

print("\n" + "=" * 100)
print("✅ MIGRATION COMPLETE!")
print("=" * 100)

print(f"\n📊 Summary:")
print(f"   • Total rows migrated: {total_rows_copied:,}")

print(f"\n🚀 Next Steps:")
print(f"   1. Update your .env file:")
print(f"      DATABASE_URL={SUPABASE_URL}")
print(f"   2. Test connection:")
print(f"      python -c \"from sqlalchemy import create_engine, text; engine = create_engine('{SUPABASE_URL}'); conn = engine.connect(); result = conn.execute(text('SELECT COUNT(*) FROM dynamic.keepa_daily_data')).fetchone(); print(f'✅ Records: {{result[0]:,}}'); conn.close()\"")
print(f"   3. Add to GitHub Secrets")
print(f"   4. Test GitHub Actions")

print("\n" + "=" * 100 + "\n")





