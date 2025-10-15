# Troubleshooting Amazon Insight Data

## Overview
This guide helps diagnose why Amazon Insight data (seller count, charts) is not showing up.

## What Was Fixed

### 1. ✅ ROI Calculator
- **Issue**: Showed "-100%" before user input
- **Fix**: Now shows "-" until user enters data
- **Location**: `index.html` line 256, `script.js` calculateROI()

### 2. ✅ Database Field Names
Updated to match your Supabase table exactly:

| Field in Code | Database Column |
|--------------|-----------------|
| `fetch_date` | Date of data fetch |
| `current_buybox_price` | Buy box price |
| `sales_rank_current` | Sales rank |
| `num_sellers` | Number of sellers |

### 3. ✅ Supabase Client Reference
- Added proper client initialization in `dataService.js`
- Function `getSupabaseClient()` retrieves the client from window object

### 4. ✅ Enhanced Logging
- Detailed console logs for debugging
- Shows query parameters, results, and errors

### 5. ✅ Seller Count Display - Made Smaller
- Reduced padding: 12px instead of 20px
- Smaller fonts: 13px label, 16px value
- More compact and subtle appearance

## Testing Steps

### Step 1: Open Browser Console
1. Open your Wholesale Portal in browser
2. Press `F12` to open DevTools
3. Go to "Console" tab

### Step 2: Check Initialization
Look for these console messages:
```
[Config] Application initialized with: {mode: 'LIVE DATA', ...}
[Supabase] ✅ Client initialized successfully
[DataService] ✅ Initialized successfully
```

❌ **If you see errors here**, your Supabase credentials are wrong.

### Step 3: Click on a Product
When you click a product, watch the console for:
```
[DataService] Querying backfill_test.dynamic_data for ASIN: xxx, Marketplace: US, From: 2024-xx-xx
[DataService] Query returned X records
[DataService] ✅ Fetched X days of historical data
[DataService] Seller count today: X
```

### Step 4: Run Diagnostic Test
In the browser console, type:
```javascript
testDynamicDataAccess('1778766800', 'US')
```

Replace `'1778766800'` with an ASIN from your product catalog.

**What to look for:**
- ✅ "Found X records" → Data is accessible
- ❌ "Error: relation does not exist" → Table not in public schema
- ❌ "Found 0 records" → No data for this ASIN/marketplace combination

## Common Issues & Solutions

### Issue 1: "Supabase client not available"
**Cause**: Supabase client failed to initialize

**Solutions**:
1. Check `config.js` - verify `USE_MOCK_DATA: false`
2. Verify Supabase credentials are correct
3. Check browser console for Supabase initialization errors
4. Ensure Supabase CDN script is loaded in `index.html`

### Issue 2: "No historical data found"
**Cause**: Data doesn't exist or query parameters don't match

**Solutions**:
1. Verify the ASIN exists in `backfill_test.dynamic_data` table
2. Check marketplace value matches **exactly** (case-sensitive):
   - Database has: `'US'` not `'us'`
   - Database has: `'UK'` not `'uk'`
3. Check if data exists from 360 days ago
4. Run diagnostic test to see what's in the database

### Issue 3: "relation 'dynamic_data' does not exist"
**Cause**: Table is not in the public schema

**Solutions**:
1. The code now tries both `public.dynamic_data` and `backfill_test.dynamic_data`
2. In Supabase dashboard, verify which schema contains the table
3. Check table permissions (RLS policies)

### Issue 4: Charts show but no data points
**Cause**: Data is null or incorrect format

**Solutions**:
1. Check if `current_buybox_price` and `sales_rank_current` have values
2. Look for console warnings about null data
3. Verify date format in `fetch_date` column

## Database Requirements

### Step 1: Create the RPC Function (REQUIRED)

Since your table is in the `backfill_test` schema, we need to create a database function to access it.

**Run this SQL in your Supabase SQL Editor:**

```sql
-- Create a function to get historical data from backfill_test schema
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

-- Grant execute permission to anonymous and authenticated users
GRANT EXECUTE ON FUNCTION get_historical_data(TEXT, TEXT, INTEGER) TO anon;
GRANT EXECUTE ON FUNCTION get_historical_data(TEXT, TEXT, INTEGER) TO authenticated;
```

### Step 2: Verify the Function Works

After creating the function, test it in SQL Editor:

```sql
-- Test the function
SELECT * FROM get_historical_data('1778766800', 'US', 360);
```

You should see rows returned with your historical data.

### Required Table Structure
**Schema**: `backfill_test`  
**Table**: `dynamic_data`

**Required Columns**:
```sql
- asin (text) - Product identifier
- marketplace (text) - 'US' or 'UK' (case-sensitive)
- fetch_date (date) - Date of data collection
- current_buybox_price (numeric) - Buy box price
- sales_rank_current (integer) - Sales rank
- num_sellers (integer) - Number of sellers
```

### Sample Data Check
In Supabase SQL Editor, run:
```sql
SELECT 
  asin,
  marketplace,
  COUNT(*) as record_count,
  MIN(fetch_date) as earliest_date,
  MAX(fetch_date) as latest_date,
  MAX(num_sellers) as seller_count_today
FROM backfill_test.dynamic_data
WHERE asin = '1778766800'
  AND marketplace = 'US'
GROUP BY asin, marketplace;
```

**Expected result:**
- `record_count` should be > 0 (ideally 360+ for full year)
- `latest_date` should be recent (today or yesterday)
- `seller_count_today` should show the current number

### RLS (Row Level Security) Policies
Ensure your table has policies that allow SELECT for anonymous users:

```sql
-- Check existing policies
SELECT * FROM pg_policies WHERE tablename = 'dynamic_data';

-- If no policies exist, create one:
CREATE POLICY "Allow public read access"
ON backfill_test.dynamic_data
FOR SELECT
TO anon
USING (true);
```

## What You Should See When Working

### On Product Page Load:
1. **Number of Sellers Today**: Should show a number (not "N/A")
2. **Buy Box Price Chart**: Should show line graph with price fluctuations
3. **Sales Rank Chart**: Should show line graph (lower numbers = better)

### Console Output (Success):
```
[DataService] Querying backfill_test.dynamic_data for ASIN: 1778766800, Marketplace: US, From: 2024-10-14
[DataService] Attempting query from public.dynamic_data...
[DataService] Query returned 365 records
[DataService] ✅ Fetched 365 days of historical data
[DataService] Date range: 2024-10-14 to 2025-10-14
[DataService] Seller count today: 2
[DataService] Sample buybox prices: [39.99, 39.99, 41.99]
[DataService] Sample sales ranks: [7776800, 7776800, 7776702]
```

## Still Not Working?

### Diagnostic Checklist:
- [ ] Supabase client initializes successfully
- [ ] Config has `USE_MOCK_DATA: false`
- [ ] Table `dynamic_data` exists in Supabase
- [ ] Table has data for the ASIN you're testing
- [ ] Marketplace value matches database exactly
- [ ] RLS policies allow anonymous read access
- [ ] Column names match exactly (case-sensitive)
- [ ] `fetch_date` is within last 360 days

### Get Help:
Run this in console and share the output:
```javascript
// Test connection and data
testDynamicDataAccess('YOUR-ASIN-HERE', 'US')

// Check current product
console.log('Current product:', state.selectedProduct)
console.log('Current market:', state.currentMarket)
```

## File Locations
- Configuration: `Front end/config.js`
- Data fetching: `Front end/dataService.js` (line 259-350)
- Display logic: `Front end/script.js` (line 908-1092)
- Styling: `Front end/styles.css` (line 867-922)
- HTML: `Front end/index.html` (line 260-284)

