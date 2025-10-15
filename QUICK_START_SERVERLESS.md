# ⚡ Quick Start - Serverless Book Portal

## 🎯 3-Step Deployment

### Step 1: Install Supabase CLI
```bash
npm install -g supabase
```

### Step 2: Deploy Edge Function
```bash
supabase login
supabase link --project-ref mofhylcyainzwbrcmrqg
supabase functions deploy generate_quote
```

### Step 3: Set Secrets
```bash
supabase secrets set SUPABASE_URL=https://mofhylcyainzwbrcmrqg.supabase.co
supabase secrets set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZmh5bGN5YWluendicmNtcnFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNDg1MTQsImV4cCI6MjA3NTkyNDUxNH0.TeaalZbVrSkqAszpZxPDSJUdoXL0wsg9veDhS1v8Bj0
```

## ✅ Test It!

Open `Front end/index.html` and search for a product. Done! 🎉

---

## 📚 Full Documentation

- **Complete Guide:** `SUPABASE_EDGE_FUNCTION_DEPLOYMENT.md`
- **Architecture:** `README_SERVERLESS_ARCHITECTURE.md`
- **Migration Details:** `MIGRATION_TO_SERVERLESS_COMPLETE.md`

---

## 🔄 Common Commands

```bash
# Deploy changes
supabase functions deploy generate_quote

# View logs
supabase functions logs generate_quote --follow

# Test locally
supabase functions serve generate_quote

# Deploy frontend to Vercel
cd "Front end"
vercel --prod
```

---

## 💡 What Changed?

**Before:** FastAPI backend (localhost:8000) ❌  
**After:** Supabase Edge Function ✅

**Benefits:**
- No backend server to run
- No uvicorn errors
- Auto-scaling
- Global performance
- Free tier: 500k invocations/month

---

**Ready to go! 🚀**





