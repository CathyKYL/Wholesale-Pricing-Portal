# 🚀 Supabase Edge Function Deployment Guide

## 🎉 New Serverless Architecture

Your Book Portal now uses **Supabase Edge Functions** instead of a custom FastAPI backend!

### ✅ Benefits:
- **No backend server to maintain** - Fully serverless!
- **No CORS issues** - Edge Functions handle CORS automatically
- **No deployment complexity** - One simple command to deploy
- **Auto-scaling** - Supabase handles all infrastructure
- **Global edge network** - Fast response times worldwide
- **Cost-effective** - Pay only for what you use

---

## 📋 Prerequisites

### 1. Install Supabase CLI

**Windows (PowerShell):**
```powershell
scoop install supabase
```

**macOS:**
```bash
brew install supabase/tap/supabase
```

**Linux:**
```bash
brew install supabase/tap/supabase
```

**Alternative (npm):**
```bash
npm install -g supabase
```

### 2. Login to Supabase

```bash
supabase login
```

This will open your browser and authenticate you with Supabase.

### 3. Link Your Project

```bash
supabase link --project-ref mofhylcyainzwbrcmrqg
```

Your project ref is: `mofhylcyainzwbrcmrqg`

---

## 🚀 Deploy the Edge Function

### Step 1: Navigate to Project Root

```bash
cd "C:\VibeCode\Wholesale Pricing Portal\Wholesale-Pricing-Portal"
```

### Step 2: Deploy the Function

```bash
supabase functions deploy generate_quote
```

You should see output like:
```
Deploying Function... (1/1)
Function URL: https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote
Completed deploy 1/1
```

### Step 3: Set Environment Secrets

The Edge Function needs access to your Supabase credentials:

```bash
supabase secrets set SUPABASE_URL=https://mofhylcyainzwbrcmrqg.supabase.co
supabase secrets set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZmh5bGN5YWluendicmNtcnFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNDg1MTQsImV4cCI6MjA3NTkyNDUxNH0.TeaalZbVrSkqAszpZxPDSJUdoXL0wsg9veDhS1v8Bj0
```

---

## ✅ Verify Deployment

### Test with curl:

```bash
curl -X POST https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote \
  -H "Content-Type: application/json" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZmh5bGN5YWluendicmNtcnFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNDg1MTQsImV4cCI6MjA3NTkyNDUxNH0.TeaalZbVrSkqAszpZxPDSJUdoXL0wsg9veDhS1v8Bj0" \
  -d '{"asin":"143914995X","marketplace":"US"}'
```

**Expected response:**
```json
{
  "feasible": true,
  "quote_q": 17.90,
  "seller_roi_pct": 25.50,
  "our_roi_pct": 15.00,
  "bb_avg": 23.45,
  "af": 3.99,
  "fc": 2.50,
  "sc": 1.30,
  ...
}
```

### Test in Browser Console:

Open your website and run:
```javascript
fetch('https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'apikey': config.SUPABASE_ANON_KEY
  },
  body: JSON.stringify({
    asin: '143914995X',
    marketplace: 'US'
  })
})
.then(r => r.json())
.then(data => console.log('Quote:', data));
```

---

## 🌐 Deploy Frontend to Vercel

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login

```bash
vercel login
```

### Step 3: Deploy

```bash
cd "Front end"
vercel deploy
```

Follow the prompts:
- Set up and deploy? **Y**
- Which scope? Select your account
- Link to existing project? **N** (first time)
- Project name? **wholesale-pricing-portal**
- Directory? **.** (current directory)
- Override settings? **N**

### Step 4: Deploy to Production

```bash
vercel --prod
```

Your website is now live at: `https://wholesale-pricing-portal.vercel.app`

---

## 🎯 What Changed?

### Before (Custom Backend):
```
Frontend → http://127.0.0.1:8000/api/quote → FastAPI → Supabase
```

**Problems:**
- Need to run backend server locally
- CORS configuration required
- Complex deployment (backend + frontend)
- Server maintenance overhead

### After (Edge Functions):
```
Frontend → Supabase Edge Function → Supabase Database
```

**Benefits:**
- No local backend needed
- No CORS issues
- Simple deployment
- Auto-scaling
- Global edge network

---

## 📁 Updated File Structure

```
Wholesale-Pricing-Portal/
│
├── supabase/
│   └── functions/
│       └── generate_quote/
│           └── index.ts            ← ✨ NEW: Edge Function
│
├── Front end/
│   ├── index.html
│   ├── script.js
│   ├── dataService.js              ← ✅ Updated: Calls Edge Function
│   ├── config.js                   ← ✅ Updated: Edge Function URL
│   ├── styles.css
│   └── ...
│
├── backend/                         ← ⚠️ DEPRECATED (can be removed)
│   └── app/
│       └── main.py                  (No longer needed)
│
└── book_portal_pricing/             ← ℹ️ Reference only
    └── calculator.py                (Logic moved to Edge Function)
```

---

## 🔧 Maintenance & Updates

### Update Edge Function Code

1. Edit `supabase/functions/generate_quote/index.ts`
2. Deploy changes:
   ```bash
   supabase functions deploy generate_quote
   ```

### View Edge Function Logs

```bash
supabase functions logs generate_quote --follow
```

### Test Locally (Optional)

```bash
supabase functions serve generate_quote
```

Then test at: `http://localhost:54321/functions/v1/generate_quote`

---

## 🐛 Troubleshooting

### Edge Function Returns 404

**Cause:** Function not deployed or wrong URL

**Solution:**
```bash
supabase functions deploy generate_quote
```

Check the URL matches in `config.js`.

### Edge Function Returns 401 Unauthorized

**Cause:** Missing or invalid API key

**Solution:**
Ensure you're sending the `apikey` header:
```javascript
headers: {
  'apikey': config.SUPABASE_ANON_KEY,
  'Authorization': `Bearer ${config.SUPABASE_ANON_KEY}`
}
```

### Edge Function Returns 500 Internal Error

**Cause:** Missing environment secrets or database error

**Solution:**
1. Check secrets are set:
   ```bash
   supabase secrets list
   ```

2. View logs for details:
   ```bash
   supabase functions logs generate_quote
   ```

3. Verify database access:
   - Ensure `backfill_test.dynamic_data` table exists
   - Check RLS policies allow access

### "No Buy Box data available"

**Cause:** Product doesn't have historical data

**Solution:**
- Run Keepa backfill to populate data
- Check product exists in `backfill_test.dynamic_data`
- Verify ASIN and marketplace match exactly

---

## 📊 Monitoring

### View Function Analytics

1. Go to: https://supabase.com/dashboard/project/mofhylcyainzwbrcmrqg
2. Navigate to: **Edge Functions** → **generate_quote**
3. View:
   - Invocation count
   - Response times
   - Error rates
   - Logs

---

## 💰 Cost Considerations

### Supabase Edge Functions Pricing:

- **Free tier:** 500,000 invocations/month
- **After free tier:** $2 per 1 million invocations

### Example Usage:

- 10 products viewed/day = 300 invocations/month
- 100 products viewed/day = 3,000 invocations/month
- 1,000 products viewed/day = 30,000 invocations/month

**All well within free tier!** 🎉

---

## 🚀 Next Steps

### 1. Deploy Edge Function

```bash
supabase functions deploy generate_quote
```

### 2. Test in Browser

Open `Front end/index.html` and search for a product. Watch the console for:
```
[DataService] 📊 Generating quote...
[DataService] ✅ Quote generated successfully!
```

### 3. Deploy Frontend to Vercel

```bash
cd "Front end"
vercel --prod
```

### 4. Remove Old Backend (Optional)

Once everything works, you can safely delete:
- `backend/` folder
- `START_BACKEND_API.bat`
- Old API documentation

---

## ✨ Summary

You've successfully migrated from a custom FastAPI backend to Supabase Edge Functions!

**What you gained:**
- ✅ No backend server to run
- ✅ No CORS issues
- ✅ Simple deployment
- ✅ Auto-scaling
- ✅ Cost-effective
- ✅ Global performance

**What to remember:**
- Deploy changes: `supabase functions deploy generate_quote`
- View logs: `supabase functions logs generate_quote`
- Frontend is ready to deploy to Vercel/Netlify

**Your Book Portal is now 100% serverless!** 🎊






