"""
Schema Migration Script
-----------------------
This script drops the old catalog_rows table and recreates it with the new schema.
Then reloads the data from Excel with the marketplace-based structure.
"""

from db import engine, init_db
from sqlalchemy import text
from load_excel import load_excel_to_db

print("\n🔄 Starting Schema Migration...")
print("=" * 70)

# Step 1: Drop old table
print("\n📋 Step 1: Dropping old table...")
try:
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS catalog_rows CASCADE;"))
        conn.commit()
    print("✅ Old table dropped successfully")
except Exception as e:
    print(f"❌ Error dropping table: {e}")
    exit(1)

# Step 2: Create new table with updated schema
print("\n📋 Step 2: Creating new table with marketplace schema...")
try:
    init_db()
    print("✅ New table created with updated schema")
except Exception as e:
    print(f"❌ Error creating table: {e}")
    exit(1)

# Step 3: Reload data
print("\n📋 Step 3: Reloading data from Excel...")
try:
    rows_loaded = load_excel_to_db()
    if rows_loaded > 0:
        print(f"✅ Successfully loaded {rows_loaded} rows")
    else:
        print("⚠️  No rows loaded (check Excel file)")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    exit(1)

print("\n" + "=" * 70)
print("🎉 Schema migration completed successfully!")
print("\n📊 New Schema:")
print("  - Single 'asin' column (instead of uk_asin + us_asin)")
print("  - 'marketplace' column ('US' or 'UK')")
print("  - Each Excel row with both ASINs creates 2 database rows")
print("\n✅ Ready to use!")
print("=" * 70)

