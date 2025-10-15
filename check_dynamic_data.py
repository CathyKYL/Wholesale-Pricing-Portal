"""Check dynamic_data structure"""
import os, psycopg2

# Load .env
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# Columns
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'backfill_test' AND table_name = 'dynamic_data'
    ORDER BY ordinal_position
""")

print("backfill_test.dynamic_data columns:")
for col, dtype in cursor.fetchall():
    print(f"  • {col:<30} ({dtype})")

# Sample
cursor.execute('SELECT * FROM "backfill_test".dynamic_data LIMIT 1')
print("\nSample row:")
if cursor.rowcount > 0:
    names = [d[0] for d in cursor.description]
    row = cursor.fetchone()
    for n, v in zip(names, row):
        print(f"  {n:<30} = {v}")

conn.close()


