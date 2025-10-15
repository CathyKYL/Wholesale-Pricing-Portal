"""Check catalog_rows structure"""
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
print("📋 CATALOG_ROWS TABLE STRUCTURE")
print("=" * 80)
print()

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Get columns
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
      AND table_name = 'catalog_rows'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()

print("Columns in public.catalog_rows:")
print()
for col, dtype in columns:
    print(f"  • {col:<30} ({dtype})")

# Sample data
cursor.execute("SELECT * FROM public.catalog_rows LIMIT 1")
sample = cursor.fetchone()
col_names = [desc[0] for desc in cursor.description]

print()
print("=" * 80)
print("📊 SAMPLE ROW")
print("=" * 80)
print()
for name, value in zip(col_names, sample) if sample else []:
    if isinstance(value, str) and len(value) > 50:
        value = value[:47] + "..."
    print(f"{name:<30} = {value}")

conn.close()

print()
print("=" * 80)


