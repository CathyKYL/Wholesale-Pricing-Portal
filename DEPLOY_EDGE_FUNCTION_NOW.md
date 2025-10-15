# 🚀 Deploy Your Edge Function Now

## ❌ Current Issue

Your website shows this error:
```
Access to fetch at 'https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote' 
from origin 'null' has been blocked by CORS policy
```

**Why?** The Edge Function hasn't been deployed yet!

---

## ✅ Solution: Deploy in 3 Steps

### Step 1: Install Supabase CLI

**Option A - Using npm (Recommended):**
```bash
npm install -g supabase
```

**Option B - Using Scoop (Windows):**
```bash
scoop install supabase
```

**Verify installation:**
```bash
supabase --version
```

### Step 2: Login & Link Project

```bash
# Login to Supabase
supabase login

# Link your project
supabase link --project-ref mofhylcyainzwbrcmrqg
```

### Step 3: Deploy Edge Function

**Easy Way - Use the batch file:**
```bash
deploy-edge-function.bat
```

**Manual Way:**
```bash
supabase functions deploy generate_quote --project-ref mofhylcyainzwbrcmrqg
```

---

## ✅ Verify Deployment

After deployment, you should see:
```
Function URL: https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote
Completed deploy 1/1
```

### Test in Browser:

1. Open `Front end/index.html`
2. Search for a product (e.g., ASIN: 143914995X)
3. Click on the product
4. You should see "Calculating..." then the quote!

### Check Console:

Press F12 and look for:
```
[DataService] 📊 Generating quote...
[DataService] ✅ Quote generated successfully!
[DataService]    Quote Price: $17.90
```

---

## 🔧 Set Environment Secrets (After First Deploy)

```bash
supabase secrets set SUPABASE_URL=https://mofhylcyainzwbrcmrqg.supabase.co
supabase secrets set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZmh5bGN5YWluendicmNtcnFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNDg1MTQsImV4cCI6MjA3NTkyNDUxNH0.TeaalZbVrSkqAszpZxPDSJUdoXL0wsg9veDhS1v8Bj0
```

---

## 🐛 Troubleshooting

### Error: "Supabase CLI not found"

**Solution:** Install Supabase CLI
```bash
npm install -g supabase
```

### Error: "Not logged in"

**Solution:** Login first
```bash
supabase login
```

### Error: "Project not linked"

**Solution:** Link project
```bash
supabase link --project-ref mofhylcyainzwbrcmrqg
```

### Error: "Function already exists"

**Solution:** That's fine! It will update it
```bash
supabase functions deploy generate_quote --project-ref mofhylcyainzwbrcmrqg
```

---

## 📊 View Logs (Optional)

```bash
# View real-time logs
supabase functions logs generate_quote --follow

# View last 100 log entries
supabase functions logs generate_quote --limit 100
```

---

## ✨ What Changed?

I updated the Edge Function with **improved CORS headers**:

```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',                    // Allow any origin
  'Access-Control-Allow-Headers': '...',                 // All needed headers
  'Access-Control-Allow-Methods': 'POST, OPTIONS',       // Allowed methods
  'Access-Control-Max-Age': '86400',                     // Cache preflight
};
```

And proper OPTIONS handling:
```typescript
if (req.method === 'OPTIONS') {
  return new Response(null, { 
    status: 204,                // Proper status code
    headers: corsHeaders 
  });
}
```

---

## 🎯 Quick Deploy Commands

**All in one:**
```bash
npm install -g supabase
supabase login
supabase link --project-ref mofhylcyainzwbrcmrqg
supabase functions deploy generate_quote
```

**Or just use the batch file:**
```bash
deploy-edge-function.bat
```

---

## ✅ After Deployment

Your console should show:
```
✅ [DataService] Quote generated successfully!
✅ Quote Price: $17.90
✅ Seller ROI: 25.50%
✅ Our ROI: 15.00%
```

Instead of:
```
❌ Cannot connect to Supabase Edge Function
⚠️ Using fallback quote (Edge Function unavailable)
```

---

**Deploy now and your quote generator will work!** 🚀





