"""
Add Keepa Columns to Database
------------------------------
This script adds the new Keepa-related columns to the existing catalog_rows table.
Safe to run multiple times - uses IF NOT EXISTS.

New columns added:
- isbn13: ISBN-13 number from Keepa
- image_urls: Product images from Amazon
- package_dimensions: Package size (L x W x H)
- package_weight: Package weight in pounds
- keepa_last_update: Timestamp of last Keepa sync
"""

from db import engine
from sqlalchemy import text

print("\n🔄 Adding Keepa columns to database...")
print("=" * 70)

try:
    with engine.connect() as conn:
        # Add all new columns with IF NOT EXISTS
        # This makes the script idempotent (safe to run multiple times)
        conn.execute(text("""
            ALTER TABLE catalog_rows
            ADD COLUMN IF NOT EXISTS isbn13 VARCHAR(13),
            ADD COLUMN IF NOT EXISTS image_url VARCHAR(200),
            ADD COLUMN IF NOT EXISTS category_lvl1 VARCHAR(200),
            ADD COLUMN IF NOT EXISTS category_lvl2 VARCHAR(200),
            ADD COLUMN IF NOT EXISTS category_lvl3 VARCHAR(200),
            ADD COLUMN IF NOT EXISTS package_dimensions VARCHAR(100),
            ADD COLUMN IF NOT EXISTS package_weight NUMERIC(10, 2);
        """))
        
        conn.commit()
    
    print("✅ Successfully added Keepa columns to catalog_rows table")
    print("\nNew columns:")
    print("  - isbn13: ISBN-13 number")
    print("  - image_url: First product image from Amazon")
    print("  - category_lvl1: Top-level category (e.g., 'Books')")
    print("  - category_lvl2: Second-level category")
    print("  - category_lvl3: Third-level category")
    print("  - package_dimensions: Package size (L x W x H inches)")
    print("  - package_weight: Package weight (pounds)")
    print("\n✅ Database schema updated!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ ERROR: Failed to add columns: {e}")
    exit(1)

