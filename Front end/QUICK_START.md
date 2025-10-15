# 🚀 Quick Start Guide - Book Portal Integration

## ⚡ 5-Minute Setup

### Option 1: Demo Mode (Easiest)

Just open `index.html` in your browser. Done! ✅

---

### Option 2: Live Data Mode

#### Step 1: Configure Frontend (2 minutes)

Edit `Front end/config.js`:

```javascript
USE_MOCK_DATA: false,  // Switch to live data
SUPABASE_URL: 'https://YOUR-PROJECT.supabase.co',  // ← Your URL
SUPABASE_ANON_KEY: 'eyJ...',  // ← Your key
```

Get these from: **Supabase Dashboard → Settings → API**

---

#### Step 2: Configure Backend (2 minutes)

Create `.env` file in **project root**:

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_KEY=your-key-here
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
SECRET_KEY=any-random-string
LOG_LEVEL=INFO
```

**Tip:** Copy from `BACKEND_ENV_TEMPLATE.txt` and fill in your values.

---

#### Step 3: Start Backend (1 minute)

```bash
cd backend/app
python main.py
```

Should see: `Uvicorn running on http://127.0.0.1:8000` ✅

---

#### Step 4: Start Frontend (1 minute)

```bash
cd "Front end"
python -m http.server 5500
```

Open: `http://localhost:5500` ✅

---

## ✅ Verify It's Working

1. **Open browser console** (`F12`)
2. Should see:
   ```
   ✅ Book Portal initialized successfully
   📦 Mode: LIVE DATA (Supabase)
   📊 Loaded 38 products
   ```

3. **Search for a product:**
   - Enter ASIN: `143914995X`
   - Click Search
   - Quote should generate

4. **Toggle markets:**
   - Switch US/UK toggle
   - Quote should regenerate

---

## 🐛 Troubleshooting

**"Connection Error"**
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `config.js`
- Verify backend is running: `http://localhost:8000/health`

**"No products found"**
- Check database has products
- Verify marketplace (US/UK) exists in database

**CORS Error**
- Add your frontend URL to `.env` file's `CORS_ORIGINS`

---

## 📚 Full Documentation

See `INTEGRATION_GUIDE.md` for complete setup instructions.

---

**Need Help?** Check browser console for detailed error messages.





