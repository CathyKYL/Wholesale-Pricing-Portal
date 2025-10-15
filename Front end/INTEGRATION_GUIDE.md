# 📚 Book Portal - Frontend Integration Guide

## 🎯 Overview

Your Book Portal frontend is now **fully integrated** with the Supabase backend! This guide will help you set everything up and switch between demo mode and live data mode.

---

## 🚀 Quick Start

### **Option 1: Demo Mode (Mock Data)**
Just open `index.html` in your browser - everything works out of the box!

### **Option 2: Live Data Mode (Supabase + Backend)**
Follow the setup instructions below to connect to your live database.

---

## 📁 New Files Created

The integration added these new files to your "Front end" folder:

1. **`config.js`** - Configuration and feature toggles
2. **`supabaseClient.js`** - Supabase database connection
3. **`dataService.js`** - Unified data access layer
4. **`INTEGRATION_GUIDE.md`** - This file

### Modified Files:
- **`index.html`** - Added script includes and Supabase CDN
- **`script.js`** - Updated to use DataService for all data operations

---

## ⚙️ Configuration

### Step 1: Get Your Supabase Credentials

1. Go to your Supabase project dashboard
2. Click **Settings** → **API**
3. Copy these two values:
   - **Project URL** (e.g., `https://abcd1234.supabase.co`)
   - **anon public key** (starts with `eyJ...`)

### Step 2: Update `config.js`

Open `Front end/config.js` and update these values:

```javascript
const config = {
    // Set to FALSE to use live Supabase data
    USE_MOCK_DATA: false,  // ← Change this to false
    
    // Replace with your actual Supabase credentials
    SUPABASE_URL: 'https://your-project.supabase.co',  // ← Paste your URL
    SUPABASE_ANON_KEY: 'your-anon-key-here',  // ← Paste your key
    
    // Update if your backend is running elsewhere
    API_BASE_URL: 'http://localhost:8000',  // ← Backend API URL
    
    // Rest of config...
};
```

---

## 🔧 Backend Setup

### Step 1: Create `.env` File

In your **project root** (not in "Front end"), create a `.env` file:

```bash
# Database Connection (Supabase)
DATABASE_URL=postgresql://postgres:[password]@[project-ref].supabase.co:5432/postgres

# Supabase API (for frontend AND backend)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Keepa API (optional - for live Amazon data)
KEEPA_API_KEY=your_keepa_api_key_here

# Environment
ENVIRONMENT=development

# CORS (allow frontend to call backend)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:5500

# Security
SECRET_KEY=your_secret_key_here
LOG_LEVEL=INFO
```

### Step 2: Install Python Dependencies

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install fastapi uvicorn supabase python-dotenv sqlalchemy psycopg2-binary
```

### Step 3: Start the Backend Server

```bash
# From project root
cd backend/app
python main.py

# OR using uvicorn directly
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     CORS enabled for origins: [...]
INFO:     Running in development mode
```

---

## 🌐 Running the Frontend

### Option 1: Simple File Server (Recommended)

```bash
# From "Front end" directory
cd "Front end"

# Python 3
python -m http.server 5500

# OR Python 2
python -m SimpleHTTPServer 5500
```

Then open: `http://localhost:5500`

### Option 2: VS Code Live Server

1. Install "Live Server" extension
2. Right-click `index.html`
3. Select "Open with Live Server"

### Option 3: Direct File Access

Just open `index.html` in your browser (works for mock data mode only).

---

## 🧪 Testing the Integration

### Check 1: Console Messages

Open Developer Tools (`F12`) and check the Console. You should see:

**Mock Data Mode:**
```
================================================================================
📚 BOOK PORTAL - Wholesale Quotation Platform
================================================================================

✅ Book Portal initialized successfully
📦 Mode: MOCK DATA (Demo)
📊 Loaded 12 products

Ready for use! Try searching for a book.
================================================================================
```

**Live Data Mode:**
```
================================================================================
📚 BOOK PORTAL - Wholesale Quotation Platform
================================================================================

[Supabase] ✅ Client initialized successfully
[Supabase] Project URL: https://your-project.supabase.co
[Supabase] Testing connection...
[Supabase] ✅ Connection successful!
[Supabase] Found 38 products in database
✅ Book Portal initialized successfully
📦 Mode: LIVE DATA (Supabase)
📊 Loaded 38 products

Ready for use! Try searching for a book.
================================================================================
```

### Check 2: Search for a Product

1. Enter an ASIN (e.g., `143914995X`) in the search box
2. Select marketplace (US or UK)
3. Click **Search**

**Expected behavior:**
- Product details display
- Quote price shows (from backend calculator)
- ROI calculator populates with live values
- Charts render with historical data

### Check 3: Market Toggle

1. Search for a product
2. Toggle between US and UK markets
3. Quote should regenerate for the new marketplace

### Check 4: Catalog

1. Click the **Catalog** tab
2. Products should load from database
3. Filters should work correctly
4. Clicking a product should display it in Quotation tab

---

## 🔄 Switching Between Mock and Live Data

### To Use Mock Data (Demo Mode):

```javascript
// config.js
USE_MOCK_DATA: true,
```

**Pros:**
- ✅ Works offline
- ✅ No backend required
- ✅ Instant loading
- ✅ Perfect for demos

**Cons:**
- ❌ Only 12 sample products
- ❌ Static data (no live quotes)
- ❌ No real ROI calculations

### To Use Live Data (Production Mode):

```javascript
// config.js
USE_MOCK_DATA: false,
SUPABASE_URL: 'https://your-project.supabase.co',
SUPABASE_ANON_KEY: 'your-actual-key',
```

**Pros:**
- ✅ Real-time database access
- ✅ Live quote generation
- ✅ Accurate ROI calculations
- ✅ Historical data charts
- ✅ All 38 products

**Cons:**
- ❌ Requires backend running
- ❌ Requires Supabase connection
- ❌ Slower initial load

---

## 📊 How It Works

### Data Flow Architecture

```
Frontend (Browser)
    ↓
config.js (Feature Toggle)
    ↓
DataService (Unified Interface)
    ↓
├── Mock Data (productsDatabase)
│   └── Returns static JSON
│
└── Live Data
    ├── supabaseClient (Database Queries)
    │   └── Fetches products, historical data
    │
    └── Backend API (Quote Generation)
        └── POST /api/quote
            └── Calculator (Smooth ROI Logic)
                └── Returns live quote
```

### Key Components

1. **`config.js`**
   - Single source of truth for all settings
   - Feature toggle for mock vs. live data
   - Supabase credentials
   - API endpoints

2. **`supabaseClient.js`**
   - Initializes Supabase connection
   - Handles database queries
   - Tests connection on startup

3. **`dataService.js`**
   - Provides unified API for all data operations
   - Automatically switches between mock/live based on config
   - Handles errors gracefully with fallbacks

4. **`script.js`**
   - All UI logic
   - Calls DataService for all data operations
   - Preserves original UI/UX completely

---

## 🐛 Troubleshooting

### Error: "Supabase library not loaded"

**Solution:** Make sure this line is in `index.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

### Error: "Failed to connect to Supabase"

**Solutions:**
1. Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `config.js`
2. Verify Supabase project is active (not paused)
3. Check browser console for CORS errors
4. Ensure you're using the correct Supabase region

### Error: "No product found"

**Solutions:**
1. Check marketplace (US/UK) matches the database
2. Verify ASIN exists in your database
3. Check Supabase RLS (Row Level Security) policies
4. Try with `USE_MOCK_DATA: true` first

### Backend Error: "SUPABASE_URL not found"

**Solution:** Make sure `.env` file exists in project root with:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
```

### Quote Generation Fails

**Solutions:**
1. Check backend is running (`http://localhost:8000/health`)
2. Verify `API_BASE_URL` in `config.js` is correct
3. Check backend logs for errors
4. Ensure product has historical Buy Box data

---

## 📝 API Endpoints

Your backend now provides these endpoints:

### Health Check
```
GET http://localhost:8000/
GET http://localhost:8000/health
```

### Get Catalog
```
GET http://localhost:8000/api/catalog
GET http://localhost:8000/api/catalog?marketplace=US
GET http://localhost:8000/api/catalog?marketplace=UK
GET http://localhost:8000/api/catalog?search=Harry
```

### Generate Quote
```
POST http://localhost:8000/api/quote
Content-Type: application/json

{
    "asin": "143914995X",
    "marketplace": "US",
    "m": 0.10,
    "fx_gbp_to_usd": 1.30
}
```

### Get Statistics
```
GET http://localhost:8000/api/stats
```

---

## 🚢 Deployment

### Frontend Deployment (Netlify/Vercel)

1. Update `config.js` with production backend URL:
```javascript
API_BASE_URL: 'https://your-backend.railway.app'
```

2. Deploy "Front end" folder to Netlify/Vercel

3. Update backend `.env` with frontend URL:
```
CORS_ORIGINS=https://your-app.netlify.app
```

### Backend Deployment (Railway/Render)

1. Push code to GitHub
2. Connect Railway/Render to your repo
3. Set environment variables in dashboard
4. Deploy

---

## ✅ Final Checklist

- [ ] `config.js` updated with Supabase credentials
- [ ] `.env` file created in project root
- [ ] Backend dependencies installed
- [ ] Backend server running on port 8000
- [ ] Frontend served via HTTP (not file://)
- [ ] Browser console shows successful initialization
- [ ] Search works and displays products
- [ ] Quote generation works
- [ ] Market toggle refreshes quote
- [ ] Catalog loads and filters work
- [ ] ROI calculator updates correctly
- [ ] Charts render with data

---

## 🎓 Next Steps

1. **Add Authentication** - Secure the portal with user login
2. **Bulk Quote Export** - Allow users to export quotes to Excel
3. **Price Alerts** - Notify users when margins change
4. **Advanced Analytics** - Add more charts and insights
5. **Mobile Optimization** - Improve responsive design

---

## 📞 Support

If you encounter issues:

1. Check browser console for errors
2. Verify all configuration values
3. Test with `USE_MOCK_DATA: true` first
4. Check backend logs
5. Verify Supabase connection

---

**Built with ❤️ for wholesale book sellers**

**Mode:** Mock Data (Demo) → Live Data (Supabase)  
**Features:** Quote Generation | ROI Calculator | Historical Analytics  
**Architecture:** Vanilla JS | Supabase | FastAPI | PostgreSQL





