"""List all tables in database"""
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
print("📊 LISTING ALL TABLES IN DATABASE")
print("=" * 80)
print()

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# List all tables
cursor.execute("""
    SELECT schemaname, tablename 
    FROM pg_tables 
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY schemaname, tablename
""")

tables = cursor.fetchall()

print(f"Found {len(tables)} tables:")
print()

current_schema = None
for schema, table in tables:
    if schema != current_schema:
        print(f"\n📁 Schema: {schema}")
        current_schema = schema
    print(f"   • {table}")

conn.close()

print()
print("=" * 80)


