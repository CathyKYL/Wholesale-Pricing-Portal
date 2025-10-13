# 🔄 Database Schema Migration Summary

## ✅ Migration Completed Successfully!

**Date:** October 13, 2025  
**Status:** Complete  
**Impact:** Database structure optimized for marketplace-based operations

---

## 📊 What Changed

### OLD Schema (Denormalized)
```sql
CREATE TABLE catalog_rows (
    id SERIAL PRIMARY KEY,
    uk_asin VARCHAR(32),
    us_asin VARCHAR(32),
    title VARCHAR(512) NOT NULL,
    author VARCHAR(512),
    available_stock INTEGER,
    rrp NUMERIC(12,2),
    our_price NUMERIC(12,2)
);
```

**Problem:**
- Two separate ASIN columns (uk_asin, us_asin)
- Difficult to query by marketplace
- Hard to scale to other marketplaces (CA, DE, FR, etc.)
- One row per product regardless of marketplaces

### NEW Schema (Normalized) ✅
```sql
CREATE TABLE catalog_rows (
    id SERIAL PRIMARY KEY,
    asin VARCHAR(32) NOT NULL,
    marketplace VARCHAR(2) NOT NULL,
    title VARCHAR(512) NOT NULL,
    author VARCHAR(512),
    available_stock INTEGER,
    rrp NUMERIC(12,2),
    our_price NUMERIC(12,2),
    UNIQUE (asin, marketplace)
);
```

**Benefits:**
- ✅ Single ASIN column
- ✅ Explicit marketplace identifier ('US' or 'UK')
- ✅ Unique constraint prevents duplicate ASIN per marketplace
- ✅ Easy to query by marketplace
- ✅ Scalable to additional marketplaces
- ✅ Better for Keepa API integration (separate queries per marketplace)
- ✅ Allows marketplace-specific pricing and stock

---

## 📈 Data Transformation

### Before Migration
- **25 Excel rows** → **25 database rows**
- Some rows had `uk_asin=NULL`, some had `us_asin=NULL`
- Some rows had both ASINs filled

### After Migration
- **25 Excel rows** → **38 database rows**
- Each row is marketplace-specific
- If Excel row has both ASINs → creates 2 database rows

**Example Transformation:**

**Excel Row:**
```
UK ASIN: 912424788X
US ASIN: B0FCFLLM8L
Title: Demon Slayer Academy Vol 1-5
```

**Becomes 2 Database Rows:**
```sql
Row 1: asin='912424788X', marketplace='UK', title='Demon Slayer Academy Vol 1-5'
Row 2: asin='B0FCFLLM8L', marketplace='US', title='Demon Slayer Academy Vol 1-5'
```

---

## 📊 Migration Results

### Data Breakdown
- **Total Items:** 38
- **UK Marketplace Items:** 16
- **US Marketplace Items:** 22
- **Excel Rows Processed:** 25

### Quality Checks ✅
- All titles preserved
- All ASINs correctly assigned to marketplaces
- No data loss
- Unique constraints working
- Indexes created on `asin` and `marketplace` columns

---

## 🔧 Files Modified

### 1. `backend/app/models.py`
**Changes:**
- Removed `uk_asin` and `us_asin` columns
- Added `asin` column (NOT NULL)
- Added `marketplace` column (NOT NULL)
- Added unique constraint on `(asin, marketplace)`
- Added indexes for performance

### 2. `backend/app/load_excel.py`
**Changes:**
- Now processes UK and US ASINs separately
- Creates one database row per ASIN found
- Updates existing rows based on `(asin, marketplace)` combination
- Better logging (shows UK vs US creations)

**Before:**
```python
# Created one row with both ASINs
catalog_row = CatalogRow(
    uk_asin=uk_asin,
    us_asin=us_asin,
    title=title,
    ...
)
```

**After:**
```python
# Creates separate rows for UK and US
if uk_asin:
    uk_row = CatalogRow(
        asin=uk_asin,
        marketplace='UK',
        title=title,
        ...
    )

if us_asin:
    us_row = CatalogRow(
        asin=us_asin,
        marketplace='US',
        title=title,
        ...
    )
```

### 3. `backend/app/main.py`
**Changes:**
- Updated API responses to include `asin` and `marketplace`
- Added marketplace filtering: `/api/catalog?marketplace=UK`
- Updated statistics to show UK vs US breakdown
- Can now search by ASIN

**New API Features:**
```python
# Filter by marketplace
GET /api/catalog?marketplace=UK
GET /api/catalog?marketplace=US

# Search includes ASIN now
GET /api/catalog?search=B0FCFLLM8L

# Stats show marketplace breakdown
GET /api/stats
{
    "total_items": 38,
    "uk_marketplace_items": 16,
    "us_marketplace_items": 22,
    ...
}
```

### 4. `backend/app/smoke_test.py`
**Changes:**
- Updated to display `asin` and `marketplace`
- Statistics now show marketplace breakdown
- Query updated to count by marketplace

### 5. NEW: `backend/app/migrate_schema.py`
**Purpose:**
- Automated migration script
- Drops old table
- Creates new schema
- Reloads data

---

## 🎯 API Endpoint Updates

### `/api/catalog` - Enhanced with Marketplace Filtering

**Before:**
```json
GET /api/catalog

Response:
[
    {
        "id": 1,
        "uk_asin": "912424788X",
        "us_asin": "B0FCFLLM8L",
        "title": "Demon Slayer Academy Vol 1-5",
        ...
    }
]
```

**After:**
```json
GET /api/catalog

Response:
[
    {
        "id": 1,
        "asin": "912424788X",
        "marketplace": "UK",
        "title": "Demon Slayer Academy Vol 1-5",
        ...
    },
    {
        "id": 2,
        "asin": "B0FCFLLM8L",
        "marketplace": "US",
        "title": "Demon Slayer Academy Vol 1-5",
        ...
    }
]
```

**New Filtering Options:**
```bash
# Get UK items only
GET /api/catalog?marketplace=UK

# Get US items only
GET /api/catalog?marketplace=US

# Search UK items for Dragon Ball
GET /api/catalog?marketplace=UK&search=Dragon

# Search by ASIN
GET /api/catalog?search=B0FCFLLM8L
```

### `/api/stats` - Marketplace Breakdown

**Before:**
```json
{
    "total_items": 25,
    "items_with_uk_asin": 16,
    "items_with_us_asin": 22,
    ...
}
```

**After:**
```json
{
    "total_items": 38,
    "uk_marketplace_items": 16,
    "us_marketplace_items": 22,
    "uk_avg_price": 25.50,
    "us_avg_price": 22.80,
    ...
}
```

---

## 🔍 How to View in pgAdmin

### 1. Navigate to Table
```
Servers
└── PostgreSQL 18
    └── Databases
        └── wholesale_portal
            └── Schemas
                └── public
                    └── Tables
                        └── catalog_rows
```

### 2. View All Data
Right-click `catalog_rows` → **View/Edit Data** → **All Rows**

### 3. Filter by Marketplace
**Query Tool:**
```sql
-- View UK marketplace items only
SELECT * FROM catalog_rows WHERE marketplace = 'UK';

-- View US marketplace items only
SELECT * FROM catalog_rows WHERE marketplace = 'US';

-- Find books that exist in both marketplaces
SELECT c1.title, c1.asin as uk_asin, c2.asin as us_asin
FROM catalog_rows c1
JOIN catalog_rows c2 ON c1.title = c2.title
WHERE c1.marketplace = 'UK' AND c2.marketplace = 'US';
```

---

## 💡 Benefits for Keepa Integration

The new schema is **perfect** for Keepa API integration:

```python
# Query UK marketplace items
uk_items = session.query(CatalogRow).filter(
    CatalogRow.marketplace == 'UK'
).all()

# For each UK item, call Keepa API with UK domain
for item in uk_items:
    keepa_data = keepa.query(item.asin, domain='UK')
    # Update with UK-specific Amazon pricing

# Query US marketplace items
us_items = session.query(CatalogRow).filter(
    CatalogRow.marketplace == 'US'
).all()

# For each US item, call Keepa API with US domain
for item in us_items:
    keepa_data = keepa.query(item.asin, domain='US')
    # Update with US-specific Amazon pricing
```

---

## 🚀 Future Expansion

With this schema, adding new marketplaces is trivial:

```python
# Add Canada marketplace
CatalogRow(
    asin='CA_ASIN_HERE',
    marketplace='CA',
    title='Product Title',
    ...
)

# Add Germany marketplace
CatalogRow(
    asin='DE_ASIN_HERE',
    marketplace='DE',
    title='Product Title',
    ...
)
```

Supported marketplace codes:
- `UK` - United Kingdom
- `US` - United States
- `CA` - Canada
- `DE` - Germany
- `FR` - France
- `IT` - Italy
- `ES` - Spain
- `JP` - Japan
- `AU` - Australia

---

## ✅ Verification Checklist

- [x] Old table dropped successfully
- [x] New table created with correct schema
- [x] Unique constraint on (asin, marketplace) working
- [x] Indexes created on asin and marketplace columns
- [x] All 25 Excel rows processed
- [x] 38 database rows created (16 UK + 22 US)
- [x] Data correctly split by marketplace
- [x] API endpoints updated and working
- [x] Smoke test passing
- [x] No data loss
- [x] Documentation updated

---

## 📝 Migration Command

To run the migration again (or on another environment):

```bash
cd backend/app
python migrate_schema.py
```

The script is idempotent - safe to run multiple times.

---

## 🎉 Summary

**Your database is now:**
- ✅ Properly normalized
- ✅ Marketplace-aware
- ✅ Ready for Keepa API integration
- ✅ Scalable to new marketplaces
- ✅ Easier to query and maintain
- ✅ Cloud-ready (no changes needed)

**From 25 Excel rows → 38 marketplace-specific database rows!**

All tests passing ✅  
Ready for production 🚀

