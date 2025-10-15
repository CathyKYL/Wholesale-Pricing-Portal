# 🔧 Fix Amazon Insight Data - Step by Step Guide

## 📋 Problem Summary

Your frontend can't access `backfill_test.dynamic_data` table because:
1. **The table exists in the `backfill_test` schema** (not `public`)
2. **Supabase only exposes the `public` schema by default** via PostgREST API
3. **The RPC function doesn't exist** to bridge the gap

This is why you see these errors:
- ❌ `404 Not Found` when querying `backfill_test.dynamic_data`
- ❌ `Could not find the function public.get_historical_data`
- ❌ "Number of Sellers Today: N/A"
- ❌ Empty charts

---

## ✅ Solution (3 Steps)

### **Step 1: Verify Your Data Exists**

1. Open **Supabase Dashboard** → **SQL Editor**
2. Paste and run this query:

```sql
SELECT COUNT(*) FROM backfill_test.dynamic_data;
```

**Expected Result:**
- If you get a **number > 0**: ✅ Data exists, proceed to Step 2
- If you get **0**: ⚠️ You need to import data first (see "No Data" section below)
- If you get **error "relation does not exist"**: ❌ The table wasn't created (see "No Table" section below)

---

### **Step 2: Create the RPC Function**

1. Open **Supabase Dashboard** → **SQL Editor**
2. Open the file: **`FIX_BACKFILL_ACCESS.sql`** (in your project root)
3. Copy the entire contents
4. Paste into Supabase SQL Editor
5. Click **Run**

**Expected Result:**
```
Success. No rows returned
```

✅ The function `public.get_historical_data()` is now created!

---

### **Step 3: Test the Fix**

#### **Option A: Browser Test Page (Easiest)**

1. Open the file: **`test_backfill_access.html`** in your browser
2. Enter your Supabase URL and Anon Key (from `Front end/config.js`)
3. Click **"Initialize Client"**
4. Enter an ASIN (e.g., `1778766800`)
5. Click **"Test RPC Function"**

**Expected Result:**
```
✅ RPC function called successfully!
   Records returned: 365
```

#### **Option B: Frontend Test (Real Application)**

1. Open your **Wholesale Portal** in browser
2. Press **F12** to open DevTools → **Console** tab
3. Run this command:

```javascript
testDynamicDataAccess('1778766800', 'US')
```

Replace `'1778766800'` with an actual ASIN from your catalog.

**Expected Result:**
```
✅ Found 365 records via RPC
```

4. Click on a product in your catalog
5. Check the **"Amazon Insight"** section:
   - ✅ Should show "Number of Sellers Today: X" (not N/A)
   - ✅ Should show Buy Box Price chart with data
   - ✅ Should show Sales Rank chart with data

---

## 🎯 Success Criteria

After completing all steps, you should see:

### In Browser Console:
```
[DataService] Fetching historical data for ASIN 1778766800...
[DataService] ✅ RPC function successful!
[DataService] Query returned 365 records
[DataService] ✅ Fetched 365 days of historical data
[DataService] Seller count today: 5
```

### In Frontend:
- ✅ **Number of Sellers Today**: Shows a number (not "N/A")
- ✅ **Buy Box Price Chart**: Shows 360 days of price history
- ✅ **Sales Rank Chart**: Shows 360 days of rank history

---

## ❌ Troubleshooting

### Issue: "function get_historical_data does not exist"

**Cause**: Step 2 wasn't completed or failed

**Solution**:
1. Go back to Step 2
2. Make sure you ran the **entire** `FIX_BACKFILL_ACCESS.sql` file
3. Check for errors in the SQL Editor output
4. Verify the function exists:
   ```sql
   SELECT routine_name FROM information_schema.routines 
   WHERE routine_name = 'get_historical_data';
   ```
   Should return 1 row.

---

### Issue: "Found 0 records" (No Data Returned)

**Cause**: The ASIN doesn't exist in your database

**Solution**:
1. Check what ASINs you have:
   ```sql
   SELECT asin, marketplace, COUNT(*) as days_of_data
   FROM backfill_test.dynamic_data
   GROUP BY asin, marketplace
   ORDER BY days_of_data DESC;
   ```

2. Use one of the ASINs from the results in your test

3. Make sure the marketplace matches exactly:
   - ✅ `'US'` not `'us'`
   - ✅ `'UK'` not `'uk'`

---

### Issue: Table "backfill_test.dynamic_data" doesn't exist

**Cause**: The table was never created

**Solution**:
Run the table creation script:

```bash
cd backend/app
python create_backfill_tables.py
```

This creates:
- `backfill_test.dynamic_data` (for daily historical data)
- `backfill_test.keepa_trends` (for weekly trends)
- `backfill_test.keepa_raw_log` (for API logs)

---

### Issue: Table exists but has no data (COUNT = 0)

**Cause**: Data was never imported

**Solution**:
You need to run your data import/backfill script. Check these files:

1. **For Keepa data**: `backend/app/keepa_backfill_test.py`
2. **For Supabase import**: `import_to_supabase_v2.py`

Example:
```bash
python backend/app/keepa_backfill_test.py --backfill
```

---

### Issue: "Permission denied for schema backfill_test"

**Cause**: Missing permissions

**Solution**:
Run these SQL commands in Supabase SQL Editor:

```sql
-- Grant usage on schema
GRANT USAGE ON SCHEMA backfill_test TO anon;
GRANT USAGE ON SCHEMA backfill_test TO authenticated;

-- Grant select on table
GRANT SELECT ON backfill_test.dynamic_data TO anon;
GRANT SELECT ON backfill_test.dynamic_data TO authenticated;
```

---

### Issue: Data is old (days_since_update > 7)

**Cause**: Daily updates aren't running

**Solution**:
Set up a daily cron job or scheduled task:

```bash
# Run daily to keep data fresh
python backend/app/keepa_ingestor.py --daily
```

---

## 📊 Understanding the Architecture

### **Why can't we access backfill_test schema directly?**

```
┌─────────────────────────────────────────┐
│  Frontend (Browser)                     │
│  ↓ Supabase JS Client                   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Supabase PostgREST API                 │
│  ✅ Exposes: public schema              │
│  ❌ Hides: backfill_test schema         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  PostgreSQL Database                    │
│  ├─ public schema                       │
│  │   ├─ catalog (products)              │
│  │   └─ get_historical_data() ← HERE!  │
│  └─ backfill_test schema                │
│      └─ dynamic_data (historical data)  │
└─────────────────────────────────────────┘
```

**The Solution:**
- Create an RPC function in the **public** schema
- This function is exposed via the API
- The function can access **backfill_test** schema internally
- Frontend calls the function → function queries backfill_test → returns data!

---

## 🔍 Diagnostic Tools

### **1. SQL Check (Supabase Dashboard)**
File: `CHECK_BACKFILL_DATA.sql`  
Purpose: Check what data exists in your database

### **2. Browser Test Page**
File: `test_backfill_access.html`  
Purpose: Test the RPC function from browser

### **3. Console Function (Frontend)**
Function: `testDynamicDataAccess(asin, marketplace)`  
Purpose: Test from your actual frontend application

---

## 📁 File Reference

| File | Purpose |
|------|---------|
| `FIX_BACKFILL_ACCESS.sql` | Creates the RPC function to access backfill_test schema |
| `CHECK_BACKFILL_DATA.sql` | Diagnostic queries to check what data exists |
| `test_backfill_access.html` | Browser-based test page for RPC function |
| `Front end/dataService.js` | Frontend code that calls the RPC function |
| `backend/app/create_backfill_tables.py` | Creates the backfill_test tables |

---

## 🎯 Quick Command Reference

```bash
# 1. Create tables (if they don't exist)
cd "backend/app"
python create_backfill_tables.py

# 2. Import initial data (backfill 360 days)
python keepa_backfill_test.py --backfill

# 3. Check data was imported
# Run in Supabase SQL Editor:
# SELECT COUNT(*) FROM backfill_test.dynamic_data;

# 4. Create RPC function
# Copy/paste FIX_BACKFILL_ACCESS.sql into Supabase SQL Editor

# 5. Test in frontend
# Open browser console, run:
# testDynamicDataAccess('YOUR-ASIN', 'US')
```

---

## ✅ Final Checklist

Before closing this issue, verify:

- [ ] `backfill_test.dynamic_data` table exists
- [ ] Table has data (COUNT > 0)
- [ ] RPC function `public.get_historical_data()` exists
- [ ] Function has proper permissions (GRANT EXECUTE)
- [ ] Test page (`test_backfill_access.html`) shows success
- [ ] Frontend shows "Number of Sellers Today: X"
- [ ] Frontend charts display historical data
- [ ] Browser console shows no 404 errors
- [ ] Console shows: "[DataService] ✅ Fetched X days of historical data"

---

## 💬 Still Having Issues?

1. Open `test_backfill_access.html` in browser
2. Click **"Run Full Diagnostic"**
3. Copy the entire output
4. Share it for debugging

The diagnostic will tell you exactly what's wrong and how to fix it!

---

**Status**: Ready to fix! Follow the 3 steps above and you'll have working Amazon Insight data in minutes! 🎉




