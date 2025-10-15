"""Quick schema checker"""
from sqlalchemy import create_engine, text, inspect
from config import settings

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)

print("\n=== keepa_raw_log table schema ===")
cols = inspector.get_columns('keepa_raw_log', schema='dynamic')
for c in cols:
    print(f"  {c['name']:<30} {c['type']}")





