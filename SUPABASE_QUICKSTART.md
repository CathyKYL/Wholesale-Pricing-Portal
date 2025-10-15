# 🚀 Supabase Migration - Quick Start

## ✅ Step 1: DONE - Database Exported!

Your database has been exported to:
- **File:** `wholesale_portal_backup.sql` (15.7 MB)
- **Contains:** 7,803 rows across 4 tables
- **Schemas:** `public`, `dynamic`, `static`

---

## 🌐 Step 2: Create Supabase Project (5 minutes)

### **Go to [supabase.com](https://supabase.com)**

1. **Sign up** (use GitHub for easy login)

2. **Create New Project:**
   - Click "New Project"
   - **Organization:** Create new or select existing
   - **Name:** `wholesale-portal`
   - **Database Password:** **IMPORTANT - SAVE THIS!**
     - Generate a strong password
     - Write it down somewhere safe
     - You'll need it in next steps
   - **Region:** Choose closest to you:
     - `us-west-1` (California)
     - `us-east-1` (Virginia)
     - `eu-west-1` (Ireland)
     - `ap-southeast-1` (Singapore)
   - **Plan:** Free

3. **Click "Create new project"**

4. **Wait 2-3 minutes** for setup to complete
   - You'll see a progress indicator
   - When done, you'll see "Active" status in green

---

## 🔗 Step 3: Get Your Connection String

1. **In Supabase Dashboard:**
   - Click **Settings** (gear icon, bottom left)
   - Click **Database** (under Configuration)

2. **Scroll down to "Connection string"**

3. **Look for "Connection pooling" section**

4. **Copy the URI** (should look like this):
   ```
   postgresql://postgres.abcdefghijklmnop:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   ```

5. **IMPORTANT: Replace `[YOUR-PASSWORD]` with your actual password**
   
   Example:
   ```
   Before: postgresql://postgres.abc123:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   After:  postgresql://postgres.abc123:MySecurePass123@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   ```

6. **Save this complete URL** - you'll need it!

---

## 📥 Step 4: Import Your Data

### **Option A: Using psql Command (Recommended)**

**If you have psql installed:**
```bash
psql "postgresql://postgres.xxxxx:PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" < wholesale_portal_backup.sql
```

Replace with your actual Supabase URL!

---

### **Option B: Using Supabase SQL Editor (Easier!)**

1. **Split the SQL file into chunks** (it's 15 MB - might be too large)
   
   I'll create a script to help you with this...

2. **Go to SQL Editor** in Supabase (left sidebar)

3. **Run each chunk** one by one

---

### **Option C: Let me create an import script for you!**

I can create a Python script that imports directly from Python - **EASIEST!**

Just tell me when you have:
- ✅ Supabase project created
- ✅ Connection string ready

---

## 🔧 Step 5: Update Your .env File

Once imported, update your local `.env`:

```env
# BEFORE (local):
DATABASE_URL=postgresql://postgres:2407@localhost:5432/wholesale_portal

# AFTER (Supabase - UPDATE THIS!):
DATABASE_URL=postgresql://postgres.xxxxx:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

---

## ✅ Step 6: Test Connection

Run this to verify:

```bash
python -c "from sqlalchemy import create_engine, text; from dotenv import load_dotenv; import os; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); result = conn.execute(text('SELECT COUNT(*) FROM dynamic.keepa_daily_data')).fetchone(); print(f'✅ Supabase connected! Records: {result[0]:,}'); conn.close()"
```

Should show: `✅ Supabase connected! Records: 6,466`

---

## 🎯 What You Need Right Now:

1. **Go to supabase.com**
2. **Create project** (5 minutes)
3. **Get connection string**
4. **Come back here - I'll help you import!**

---

**Tell me when you have the connection string and I'll create an import script for you!** 🚀





