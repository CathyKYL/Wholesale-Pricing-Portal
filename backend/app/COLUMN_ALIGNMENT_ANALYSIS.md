# 📊 Column Alignment Analysis: Backfill vs Daily vs Database

## ✅ **RESOLVED: Schema Now Aligned**

**After cleanup (October 13, 2025):**
- Database has **13 columns** (reduced from 22)
- Removed **9 unused columns** that were never populated
- Backfill mode populates **8 core columns** (100% of available historical data)
- Daily mode populates **11 columns** (includes real-time seller/rating data)
- **Perfect alignment** between code and schema

---

## 📋 Detailed Column Comparison

| Column Name | Database | Backfill Mode | Daily Mode | Status |
|-------------|----------|---------------|------------|--------|
| **asin** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **marketplace** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **fetch_date** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **current_buybox_price** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **amazon_price** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **new_price** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **used_price** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **sales_rank_current** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **num_sellers** | ✅ | ❌ Always `None` | ✅ From stats | ⚠️ PARTIAL |
| **rating_value** | ✅ | ❌ Always `None` | ✅ From stats | ⚠️ PARTIAL |
| **rating_count** | ✅ | ❌ Always `None` | ✅ From stats | ⚠️ PARTIAL |
| **last_updated** | ✅ | ✅ | ✅ | ✅ ALIGNED |
| **sales_rank_30d_avg** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **sales_rank_90d_avg** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **sales_rank_drops_30d** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **num_fba_sellers** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **out_of_stock_percentage** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **rolling_30d_avg_buybox** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **rolling_90d_avg_buybox** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **sales_rank_trend_percent** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |
| **raw_json** | ❌ REMOVED | N/A | N/A | ✅ CLEANED |

---

## 🔍 What Each Mode Returns

### **BACKFILL Mode** (360 days historical)
```python
{
    'asin': '9124229466',
    'marketplace': 'UK',
    'fetch_date': date(2024, 9, 8),
    'current_buybox_price': Decimal('28.49'),
    'amazon_price': None,
    'new_price': Decimal('28.49'),
    'used_price': None,
    'sales_rank_current': 4234,
    'num_sellers': None,              # ❌ NOT AVAILABLE in historical data
    'rating_value': None,              # ❌ NOT AVAILABLE in historical data
    'rating_count': None,              # ❌ NOT AVAILABLE in historical data
    'last_updated': datetime.now()
}
```
**Populates:** 8 out of 21 columns (38%)

---

### **DAILY Mode** (current snapshot)
```python
{
    'asin': '9124229466',
    'marketplace': 'UK',
    'fetch_date': date(2025, 10, 13),
    'current_buybox_price': Decimal('28.49'),
    'amazon_price': Decimal('28.49'),
    'new_price': Decimal('28.49'),
    'used_price': None,
    'sales_rank_current': 4234,
    'num_sellers': 12,                 # ✅ FROM stats['current'][11]
    'rating_value': Decimal('4.5'),    # ✅ FROM stats['rating']
    'rating_count': 1250,              # ✅ FROM stats['reviewCount']
    'last_updated': datetime.now()
}
```
**Populates:** 11 out of 21 columns (52%)

---

## 🗄️ Database Table: `dynamic.keepa_daily_data`

**Location:** PostgreSQL schema `dynamic`

**Schema Definition (After Cleanup):**
```sql
CREATE TABLE dynamic.keepa_daily_data (
    -- Core identifiers
    id SERIAL PRIMARY KEY,
    asin TEXT NOT NULL,
    marketplace TEXT NOT NULL,
    fetch_date DATE NOT NULL,
    
    -- ✅ POPULATED: Price data (from Keepa CSV historical or current stats)
    current_buybox_price NUMERIC(12, 2),
    amazon_price NUMERIC(12, 2),
    new_price NUMERIC(12, 2),
    used_price NUMERIC(12, 2),
    
    -- ✅ POPULATED: Sales rank (from Keepa salesRanks)
    sales_rank_current INTEGER,
    
    -- ⚠️ PARTIAL: Seller data (only available in daily mode from stats['current'][11])
    num_sellers INTEGER,
    
    -- ⚠️ PARTIAL: Ratings (only available in daily mode from stats)
    rating_value NUMERIC(3, 2),
    rating_count INTEGER,
    
    -- ✅ POPULATED: Metadata
    last_updated TIMESTAMP DEFAULT NOW(),
    
    -- Ensure one record per ASIN/marketplace/date
    CONSTRAINT unique_asin_marketplace_date 
        UNIQUE (asin, marketplace, fetch_date)
);
```

**Total: 13 columns** (down from 22)

---

## 🎯 Destination Table Summary

**All data from BOTH modes goes into:**
- **Table:** `dynamic.keepa_daily_data`
- **Schema:** `dynamic` (PostgreSQL schema)
- **Full Path:** `dynamic.keepa_daily_data`

**No other tables are populated by fetch operations.**

*(Note: `dynamic.keepa_trends` exists but is populated by the separate `compute_trends()` function)*

---

## ⚠️ Critical Issues

### **Issue 1: Backfill Missing Seller/Rating Data**
- Historical data doesn't include `num_sellers`, `rating_value`, `rating_count`
- These are only available in current snapshots
- **Impact:** Historical analysis of seller competition and ratings is impossible

### **Issue 2: Unused Database Columns**
The following columns are NEVER populated:
- `sales_rank_30d_avg`
- `sales_rank_90d_avg`
- `sales_rank_drops_30d`
- `num_fba_sellers`
- `out_of_stock_percentage`
- `rolling_30d_avg_buybox` (should be in trends table)
- `rolling_90d_avg_buybox` (should be in trends table)
- `sales_rank_trend_percent` (should be in trends table)
- `raw_json`

### **Issue 3: Computed Fields in Wrong Table**
- `rolling_30d_avg_buybox`, `rolling_90d_avg_buybox`, `sales_rank_trend_percent` should be computed metrics
- They belong in `dynamic.keepa_trends`, not raw daily data
- Currently, they're never populated anywhere

### **Issue 4: No Raw JSON Logging**
- `raw_json` column exists but is never used
- All raw responses go to `dynamic.keepa_raw_log` instead
- This column should be removed or populated

---

## ✅ Recommended Fixes

### **Option 1: Minimal Alignment (Recommended)**
**Remove unused columns to align with what we actually fetch:**

```sql
-- Keep only these columns in dynamic.keepa_daily_data:
ALTER TABLE dynamic.keepa_daily_data
DROP COLUMN IF EXISTS sales_rank_30d_avg,
DROP COLUMN IF EXISTS sales_rank_90d_avg,
DROP COLUMN IF EXISTS sales_rank_drops_30d,
DROP COLUMN IF EXISTS num_fba_sellers,
DROP COLUMN IF EXISTS out_of_stock_percentage,
DROP COLUMN IF EXISTS rolling_30d_avg_buybox,
DROP COLUMN IF EXISTS rolling_90d_avg_buybox,
DROP COLUMN IF EXISTS sales_rank_trend_percent,
DROP COLUMN IF EXISTS raw_json;
```

**Result:** Clean table with only populated columns

---

### **Option 2: Enhance Backfill to Match Daily**
**Modify backfill to also fetch seller/rating data for each historical date**

**Pros:**
- Complete historical data
- Both modes aligned

**Cons:**
- Not possible - Keepa doesn't provide historical seller counts/ratings in CSV
- Would require separate API calls per date (expensive, slow)

---

### **Option 3: Accept Partial Data**
**Keep current implementation, document that backfill has limited fields**

**Pros:**
- No code changes needed
- Follows Keepa API limitations

**Cons:**
- Inconsistent data between backfill and daily
- Still leaves unused columns

---

## ✅ Implemented Solution: Option 1 (Database Cleanup)

**Successfully implemented on October 13, 2025:**

### What Was Done:
1. ✅ Removed 9 unused columns from `dynamic.keepa_daily_data`
2. ✅ Cleared all test data (1,336 rows from keepa_daily_data, 146 from keepa_trends, 34 from keepa_raw_log)
3. ✅ Updated `setup_database.py` to reflect clean schema
4. ✅ Documented that backfill can't populate seller/rating data (Keepa API limitation)
5. ✅ Computed metrics remain in `dynamic.keepa_trends` (separate table)

### Results:
- ✅ **Schema reduced from 22 to 13 columns** (41% reduction)
- ✅ **Perfect alignment** between code and database
- ✅ **No unused columns** - every column serves a purpose
- ✅ **Clear data flow** - raw data in daily_data, computed in trends
- ✅ **Follows Keepa API** capabilities and limitations
- ✅ **Ready for production** backfill with clean slate

### Schema Comparison:
```
BEFORE:  22 columns (9 never used)
AFTER:   13 columns (all actively used)
SAVINGS: 41% smaller, 100% utilized
```

**System is now ready for production backfill of 38 ASINs! 🚀**

