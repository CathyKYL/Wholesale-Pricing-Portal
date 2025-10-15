# 🚀 Migrate to Supabase - Complete Guide

## Step-by-Step Migration Process

---

## 📦 STEP 1: Export Your Local Database

### **Option A: Export as Custom Format (Recommended)**
```bash
pg_dump -U postgres -h localhost -d wholesale_portal -F c -f wholesale_portal_backup.dump
```

### **Option B: Export as SQL (Alternative)**
```bash
pg_dump -U postgres -h localhost -d wholesale_portal > wholesale_portal_backup.sql
```

**What this exports:**
- ✅ All tables (`catalog_rows`, `dynamic.keepa_daily_data`, `dynamic.keepa_trends`, etc.)
- ✅ All data (6,466 records)
- ✅ Schemas (`public`, `dynamic`, `static`)
- ✅ Indexes and constraints
- ❌ Does NOT export users/roles (Supabase manages these)

**Expected file size:** ~2-5 MB

---

## 🌐 STEP 2: Set Up Supabase

### **Create Supabase Project:**

1. **Go to [supabase.com](https://supabase.com)**

2. **Sign Up / Log In**
   - Use GitHub account for easy login

3. **Create New Project**
   - Click "New Project"
   - **Name:** `wholesale-portal` (or any name)
   - **Database Password:** Generate a strong password (SAVE THIS!)
   - **Region:** Choose closest to you (e.g., US East, US West, EU)
   - **Plan:** Free (includes 500 MB database)
   - Click "Create new project"

4. **Wait for Setup** (2-3 minutes)
   - Project will provision PostgreSQL database
   - You'll see a green "Active" status when ready

---

## 🔗 STEP 3: Get Supabase Connection Details

1. **In your Supabase dashboard:**
   - Go to **Settings** (gear icon, left sidebar)
   - Click **Database** (under Configuration)

2. **Find Connection Info:**
   - Scroll down to "Connection string"
   - Look for **"Connection pooling"** section
   - Copy the **"URI"** (looks like this):
     ```
     postgresql://postgres.xxxxxxxxxxxxx:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres
     ```

3. **Important Notes:**
   - Use **Port 6543** (connection pooling) - NOT 5432
   - Use **Transaction mode** for best compatibility
   - Replace `[YOUR-PASSWORD]` with your actual password

**Example Connection String:**
```
postgresql://postgres.abcdefghijklmnop:MySecurePass123@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

---

## 📥 STEP 4: Import Data to Supabase

### **Method 1: Using psql (Recommended)**

**If you exported as .sql:**
```bash
psql "postgresql://postgres.xxxxx:PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" < wholesale_portal_backup.sql
```

**If you exported as .dump:**
```bash
pg_restore -h aws-0-us-west-1.pooler.supabase.com -p 6543 -U postgres.xxxxx -d postgres -v wholesale_portal_backup.dump
```

**Enter password when prompted.**

---

### **Method 2: Using Supabase Dashboard (For smaller databases)**

1. **Go to SQL Editor** in Supabase dashboard
2. **Open your .sql file** in a text editor
3. **Copy the SQL content**
4. **Paste into SQL Editor**
5. **Run** (might need to run in chunks if large)

---

### **Method 3: Using pgAdmin (GUI)**

1. **Open pgAdmin**
2. **Add New Server:**
   - Host: `aws-0-us-west-1.pooler.supabase.com`
   - Port: `6543`
   - Database: `postgres`
   - Username: `postgres.xxxxxxxxxxxxx`
   - Password: Your Supabase password
3. **Right-click database → Restore**
4. **Select your .dump or .sql file**
5. **Run restore**

---

## 🔧 STEP 5: Update Your Local .env File

**Edit your `.env` file:**

```bash
# BEFORE (local):
DATABASE_URL=postgresql://postgres:2407@localhost:5432/wholesale_portal

# AFTER (Supabase):
DATABASE_URL=postgresql://postgres.xxxxxxxxxxxxx:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

**Full .env example:**
```env
# API Keys
KEEPA_API_KEY=d452t88rcid318a6aii79vj5lgh5kd46o71u0ht5vnddqobb0b180ar4belbpitp

# Database Connection (Supabase Cloud)
DATABASE_URL=postgresql://postgres.xxxxxxxxxxxxx:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Excel dataset path
EXCEL_PATH=C:\VibeCode\Wholesale Pricing Portal\Wholesale-Pricing-Portal\Data.xlsx

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

---

## ✅ STEP 6: Test Cloud Database Connection

**Run this test script:**

```bash
cd backend/app
python -c "from sqlalchemy import create_engine, text; from dotenv import load_dotenv; import os; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); result = conn.execute(text('SELECT COUNT(*) as count FROM dynamic.keepa_daily_data')).fetchone(); print(f'✅ Connected to Supabase! Records: {result[0]}'); conn.close()"
```

**Expected output:**
```
✅ Connected to Supabase! Records: 6466
```

---

## 🧪 STEP 7: Test Daily Update on Cloud

**Test that your scripts work with Supabase:**

```bash
cd backend/app
python keepa_ingestor.py --test --daily
```

**Should show:**
- ✅ Connection successful
- ✅ Data fetched from Keepa
- ✅ Data saved to Supabase
- ✅ No errors

---

## 🔐 STEP 8: Add Supabase URL to GitHub Secrets

**Now that you have cloud database:**

1. **Go to your GitHub repository**
2. **Settings → Secrets and variables → Actions**
3. **Add/Update these secrets:**

   **DATABASE_URL:**
   ```
   postgresql://postgres.xxxxxxxxxxxxx:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   ```

   **KEEPA_API_KEY:**
   ```
   d452t88rcid318a6aii79vj5lgh5kd46o71u0ht5vnddqobb0b180ar4belbpitp
   ```

---

## 📊 STEP 9: Verify Data in Supabase

### **Using Supabase Dashboard:**

1. **Go to Table Editor** (left sidebar)
2. **Select schema:** `dynamic`
3. **Browse tables:**
   - `keepa_daily_data` - Should have 6,466 rows
   - `keepa_trends` - Should have 1,185 rows
   - `keepa_raw_log` - Should have 38+ rows
4. **Select schema:** `public`
5. **Browse tables:**
   - `catalog_rows` - Should have your catalog data

### **Using SQL Editor:**

```sql
-- Check all tables and row counts
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;

-- Should show:
-- dynamic.keepa_daily_data: 6466
-- dynamic.keepa_trends: 1185
-- dynamic.keepa_raw_log: 38
-- public.catalog_rows: your catalog size
```

---

## 🚀 STEP 10: Test GitHub Actions

**Now test your automated workflow:**

1. **Go to GitHub → Actions tab**
2. **Click "Daily Keepa Price Update"**
3. **Click "Run workflow"**
4. **Watch it run with cloud database**
5. **Check for ✅ green checkmark**

**It should:**
- ✅ Connect to Supabase
- ✅ Fetch new data
- ✅ Save to cloud database
- ✅ Complete successfully

---

## 🎯 Troubleshooting

### **"Connection refused" error:**
- ✅ Use port **6543** (not 5432)
- ✅ Use connection pooling URL
- ✅ Check password is correct

### **"SSL required" error:**
Add `?sslmode=require` to URL:
```
postgresql://postgres.xxx:pass@host:6543/postgres?sslmode=require
```

### **"Too many connections" error:**
- Use connection pooling (port 6543)
- Enable "Transaction mode" in Supabase settings

### **"Schema does not exist" error:**
Create schemas manually in Supabase SQL Editor:
```sql
CREATE SCHEMA IF NOT EXISTS dynamic;
CREATE SCHEMA IF NOT EXISTS static;
```

Then re-import data.

### **"Permission denied" error:**
Make sure you're using the correct username format:
```
postgres.xxxxxxxxxxxxx
```
(Not just `postgres`)

---

## 💰 Supabase Free Tier Limits

**What you get for FREE:**
- ✅ 500 MB database storage (you're using ~5 MB)
- ✅ Unlimited API requests
- ✅ 2 GB bandwidth/month
- ✅ 500 MB file storage
- ✅ SSL enabled
- ✅ Daily backups (7 days)
- ✅ Connection pooling

**You're well within limits!** 🎉

---

## 📚 Additional Resources

- [Supabase Docs](https://supabase.com/docs)
- [Connection Pooling Guide](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [SQL Editor](https://supabase.com/docs/guides/database/overview#sql-editor)

---

## ✅ Migration Checklist

- [ ] Export local database (pg_dump)
- [ ] Create Supabase project
- [ ] Get connection string
- [ ] Import data to Supabase
- [ ] Update local .env file
- [ ] Test local connection
- [ ] Test scripts work with cloud
- [ ] Add secrets to GitHub
- [ ] Test GitHub Actions workflow
- [ ] Verify data in Supabase dashboard
- [ ] Celebrate! 🎉

---

**Status:** Ready to migrate! Follow steps above. 🚀





