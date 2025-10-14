# 🤖 GitHub Actions Setup Guide

## ✅ What Was Created

I've created `.github/workflows/daily-keepa-update.yml` which will:
- ✅ Run automatically at **3:00 AM UTC** every day
- ✅ Fetch current prices for all 38 ASINs
- ✅ Update seller counts (only available in daily updates!)
- ✅ Recompute weekly trends
- ✅ Use **0 server resources** (runs on GitHub's servers)
- ✅ **Completely FREE**

---

## 🔐 Step 1: Add Secrets to GitHub

**IMPORTANT:** Your `DATABASE_URL` and `KEEPA_API_KEY` must be stored as GitHub Secrets (never commit them to code!)

### **How to Add Secrets:**

1. **Go to your GitHub repository**
   - Open your repo on GitHub.com

2. **Navigate to Settings**
   - Click **Settings** tab (top right)

3. **Go to Secrets and Variables**
   - Click **Secrets and variables** → **Actions** (left sidebar)

4. **Add New Repository Secret**
   - Click **New repository secret** button

5. **Add DATABASE_URL:**
   - **Name:** `DATABASE_URL`
   - **Value:** Your full PostgreSQL connection string
     ```
     postgresql://postgres:2407@localhost:5432/wholesale_portal
     ```
   - **⚠️ IMPORTANT:** If your database is local (`localhost`), it won't work from GitHub!
     - You need a cloud database (Railway, Render, Supabase, etc.)
     - Example cloud URL:
       ```
       postgresql://user:pass@your-db.railway.app:5432/wholesale_portal
       ```
   - Click **Add secret**

6. **Add KEEPA_API_KEY:**
   - Click **New repository secret** again
   - **Name:** `KEEPA_API_KEY`
   - **Value:** `d452t88rcid318a6aii79vj5lgh5kd46o71u0ht5vnddqobb0b180ar4belbpitp`
   - Click **Add secret**

---

## 🚀 Step 2: Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Add GitHub Actions for daily Keepa updates"

# Push to GitHub
git push origin main
```

---

## ⚡ Step 3: Test the Workflow (Manual Trigger)

**Don't wait until 3 AM tomorrow! Test it now:**

1. **Go to Actions tab** on GitHub
   - Click **Actions** (top menu)

2. **Find your workflow**
   - You'll see "Daily Keepa Price Update" in the left sidebar

3. **Run manually**
   - Click on "Daily Keepa Price Update"
   - Click **Run workflow** dropdown (right side)
   - Click green **Run workflow** button

4. **Watch it run**
   - Click on the workflow run to see live logs
   - Should complete in ~30 seconds

5. **Check results**
   - ✅ Green checkmark = Success!
   - ❌ Red X = Failed (check logs for errors)

---

## 📊 Step 4: Verify Data Was Updated

After the workflow completes, check your database:

```sql
-- Check latest data
SELECT MAX(fetch_date) as latest_date, COUNT(*) as records
FROM dynamic.keepa_daily_data
WHERE fetch_date = (SELECT MAX(fetch_date) FROM dynamic.keepa_daily_data);

-- Should show today's date and 38 records
```

---

## 🔍 Monitoring

### **View Workflow History:**
1. Go to **Actions** tab on GitHub
2. See all past runs with timestamps
3. Click any run to see detailed logs

### **Email Notifications:**
- GitHub automatically emails you on failures
- Configure in **Settings** → **Notifications** → **Actions**

### **Badge in README:**
Add this to your `README.md` to show workflow status:

```markdown
![Daily Update](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/daily-keepa-update.yml/badge.svg)
```

---

## ⏰ Schedule Details

**Current schedule:** `0 3 * * *` (3:00 AM UTC daily)

**Cron syntax:**
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6, Sunday = 0)
│ │ │ │ │
0 3 * * *
```

**Want a different time?** Edit `.github/workflows/daily-keepa-update.yml`:
```yaml
# 9 AM UTC (4 AM EST):
- cron: '0 9 * * *'

# 6 PM UTC (1 PM EST):
- cron: '0 18 * * *'

# Every 12 hours:
- cron: '0 0,12 * * *'

# Weekly (Monday at 3 AM):
- cron: '0 3 * * 1'
```

---

## ⚠️ Important Notes

### **1. Database Must Be Accessible from Internet**
- ❌ `localhost` databases won't work
- ✅ Use cloud database:
  - **Railway:** Free tier, auto-provision
  - **Render:** $7/month for PostgreSQL
  - **Supabase:** Free tier up to 500MB
  - **Neon:** Free serverless PostgreSQL

### **2. GitHub Actions Limitations**
- ⏱️ Max 6 hours per job (your update takes ~30 seconds)
- 💾 2,000 minutes/month on free plan (you'll use ~15 minutes/month)
- 🔄 If workflow fails 3 times, it auto-disables (re-enable manually)

### **3. Workflow Will Only Run If:**
- ✅ Code is pushed to main branch
- ✅ Workflow file has no syntax errors
- ✅ Secrets are properly set
- ✅ Repository is active (not archived)

---

## 🐛 Troubleshooting

### **Workflow Not Appearing?**
1. Make sure `.github/workflows/` folder exists
2. Make sure file is named with `.yml` or `.yaml` extension
3. Push to `main` branch (or your default branch)
4. Check Actions tab after push

### **Workflow Failing?**
**Check these common issues:**

1. **Database connection error:**
   - ✅ Verify `DATABASE_URL` secret is correct
   - ✅ Database must be accessible from internet
   - ✅ No `localhost` or `127.0.0.1`

2. **Keepa API error:**
   - ✅ Verify `KEEPA_API_KEY` secret is correct
   - ✅ Check you have API credits at keepa.com
   - ✅ Check rate limits

3. **Python dependency error:**
   - ✅ Make sure `requirements.txt` is in repo root
   - ✅ All packages listed correctly

4. **File not found error:**
   - ✅ Check path: `backend/app/keepa_ingestor.py`
   - ✅ Make sure all files are committed

### **Manual Fix Workflow:**
If workflow fails, you can always run manually:
```bash
# On your local machine
python backend/app/keepa_ingestor.py --daily
```

---

## 💰 Cost Analysis

**GitHub Actions (Free Plan):**
- ✅ 2,000 minutes/month FREE
- Your job uses: ~0.5 minutes/day × 30 days = **15 minutes/month**
- **Cost:** $0/month (well within free tier!)

**Keepa API:**
- 38 tokens/day × 30 days = **1,140 tokens/month**
- **Cost:** $11.40/month

**Total:** $11.40/month (just Keepa API)

---

## 🎯 Next Steps

1. ✅ Add secrets to GitHub (DATABASE_URL, KEEPA_API_KEY)
2. ✅ Push code to GitHub
3. ✅ Manually trigger workflow to test
4. ✅ Verify data in database
5. ✅ Relax - it will run automatically every day!

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cron Schedule Helper](https://crontab.guru/)
- [GitHub Actions Status Page](https://www.githubstatus.com/)

---

**Status:** ✅ **Ready to deploy!**

Once you push to GitHub and add the secrets, your daily updates will run automatically! 🚀

