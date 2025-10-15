"""
Import Database to Supabase
----------------------------
Import your exported SQL file to Supabase cloud database.

USAGE:
    python import_to_supabase.py "YOUR_SUPABASE_CONNECTION_STRING"

Example:
    python import_to_supabase.py "postgresql://postgres.abc:pass@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
"""

import sys
import os
from sqlalchemy import create_engine, text

if len(sys.argv) < 2:
    print("\n❌ ERROR: Please provide Supabase connection string")
    print("\nUSAGE:")
    print('  python import_to_supabase.py "YOUR_SUPABASE_URL"')
    print("\nExample:")
    print('  python import_to_supabase.py "postgresql://postgres.abc:pass@aws-0-us-west-1.pooler.supabase.com:6543/postgres"')
    sys.exit(1)

SUPABASE_URL = sys.argv[1]
SQL_FILE = "wholesale_portal_backup.sql"

if not os.path.exists(SQL_FILE):
    print(f"\n❌ ERROR: SQL file not found: {SQL_FILE}")
    print("   Run export_database.py first!")
    sys.exit(1)

print("\n" + "=" * 100)
print("📥 IMPORTING DATABASE TO SUPABASE")
print("=" * 100)

print(f"\n📄 SQL File: {SQL_FILE}")
print(f"📊 File size: {os.path.getsize(SQL_FILE) / 1024:.1f} KB")
print(f"🌐 Target: {SUPABASE_URL.split('@')[1].split('/')[0] if '@' in SUPABASE_URL else 'Supabase'}")

print("\n⏳ Connecting to Supabase...")

try:
    engine = create_engine(SUPABASE_URL)
    conn = engine.connect()
    print("✅ Connected successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n💡 Common issues:")
    print("   • Wrong password")
    print("   • Wrong URL format")
    print("   • Firewall blocking connection")
    sys.exit(1)

print(f"\n📖 Reading SQL file...")

# Read SQL file
with open(SQL_FILE, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Split into statements
statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

print(f"✅ Found {len(statements)} SQL statements")

print(f"\n⏳ Executing statements...")
print("   This may take a few minutes...")

success_count = 0
error_count = 0
skipped_count = 0

for i, statement in enumerate(statements, 1):
    try:
        # Skip comments and empty statements
        if not statement or statement.startswith('--'):
            skipped_count += 1
            continue
        
        # Execute statement
        conn.execute(text(statement))
        conn.commit()
        success_count += 1
        
        # Progress indicator
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(statements)} statements ({success_count} succeeded, {error_count} errors)")
    
    except Exception as e:
        error_msg = str(e)
        
        # Ignore certain expected errors
        if 'already exists' in error_msg.lower():
            skipped_count += 1
        elif 'duplicate key' in error_msg.lower():
            skipped_count += 1
        else:
            error_count += 1
            if error_count <= 5:  # Only show first 5 errors
                print(f"   ⚠️  Error in statement {i}: {error_msg[:100]}")

conn.close()

print("\n" + "=" * 100)
print("✅ IMPORT COMPLETE!")
print("=" * 100)

print(f"\n📊 Summary:")
print(f"   • Total statements: {len(statements)}")
print(f"   • Succeeded: {success_count}")
print(f"   • Skipped: {skipped_count}")
print(f"   • Errors: {error_count}")

if error_count > 5:
    print(f"\n⚠️  Note: Showing first 5 errors only. Total errors: {error_count}")

print(f"\n✅ Verifying import...")

# Verify data
try:
    engine = create_engine(SUPABASE_URL)
    conn = engine.connect()
    
    # Check tables
    result = conn.execute(text("""
        SELECT schemaname, tablename, n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname IN ('public', 'dynamic', 'static')
        ORDER BY schemaname, tablename
    """)).fetchall()
    
    print(f"\n📊 Tables in Supabase:")
    total_rows = 0
    for row in result:
        print(f"   • {row[0]}.{row[1]}: {row[2]:,} rows")
        total_rows += row[2]
    
    print(f"\n✅ Total rows imported: {total_rows:,}")
    
    conn.close()
    
except Exception as e:
    print(f"⚠️  Could not verify: {e}")

print(f"\n🚀 Next Steps:")
print(f"   1. Update your .env file with Supabase URL")
print(f"   2. Test connection locally")
print(f"   3. Add URL to GitHub Secrets")
print(f"   4. Test GitHub Actions workflow")

print("\n" + "=" * 100 + "\n")





