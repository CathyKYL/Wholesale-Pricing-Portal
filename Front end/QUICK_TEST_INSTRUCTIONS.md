# Quick Test Instructions - Amazon Insight

## ⚠️ REQUIRED FIRST STEP

**You MUST create the database function first!**

Go to your **Supabase Dashboard** → **SQL Editor** and run:

```sql
CREATE OR REPLACE FUNCTION get_historical_data(
  p_asin TEXT,
  p_marketplace TEXT,
  p_days_back INTEGER DEFAULT 360
)
RETURNS TABLE (
  fetch_date DATE,
  current_buybox_price NUMERIC,
  sales_rank_current INTEGER,
  num_sellers INTEGER
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    d.fetch_date,
    d.current_buybox_price,
    d.sales_rank_current,
    d.num_sellers
  FROM backfill_test.dynamic_data d
  WHERE d.asin = p_asin
    AND d.marketplace = p_marketplace
    AND d.fetch_date >= CURRENT_DATE - p_days_back
  ORDER BY d.fetch_date ASC;
END;
$$;

GRANT EXECUTE ON FUNCTION get_historical_data(TEXT, TEXT, INTEGER) TO anon;
GRANT EXECUTE ON FUNCTION get_historical_data(TEXT, TEXT, INTEGER) TO authenticated;
```

**Why?** Your table is in the `backfill_test` schema, which isn't exposed by default. This function lets us access it.

---

## ✅ What Was Fixed

1. **ROI Calculator**: Shows "-" instead of "-100%" before user input
2. **Database Fields**: Mapped correctly to your Supabase columns
3. **Supabase Client**: Properly referenced in dataService
4. **Seller Display**: Made smaller and more compact
5. **Logging**: Added detailed console debugging
6. **Schema Access**: Now uses RPC function to access backfill_test schema

## 🧪 Quick Test (2 Minutes)

### Open the Portal and Check Console

1. **Open** your Wholesale Portal in browser
2. **Press F12** → Go to Console tab
3. **Look for** these messages:
   ```
   [Config] Application initialized with: {mode: 'LIVE DATA', ...}
   [Supabase] ✅ Client initialized successfully
   ```

4. **Click any product** in the catalog
5. **Watch console** for:
   ```
   [DataService] Querying backfill_test.dynamic_data...
   [DataService] Query returned X records
   [DataService] Seller count today: X
   ```

### Run Diagnostic Command

In browser console, type:

```javascript
testDynamicDataAccess('1778766800', 'US')
```

**Replace with an ASIN from your database!**

## 📊 Expected Results

### If Working:
- ✅ **Number of Sellers Today**: Shows a number (e.g., "2")
- ✅ **Charts**: Display with data points
- ✅ **Console**: `✅ Found X records`

### If Not Working:
Check console for one of these:

| Message | Cause | Fix |
|---------|-------|-----|
| `Supabase client not available` | Not initialized | Check config.js credentials |
| `No historical data found` | No matching data | Wrong ASIN or marketplace |
| `relation does not exist` | Table not found | Check schema/table name |
| `Found 0 records` | Data doesn't exist | Add data to database |

## 🔍 Verify Your Database

Run this SQL in Supabase:

```sql
-- Check if data exists for a product
SELECT 
  COUNT(*) as total_records,
  MAX(fetch_date) as latest_date,
  MAX(num_sellers) as current_sellers
FROM backfill_test.dynamic_data
WHERE asin = '1778766800'  -- Replace with your ASIN
  AND marketplace = 'US';
```

**Expected:**
- `total_records` > 0
- `latest_date` = recent date
- `current_sellers` = some number

## 🎯 Most Common Issue

**Problem**: "N/A" shown for seller count, no data in charts

**Root Cause**: Usually one of these:
1. ❌ ASIN in `catalog_rows` doesn't match ASIN in `dynamic_data`
2. ❌ Marketplace case doesn't match (`'US'` vs `'us'`)
3. ❌ Table permissions (RLS) not set correctly
4. ❌ Data older than 360 days

**Quick Fix**: Run the diagnostic test to see exactly what's wrong!

## 📞 Share This If You Need Help

Run in console and share output:
```javascript
// 1. Test database access
testDynamicDataAccess('1778766800', 'US')

// 2. Check what product you're viewing
console.log('Selected ASIN:', state.selectedProduct?.asin)
console.log('Market:', state.currentMarket)
```

---

**Full Documentation**: See `TROUBLESHOOTING_AMAZON_INSIGHT.md`

