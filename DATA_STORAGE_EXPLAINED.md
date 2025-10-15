# 📊 Where Daily Keepa Updates Are Saved

## 🗄️ **Database: Supabase PostgreSQL**

**Host:** `aws-1-eu-west-1.pooler.supabase.com`  
**Database:** Your Supabase project database

---

## 📁 **Table Structure:**

### **Main Data Table: `backfill_test.dynamic_data`**

This is where **ALL daily updates are saved**:

```sql
Schema: backfill_test
Table:  dynamic_data

Columns:
- id                      (BIGINT, Primary Key)
- asin                    (VARCHAR, Product identifier)
- marketplace             (VARCHAR, 'US' or 'UK')
- fetch_date              (DATE, Date of data)
- current_buybox_price    (NUMERIC, Current Buy Box price)
- sales_rank_current      (INTEGER, Current sales rank)
- num_sellers             (INTEGER, Number of sellers)
- last_updated            (TIMESTAMP, When record was updated)

Unique Constraint: (asin, marketplace, fetch_date)
```

**Current Records:** 6,466 records (as of last check)

---

## 🔄 **How Updates Work:**

### **Daily Update Process:**

1. **Trigger:** GitHub Actions runs at 3 AM UTC daily
2. **Script:** `backend/app/keepa_ingestor.py --daily`
3. **Action:** 
   - Fetches latest data from Keepa API
   - Parses pricing, rank, and seller data
   - **Upserts** (insert or update) into `backfill_test.dynamic_data`
4. **Result:** Today's data is added/updated for all products

### **Upsert Logic:**
```sql
INSERT INTO backfill_test.dynamic_data (...)
VALUES (...)
ON CONFLICT (asin, marketplace, fetch_date)
DO UPDATE SET
    current_buybox_price = EXCLUDED.current_buybox_price,
    sales_rank_current = EXCLUDED.sales_rank_current,
    num_sellers = EXCLUDED.num_sellers,
    last_updated = NOW()
```

This means:
- ✅ If data for today doesn't exist → INSERT new record
- ✅ If data for today exists → UPDATE with latest values
- ✅ No duplicates!

---

## 🔍 **How Frontend Accesses the Data:**

### **1. Via PostgreSQL View: `public.historical_data`**

The frontend queries a VIEW that points to the data:

```sql
CREATE VIEW public.historical_data AS
SELECT 
    id,
    asin,
    marketplace,
    fetch_date,
    current_buybox_price,
    sales_rank_current,
    num_sellers,
    last_updated
FROM backfill_test.dynamic_data;
```

**Why a VIEW?**
- The `backfill_test` schema is NOT exposed via Supabase API
- The VIEW in `public` schema makes data accessible to frontend
- Provides security and abstraction layer

### **2. Frontend Query:**

In `Front end/dataService.js`:
```javascript
const { data, error } = await supabaseClient
    .from('historical_data')  // ← Queries the VIEW
    .select('fetch_date, current_buybox_price, sales_rank_current, num_sellers')
    .eq('asin', asin)
    .eq('marketplace', marketplace)
    .gte('fetch_date', dateString)  // Last 360 days
    .order('fetch_date', { ascending: true });
```

---

## 📈 **Additional Storage:**

### **Trends Table: `backfill_test.keepa_trends`**

After daily data is saved, trends are computed:

```sql
Schema: backfill_test
Table:  keepa_trends

Columns:
- asin
- marketplace
- week_start_date
- avg_buybox_price
- min_buybox_price
- max_buybox_price
- price_volatility
- avg_sales_rank
- min_sales_rank
- max_sales_rank
- rank_volatility
- data_points_count
```

**Purpose:** Weekly aggregated trends for analytics

### **Raw Log Table: `backfill_test.keepa_raw_log`**

Stores raw API responses for debugging:

```sql
Schema: backfill_test
Table:  keepa_raw_log

Columns:
- asin
- marketplace
- mode (daily/backfill)
- raw_response (JSON)
- status
- error_message
- tokens_consumed
- duration_ms
- created_at
```

**Purpose:** Audit trail and debugging

---

## 🔎 **How to View Your Data:**

### **Option 1: Supabase Dashboard**

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to **Table Editor**
4. Select schema: `backfill_test`
5. Select table: `dynamic_data`
6. View all records, filter by date, ASIN, etc.

### **Option 2: SQL Editor**

In Supabase Dashboard → SQL Editor:

```sql
-- See latest updates
SELECT 
    asin,
    marketplace,
    fetch_date,
    current_buybox_price,
    sales_rank_current,
    num_sellers,
    last_updated
FROM backfill_test.dynamic_data
ORDER BY last_updated DESC
LIMIT 50;

-- Count records per day
SELECT 
    fetch_date,
    COUNT(*) as record_count
FROM backfill_test.dynamic_data
GROUP BY fetch_date
ORDER BY fetch_date DESC
LIMIT 30;

-- See specific product history
SELECT 
    fetch_date,
    current_buybox_price,
    sales_rank_current,
    num_sellers
FROM backfill_test.dynamic_data
WHERE asin = '9124229466'
    AND marketplace = 'UK'
ORDER BY fetch_date DESC
LIMIT 30;
```

---

## 📊 **Data Flow Summary:**

```
┌─────────────────┐
│  GitHub Actions │
│  (3 AM UTC)     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Keepa API      │
│  (fetch data)   │
└────────┬────────┘
         │
         v
┌─────────────────────────────┐
│  backfill_test.dynamic_data │  ← Daily updates saved here
│  (Supabase PostgreSQL)      │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────┐
│  public.historical_data │  ← VIEW pointing to data
│  (Exposed via API)      │
└────────┬────────────────┘
         │
         v
┌─────────────────┐
│  Frontend       │
│  (Charts/Stats) │
└─────────────────┘
```

---

## ⏰ **Data Retention:**

**Current Setup:**
- Keeps data for **last 360 days** (used in frontend)
- All data is retained in database (no automatic deletion)
- You can query older data if needed

**Query Optimization:**
- Frontend only fetches last 360 days for charts
- Older data stays in database for historical analysis

---

## 🔐 **Security:**

✅ **Protected:**
- `backfill_test` schema NOT exposed via Supabase API
- Only authorized API calls can write
- Frontend reads via public VIEW (read-only)
- No direct table access from frontend

✅ **Access Control:**
- GitHub Actions uses `DATABASE_URL` secret (direct PostgreSQL access)
- Frontend uses `SUPABASE_ANON_KEY` (limited API access)
- Proper separation of concerns

---

## 📅 **Example Data:**

```
ASIN: 9124229466
Marketplace: UK
Fetch Date: 2024-10-14

current_buybox_price: 36.99
sales_rank_current: 7776688
num_sellers: 4
last_updated: 2024-10-14 03:15:23
```

This data is:
1. Saved to `backfill_test.dynamic_data`
2. Accessible via `public.historical_data` VIEW
3. Displayed in frontend Amazon Insight charts
4. Updated daily at 3 AM UTC

---

## 🎯 **Bottom Line:**

**Your daily Keepa updates are saved to:**

📍 **Supabase Database**
- Schema: `backfill_test`
- Table: `dynamic_data`
- Accessible via: `public.historical_data` VIEW
- Updated: Daily at 3 AM UTC
- Current records: 6,466+

**You can view them at:**
https://supabase.com/dashboard → Your Project → Table Editor → `backfill_test.dynamic_data`


