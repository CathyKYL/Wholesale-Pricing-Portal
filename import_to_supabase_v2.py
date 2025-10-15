"""
Import Database to Supabase (Version 2 - Fixed)
------------------------------------------------
Improved import with better error handling and schema creation.

USAGE:
    python import_to_supabase_v2.py "YOUR_SUPABASE_CONNECTION_STRING"
"""

import sys
import os
from sqlalchemy import create_engine, text

if len(sys.argv) < 2:
    print("\n❌ ERROR: Please provide Supabase connection string")
    print("\nUSAGE:")
    print('  python import_to_supabase_v2.py "YOUR_SUPABASE_URL"')
    sys.exit(1)

SUPABASE_URL = sys.argv[1]
SQL_FILE = "wholesale_portal_backup.sql"

if not os.path.exists(SQL_FILE):
    print(f"\n❌ ERROR: SQL file not found: {SQL_FILE}")
    sys.exit(1)

print("\n" + "=" * 100)
print("📥 IMPORTING DATABASE TO SUPABASE (IMPROVED)")
print("=" * 100)

print(f"\n📄 SQL File: {SQL_FILE}")
print(f"📊 File size: {os.path.getsize(SQL_FILE) / 1024:.1f} KB")
print(f"🌐 Target: {SUPABASE_URL.split('@')[1].split('/')[0] if '@' in SUPABASE_URL else 'Supabase'}")

print("\n⏳ Connecting to Supabase...")

try:
    # Use autocommit mode to handle transactions better
    engine = create_engine(SUPABASE_URL, isolation_level="AUTOCOMMIT")
    conn = engine.connect()
    print("✅ Connected successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# STEP 1: Create schemas first
print(f"\n1️⃣ Creating schemas...")
schemas = ['dynamic', 'static']
for schema in schemas:
    try:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
        print(f"   ✅ Schema '{schema}' created")
    except Exception as e:
        print(f"   ⚠️  Schema '{schema}': {str(e)[:80]}")

# STEP 2: Read and parse SQL file
print(f"\n2️⃣ Reading SQL file...")

with open(SQL_FILE, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Split into statements more carefully
statements = []
current_statement = []

for line in sql_content.split('\n'):
    # Skip comments
    if line.strip().startswith('--') and not current_statement:
        continue
    
    current_statement.append(line)
    
    # Check if statement ends with semicolon
    if line.strip().endswith(';'):
        stmt = '\n'.join(current_statement).strip()
        if stmt and not stmt.startswith('--'):
            statements.append(stmt)
        current_statement = []

print(f"✅ Found {len(statements)} SQL statements")

# STEP 3: Execute statements
print(f"\n3️⃣ Executing statements...")
print("   This may take a few minutes...")

success_count = 0
error_count = 0
skipped_count = 0
errors = []

for i, statement in enumerate(statements, 1):
    try:
        conn.execute(text(statement))
        success_count += 1
        
        # Progress indicator
        if i % 25 == 0:
            print(f"   Progress: {i}/{len(statements)} statements ({success_count} succeeded, {error_count} errors, {skipped_count} skipped)")
    
    except Exception as e:
        error_msg = str(e)
        
        # Ignore certain expected errors
        if 'already exists' in error_msg.lower():
            skipped_count += 1
        elif 'duplicate key' in error_msg.lower():
            skipped_count += 1
        elif 'constraint' in error_msg.lower() and 'already exists' in error_msg.lower():
            skipped_count += 1
        else:
            error_count += 1
            if len(errors) < 10:  # Store first 10 errors
                errors.append({
                    'statement_num': i,
                    'error': error_msg[:200],
                    'sql': statement[:100]
                })

print("\n" + "=" * 100)
print("✅ IMPORT COMPLETE!")
print("=" * 100)

print(f"\n📊 Summary:")
print(f"   • Total statements: {len(statements)}")
print(f"   • Succeeded: {success_count}")
print(f"   • Skipped (already exists): {skipped_count}")
print(f"   • Errors: {error_count}")

if errors:
    print(f"\n⚠️  First {len(errors)} errors:")
    for err in errors:
        print(f"\n   Statement #{err['statement_num']}:")
        print(f"   SQL: {err['sql']}...")
        print(f"   Error: {err['error']}")

# STEP 4: Verify data
print(f"\n4️⃣ Verifying import...")

try:
    # Check tables
    result = conn.execute(text("""
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
        total_rows = 0
        for row in result:
            print(f"   • {row[0]}.{row[1]}: {row[2]:,} rows")
            total_rows += row[2]
        
        print(f"\n✅ Total rows imported: {total_rows:,}")
    else:
        print("   ⚠️  No tables found. Import may have failed.")
    
except Exception as e:
    print(f"⚠️  Could not verify: {str(e)[:100]}")

conn.close()

print(f"\n🚀 Next Steps:")
print(f"   1. Update your .env file with Supabase URL")
print(f"   2. Test connection locally")
print(f"   3. Add URL to GitHub Secrets")
print(f"   4. Test GitHub Actions workflow")

print("\n" + "=" * 100 + "\n")





