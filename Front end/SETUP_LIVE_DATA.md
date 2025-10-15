# 🚀 Setup Live Data - Quick Guide

## ✅ Your App is Now Set to LIVE DATA MODE

Mock data is disabled by default. The app will fetch from your PostgreSQL (Supabase) database.

---

## 📋 Setup Checklist

### Step 1: Test Database Connection ✅

You should have just tested this! If not:

1. Open `test_frontend_database_connection.html`
2. Enter your Supabase URL and Key
3. Click "Test Database Connection"
4. Click "Fetch Products"

**Expected result:** Shows your 38 products from database

---

### Step 2: Update Frontend Config

Edit **`config.js`** and paste your credentials:

```javascript
const config = {
    USE_MOCK_DATA: false,  // ✅ Already set to false
    
    // ⚠️ REPLACE THESE:
    SUPABASE_URL: 'https://YOUR-PROJECT.supabase.co',  // ← Paste here
    SUPABASE_ANON_KEY: 'eyJ...',  // ← Paste here
    
    API_BASE_URL: 'http://localhost:8000',  // Backend API
};
```

---

### Step 3: Setup Backend API

**WHY?** The backend API is needed for **quote generation only**. Product fetching is direct to Supabase.

#### Create `.env` file:

In your **project root** (not in "Front end"), create `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres

# Supabase API (same as frontend)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Environment
ENVIRONMENT=development

# CORS (allow frontend)
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# Security
SECRET_KEY=any-random-string-here
LOG_LEVEL=INFO
```

#### Start Backend:

```bash
cd backend/app
python main.py
```

Should see: `Uvicorn running on http://127.0.0.1:8000`

---

### Step 4: Run Frontend

```bash
cd "Front end"
python -m http.server 5500
```

Open: `http://localhost:5500`

---

## ✅ Verify Everything Works

Open browser console (`F12`), should see:

```
================================================================================
📚 BOOK PORTAL - Wholesale Quotation Platform
================================================================================

[Supabase] ✅ Client initialized successfully
[Supabase] Testing connection...
[Supabase] ✅ Connection successful!
[Supabase] Found 38 products in database

✅ Book Portal initialized successfully
📦 Mode: LIVE DATA (Supabase)
📊 Loaded 38 products

Ready for use! Try searching for a book.
================================================================================
```

---

## 🔄 Data Flow

### Frontend → Supabase (Direct)
✅ Fetch products  
✅ Get Buy Box history  
✅ Search products  

### Frontend → Backend API → Supabase
✅ Generate quotes (complex ROI calculations)

---

## ❓ Do You Need the Backend API?

**YES** - But only for quote generation.

**Why not direct to Supabase for quotes?**
- Quote calculator has complex logic (smooth ROI, fees, tiers)
- Should run server-side for consistency and security
- Too complex for frontend calculations

**What if I skip the API?**
- ✅ Product listing will work
- ✅ Catalog will work
- ✅ Search will work
- ❌ Quote generation will fail
- ❌ ROI calculator won't have live values

---

## 🐛 Troubleshooting

**"Connection Error"**
→ Check SUPABASE_URL and SUPABASE_ANON_KEY in config.js

**"No products found"**
→ Run test_frontend_database_connection.html to verify database has products

**Quote generation fails**
→ Backend API not running. Start with: `cd backend/app && python main.py`

**CORS error**
→ Add your frontend URL to .env CORS_ORIGINS

---

## 📊 Current Status

✅ Frontend configured for LIVE DATA  
✅ Mock data kept as fallback only  
⏳ Need to add Supabase credentials to config.js  
⏳ Need to start backend API for quote generation  

---

**Next:** Complete Step 2 above (update config.js with your Supabase credentials)





