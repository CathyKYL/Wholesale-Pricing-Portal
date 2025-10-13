# 🔌 Keepa API Integration Guide

## Overview

This guide explains how to use the Keepa API integration to enrich your product catalog with additional metadata from Amazon.

---

## 📊 What Data Does Keepa Provide?

The Keepa integration fetches the following data for each product:

| Field | Description | Example |
|-------|-------------|---------|
| **ISBN-13** | International Standard Book Number | `9781234567890` |
| **Image URLs** | Product images from Amazon | `"71abc123,72def456"` |
| **Package Dimensions** | Size in inches (L x W x H) | `10.20 x 8.50 x 1.20` |
| **Package Weight** | Weight in pounds | `2.35` |
| **Last Update** | Timestamp of last sync | `2025-10-13T15:30:00` |

---

## 🚀 Quick Start

### Step 1: Ensure You Have a Keepa API Key

1. Sign up at [Keepa.com](https://keepa.com/#!api)
2. Purchase API credits (pricing at https://keepa.com/#!api)
3. Get your API key from the Keepa dashboard

### Step 2: Add API Key to `.env`

```env
KEEPA_API_KEY=your_keepa_api_key_here
```

### Step 3: Add Keepa Columns to Database

```bash
cd backend/app
python add_keepa_columns.py
```

This adds the new columns to your `catalog_rows` table.

### Step 4: Sync Keepa Data

```bash
# Sync all catalog items
python sync_keepa.py

# Or sync only US marketplace
python sync_keepa.py --marketplace US

# Or sync only UK marketplace
python sync_keepa.py --marketplace UK

# Or test with first 5 items
python sync_keepa.py --limit 5
```

---

## 📖 Detailed Usage

### Syncing All Items

```bash
python sync_keepa.py
```

This will:
1. Query all items in your `catalog_rows` table
2. Group them by marketplace (US, UK)
3. Fetch data from Keepa API (100 ASINs per request)
4. Update database with ISBN, images, dimensions, weight
5. Set `keepa_last_update` timestamp

### Syncing by Marketplace

**US Marketplace Only:**
```bash
python sync_keepa.py --marketplace US
```

**UK Marketplace Only:**
```bash
python sync_keepa.py --marketplace UK
```

### Testing with Limited Items

```bash
# Test with first 10 items
python sync_keepa.py --limit 10

# Test with first 5 UK items
python sync_keepa.py --marketplace UK --limit 5
```

---

## 💻 Programmatic Usage

### Import the Module

```python
from keepa_integration import update_catalog_with_keepa, fetch_keepa_data
```

### Update All Catalog Items

```python
# Update all items
updated_count = update_catalog_with_keepa()
print(f"Updated {updated_count} items")

# Update only US items
updated_count = update_catalog_with_keepa(marketplace='US')

# Update only UK items with limit
updated_count = update_catalog_with_keepa(marketplace='UK', limit=10)
```

### Fetch Specific ASINs

```python
from keepa_integration import fetch_keepa_data, parse_keepa_product

# Fetch data for specific ASINs
asins = ['B0FCFLLM8L', '912424788X']
products = fetch_keepa_data(asins, 'US')

# Parse the results
for product in products:
    parsed = parse_keepa_product(product, 'US')
    print(f"ASIN: {parsed['asin']}")
    print(f"Title: {parsed['title']}")
    print(f"ISBN-13: {parsed['isbn13']}")
    print(f"Dimensions: {parsed['package_dimensions']}")
    print(f"Weight: {parsed['package_weight']} lbs")
```

---

## 🗄️ Database Schema

### New Columns Added

```sql
ALTER TABLE catalog_rows
ADD COLUMN isbn13 VARCHAR(13),
ADD COLUMN image_urls VARCHAR(1000),
ADD COLUMN package_dimensions VARCHAR(100),
ADD COLUMN package_weight NUMERIC(10, 2),
ADD COLUMN keepa_last_update VARCHAR(50);
```

### Example Data

```sql
SELECT 
    asin,
    marketplace,
    title,
    isbn13,
    package_dimensions,
    package_weight,
    keepa_last_update
FROM catalog_rows
WHERE marketplace = 'US'
LIMIT 5;
```

**Result:**
```
asin         | marketplace | title                  | isbn13         | package_dimensions | package_weight | keepa_last_update
-------------+-------------+------------------------+----------------+--------------------+----------------+------------------
B0FCFLLM8L   | US          | Demon Slayer Vol 1-5   | 9781234567890  | 10.20 x 8.50 x 1.20| 2.35           | 2025-10-13T15:30:00
912434981X   | US          | JuJutsu Kaisen 16-20   | 9789876543210  | 9.50 x 7.80 x 1.50 | 1.85           | 2025-10-13T15:30:05
```

---

## 🔍 Viewing Keepa Data

### In pgAdmin

1. Navigate to `wholesale_portal` → `Schemas` → `public` → `Tables` → `catalog_rows`
2. Right-click → **View/Edit Data** → **All Rows**
3. Scroll right to see the new Keepa columns

### Via API

```bash
# Start the API server
uvicorn main:app --reload --port 8000

# Query catalog items
curl http://localhost:8000/api/catalog
```

Response will include Keepa fields:
```json
{
    "id": 1,
    "asin": "B0FCFLLM8L",
    "marketplace": "US",
    "title": "Demon Slayer Academy Vol 1-5",
    "isbn13": "9781234567890",
    "image_urls": "71abc123,72def456",
    "package_dimensions": "10.20 x 8.50 x 1.20",
    "package_weight": 2.35,
    "keepa_last_update": "2025-10-13T15:30:00"
}
```

---

## ⚙️ API Configuration

### Keepa API Limits

- **Max ASINs per request:** 100
- **Rate limits:** Depends on your Keepa plan
- **Credits:** Each request consumes credits based on your plan

The integration automatically:
- Batches ASINs into groups of 100
- Handles rate limiting gracefully
- Retries failed requests

### Marketplace Codes

| Code | Marketplace | Keepa Domain |
|------|-------------|--------------|
| US | Amazon.com | 1 |
| UK | Amazon.co.uk | 2 |
| DE | Amazon.de | 3 |
| FR | Amazon.fr | 4 |
| JP | Amazon.co.jp | 5 |
| CA | Amazon.ca | 6 |
| IT | Amazon.it | 7 |
| ES | Amazon.es | 8 |

---

## 🐛 Troubleshooting

### Error: "KEEPA_API_KEY not found"

**Solution:** Add your Keepa API key to `.env`:
```env
KEEPA_API_KEY=your_actual_key_here
```

### Error: "Keepa API error (HTTP 403)"

**Solution:** Your API key is invalid or expired. Check your Keepa account.

### Error: "Keepa API error (HTTP 429)"

**Solution:** Rate limit exceeded. Wait a moment and try again.

### Error: "No credits remaining"

**Solution:** Purchase more API credits at [Keepa.com](https://keepa.com/#!api)

### No Data Returned

**Possible causes:**
1. ASINs don't exist in that marketplace
2. Products are restricted/unavailable
3. Keepa doesn't have data for those products

**Solution:** Check the ASIN on Amazon directly to verify it exists.

---

## 📋 Best Practices

### 1. Sync Incrementally

Don't sync all items at once if you have thousands of products:

```bash
# Sync in batches of 100
python sync_keepa.py --limit 100

# Check results, then continue
python sync_keepa.py --limit 100
```

### 2. Monitor API Credits

Check your Keepa credits regularly to avoid running out mid-sync.

### 3. Schedule Regular Updates

Set up a cron job or scheduled task to sync weekly:

```bash
# Linux/Mac cron (weekly on Sunday at 2 AM)
0 2 * * 0 cd /path/to/backend/app && python sync_keepa.py

# Windows Task Scheduler
# Create a scheduled task to run sync_keepa.py weekly
```

### 4. Keep Track of Last Update

The `keepa_last_update` field shows when each item was last synced:

```sql
-- Find items never synced
SELECT asin, marketplace, title
FROM catalog_rows
WHERE keepa_last_update IS NULL;

-- Find items synced over 30 days ago
SELECT asin, marketplace, title, keepa_last_update
FROM catalog_rows
WHERE keepa_last_update < NOW() - INTERVAL '30 days';
```

---

## 🔄 Re-syncing Data

To update existing Keepa data (e.g., dimensions changed):

```bash
# Re-sync all items
python sync_keepa.py

# Re-sync specific marketplace
python sync_keepa.py --marketplace US
```

The sync script will **update** existing data, not duplicate it.

---

## 📊 Example Output

```
🚀 Starting Keepa Sync...
======================================================================

📋 No marketplace filter (syncing all)

======================================================================
🔄 KEEPA CATALOG UPDATE
======================================================================
📊 Found 38 items to update

📡 Processing US marketplace (22 ASINs)...
📡 Fetching 22 ASINs from Keepa (US marketplace)...
  Processing chunk 1/1 (22 ASINs)...
  ✅ Received 22 products from Keepa
✅ Total products fetched from Keepa: 22

💾 Updating database with US data...
  ✅ Updated: B0FCFLLM8L - Demon Slayer Academy Vol 1-5
  ✅ Updated: B09KQJNLP2 - Demon Slayer: Kimetsu no Yaiba Vol 16-23
  ...
✅ Committed US updates to database

📡 Processing UK marketplace (16 ASINs)...
📡 Fetching 16 ASINs from Keepa (UK marketplace)...
  Processing chunk 1/1 (16 ASINs)...
  ✅ Received 16 products from Keepa
✅ Total products fetched from Keepa: 16

💾 Updating database with UK data...
  ✅ Updated: 912424788X - Demon Slayer Academy Vol 1-5
  ...
✅ Committed UK updates to database

======================================================================
🎉 Update complete! 38 items enriched with Keepa data
======================================================================

✅ Success! Updated 38 catalog items with Keepa data
```

---

## 🎯 Next Steps

After syncing Keepa data, you can:

1. **Use dimensions/weight for shipping calculations**
   ```python
   # Calculate shipping cost based on weight
   if item.package_weight:
       shipping_cost = calculate_shipping(item.package_weight)
   ```

2. **Display product images on your website**
   ```python
   # Convert Keepa image IDs to URLs
   if item.image_urls:
       image_ids = item.image_urls.split(',')
       for img_id in image_ids:
           url = f"https://images-na.ssl-images-amazon.com/images/I/{img_id}"
   ```

3. **Use ISBN for inventory management**
   ```python
   # Match with supplier catalogs using ISBN
   if item.isbn13:
       supplier_match = find_supplier_by_isbn(item.isbn13)
   ```

4. **Track data freshness**
   ```sql
   -- Find stale data (>30 days old)
   SELECT * FROM catalog_rows
   WHERE keepa_last_update < NOW() - INTERVAL '30 days';
   ```

---

## 📚 Resources

- **Keepa API Documentation:** https://keepa.com/#!discuss/t/product-object/116
- **Keepa Pricing:** https://keepa.com/#!api
- **Amazon ASIN Lookup:** https://www.amazon.com/dp/{ASIN}

---

**🎉 You're now ready to enrich your catalog with Keepa data!**

For questions or issues, check the troubleshooting section or review the code in `keepa_integration.py`.

