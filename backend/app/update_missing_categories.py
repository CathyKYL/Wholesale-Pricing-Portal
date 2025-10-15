"""
Update Missing Categories by Author
------------------------------------
Purpose:
- Find products with NULL category_lvl3
- Look up other books by the same author
- Fill in the missing category_lvl3 based on author's other books

This ensures consistent categorization across all books by the same author.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_KEY in .env file")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("🔄 UPDATING MISSING CATEGORY_LVL3 VALUES BY AUTHOR")
print("=" * 80)
print()

# Step 1: Get all products with NULL category_lvl3
print("📊 Step 1: Finding products with NULL category_lvl3...")

response = supabase.table('catalog_rows').select('id, asin, title, author, category_lvl3').execute()
all_products = response.data

# Separate products with and without category_lvl3
products_with_category = {}  # author -> category_lvl3
products_without_category = []

for product in all_products:
    author = product.get('author')
    category = product.get('category_lvl3')
    
    # Skip if no author
    if not author or author == 'Unknown Author' or author == '':
        continue
    
    if category and category != 'null' and category != '':
        # Store author's category
        if author not in products_with_category:
            products_with_category[author] = category
    else:
        # This product needs a category
        products_without_category.append(product)

print(f"   ✅ Found {len(products_without_category)} products with missing category_lvl3")
print(f"   ✅ Found {len(products_with_category)} authors with known categories")
print()

# Step 2: Update products based on author's other books
print("📝 Step 2: Updating missing categories...")
updated_count = 0
skipped_count = 0

for product in products_without_category:
    author = product.get('author')
    product_id = product.get('id')
    asin = product.get('asin')
    title = product.get('title')
    
    # Check if we have a category for this author
    if author in products_with_category:
        category_to_use = products_with_category[author]
        
        # Update the product
        try:
            supabase.table('catalog_rows').update({
                'category_lvl3': category_to_use
            }).eq('id', product_id).execute()
            
            print(f"   ✅ Updated: {title[:50]}... by {author}")
            print(f"      ASIN: {asin} → Category: {category_to_use}")
            updated_count += 1
            
        except Exception as e:
            print(f"   ❌ Error updating {asin}: {e}")
    else:
        print(f"   ⚠️  Skipped: {title[:50]}... by {author}")
        print(f"      Reason: No other books by this author with category")
        skipped_count += 1

print()
print("=" * 80)
print("✅ UPDATE COMPLETE!")
print("=" * 80)
print(f"📊 Summary:")
print(f"   - Updated: {updated_count} products")
print(f"   - Skipped: {skipped_count} products (no author reference found)")
print()
print("🔄 Please refresh your frontend to see the updated categories!")
print("=" * 80)






