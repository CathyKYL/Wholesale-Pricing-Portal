"""
Setup Verification for Keepa Data Ingestion System
---------------------------------------------------
Verifies all requirements are met before running the ingestion system.
"""

import sys
import os

print("\n" + "=" * 100)
print("🔍 SETUP VERIFICATION: Keepa Data Ingestion System")
print("=" * 100)

# 1. Check Python version
print("\n1️⃣ Checking Python version...")
py_version = sys.version_info
if py_version.major >= 3 and py_version.minor >= 10:
    print(f"   ✅ Python {py_version.major}.{py_version.minor}.{py_version.micro} (>= 3.10 required)")
else:
    print(f"   ❌ Python {py_version.major}.{py_version.minor}.{py_version.micro} - Need Python >= 3.10")
    sys.exit(1)

# 2. Check required packages
print("\n2️⃣ Checking required packages...")
required_packages = [
    'keepa', 'psycopg2', 'python-dotenv', 'pandas', 
    'schedule', 'sqlalchemy'
]

missing_packages = []
for package in required_packages:
    try:
        if package == 'python-dotenv':
            __import__('dotenv')
        else:
            __import__(package)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} - NOT INSTALLED")
        missing_packages.append(package)

if missing_packages:
    print(f"\n   ⚠️  Missing packages: {', '.join(missing_packages)}")
    print(f"   Run: pip install {' '.join(missing_packages)}")
    sys.exit(1)

# 3. Check environment variables
print("\n3️⃣ Checking environment variables...")
from dotenv import load_dotenv
load_dotenv()

keepa_key = os.getenv('KEEPA_API_KEY')
database_url = os.getenv('DATABASE_URL')

if keepa_key:
    print(f"   ✅ KEEPA_API_KEY found ({keepa_key[:20]}...)")
else:
    print(f"   ❌ KEEPA_API_KEY not found in .env")
    sys.exit(1)

if database_url:
    # Mask password in URL
    masked_url = database_url.split('@')[1] if '@' in database_url else database_url[:50]
    print(f"   ✅ DATABASE_URL found (...@{masked_url})")
else:
    print(f"   ❌ DATABASE_URL not found in .env")
    sys.exit(1)

# 4. Test database connection
print("\n4️⃣ Testing database connection...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(database_url, echo=False)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✅ PostgreSQL connected")
        print(f"   📌 Version: {version.split(',')[0]}")
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")
    sys.exit(1)

# 5. Check if schemas exist (or will be created)
print("\n5️⃣ Checking database schemas...")
try:
    with engine.connect() as conn:
        # Check for static schema
        result = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('static', 'dynamic')
        """))
        existing_schemas = [row[0] for row in result]
        
        if 'static' in existing_schemas:
            print(f"   ✅ 'static' schema exists")
        else:
            print(f"   ⚠️  'static' schema will be created")
        
        if 'dynamic' in existing_schemas:
            print(f"   ✅ 'dynamic' schema exists")
        else:
            print(f"   ⚠️  'dynamic' schema will be created")
except Exception as e:
    print(f"   ⚠️  Could not check schemas: {e}")

# 6. Summary
print("\n" + "=" * 100)
print("✅ SETUP VERIFICATION COMPLETE!")
print("=" * 100)
print("\nAll requirements met. Ready to run Keepa data ingestion system.")
print("\nNext steps:")
print("  1. Run: python setup_database.py  (to create schemas and tables)")
print("  2. Run: python keepa_ingestor.py --test  (to test with sample data)")
print("  3. Run: python keepa_ingestor.py --backfill  (to load 360 days of data)")
print("  4. Run: python keepa_ingestor.py --daily  (for daily updates, or schedule it)")
print("=" * 100 + "\n")





