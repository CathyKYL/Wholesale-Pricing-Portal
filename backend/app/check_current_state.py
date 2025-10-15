"""Check current database state"""
from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(settings.DATABASE_URL)
conn = engine.connect()

# Check affected ASINs
asins = ['0114850003','070234236X','1546103597','1637995059','163799673X','163799897X','2067955810','4027876040','9124233684','912424788X','B0F38CZDDF','B0FCFLLM8L']

result = conn.execute(text("""
    SELECT asin, marketplace, COUNT(*) as rows, 
           COUNT(CASE WHEN current_buybox_price IS NULL THEN 1 END) as null_prices,
           MIN(fetch_date) as first_date,
           MAX(fetch_date) as last_date
    FROM dynamic.keepa_daily_data 
    WHERE asin = ANY(:asins)
    GROUP BY asin, marketplace 
    ORDER BY asin
"""), {'asins': asins}).fetchall()

print("Current state after interrupted backfill:")
print(f"{'ASIN':<15} {'Market':<8} {'Rows':<6} {'NULL':<6} {'First Date':<12} {'Last Date':<12}")
print("-" * 80)

for r in result:
    print(f"{r[0]:<15} {r[1]:<8} {r[2]:<6} {r[3]:<6} {str(r[4]):<12} {str(r[5]):<12}")

conn.close()




