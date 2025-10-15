# 🔄 Daily Scheduler Setup Guide

## ⚠️ Important: Daily Data Collection Limitation

**Keepa API Limitation:**
- Daily mode fetches CURRENT snapshot only
- Cannot retroactively fetch past daily snapshots
- Seller counts are ONLY available in current data
- Historical backfill does NOT include seller counts

**What This Means:**
- ✅ Oct 14, 2025: We have seller counts (just fetched)
- ❌ Oct 13, 2025: Only price/rank from backfill, NO seller counts
- ✅ Going forward: Scheduler will capture daily seller counts

---

## 🚀 Starting the Automated Scheduler

### **Method 1: Windows Task Scheduler (Recommended for Production)**

**Create a scheduled task that runs daily:**

1. **Open Task Scheduler** (Windows + R, type `taskschd.msc`)

2. **Create Basic Task:**
   - Name: `Keepa Daily Update`
   - Trigger: Daily at 03:00 AM
   - Action: Start a program
   
3. **Program Settings:**
   - Program: `C:\VibeCode\Wholesale Pricing Portal\Wholesale-Pricing-Portal\venv\Scripts\python.exe`
   - Arguments: `keepa_ingestor.py --daily`
   - Start in: `C:\VibeCode\Wholesale Pricing Portal\Wholesale-Pricing-Portal\backend\app`

4. **Advanced Settings:**
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges
   - ✅ If task fails, restart every 15 minutes (up to 3 times)

**Logs:**
- Output will be logged by Windows Task Scheduler
- Check Task History for execution status

---

### **Method 2: Python Scheduler (Simple, requires terminal open)**

**Start the scheduler now:**
```bash
python keepa_ingestor.py --schedule
```

**What it does:**
- Runs continuously in the terminal
- Updates at 03:00 every day
- Prints status messages
- Press `Ctrl+C` to stop

**Pros:**
- Simple to start
- See real-time output

**Cons:**
- Terminal must stay open
- Stops if you close terminal or restart PC

---

### **Method 3: Windows Service (Advanced)**

**Convert to a Windows Service using NSSM:**

1. Download NSSM (Non-Sucking Service Manager)
2. Install as service:
   ```bash
   nssm install KeepaScheduler "C:\...\venv\Scripts\python.exe" "keepa_ingestor.py --schedule"
   ```
3. Service will run in background always

---

## 📊 What Gets Updated Daily

**Every day at 03:00:**
1. Fetches current data for all 38 ASINs
2. Updates BuyBox prices
3. Updates sales ranks
4. **Captures seller counts** (critical!)
5. Recomputes weekly trends
6. Logs API calls

**Cost:** ~38 tokens/day = $0.38/day = $11.40/month

---

## ✅ Verification

**Check if scheduler is working:**

**After first run (tomorrow at 03:00), check:**
```bash
python -c "from sqlalchemy import create_engine, text; from dotenv import load_dotenv; import os; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); result = conn.execute(text('SELECT MAX(fetch_date) as latest, COUNT(*) as count FROM dynamic.keepa_daily_data WHERE fetch_date = (SELECT MAX(fetch_date) FROM dynamic.keepa_daily_data)')).fetchone(); print(f'Latest data: {result[0]}, Records: {result[1]}'); conn.close()"
```

Expected output:
```
Latest data: 2025-10-15, Records: 38
```

---

## 🛑 Stopping the Scheduler

**Method 1 (Python Scheduler):**
- Press `Ctrl+C` in the terminal

**Method 2 (Task Scheduler):**
- Open Task Scheduler
- Find "Keepa Daily Update"
- Right-click → Disable/Delete

**Method 3 (Windows Service):**
```bash
nssm stop KeepaScheduler
```

---

## 📝 Monitoring

**Check daily data collection:**
```sql
SELECT fetch_date, COUNT(*) as records, COUNT(num_sellers) as with_sellers
FROM dynamic.keepa_daily_data
WHERE fetch_date >= CURRENT_DATE - 7
GROUP BY fetch_date
ORDER BY fetch_date DESC;
```

Should show:
- 38 records per day
- 36+ with seller counts per day

---

## 🔧 Troubleshooting

**Scheduler not running:**
1. Check Python path is correct
2. Check working directory is correct
3. Check .env file is accessible
4. Check database connectivity
5. Check Keepa API key is valid

**Missing seller counts:**
- Normal for ~2 ASINs per day (no current data)
- If all missing, check API response

**API errors:**
- Check token balance at keepa.com
- Check API key is active
- Check rate limits (1 request per second)

---

## 💰 Cost Optimization

**Reduce costs by updating less frequently:**

**Weekly updates:** ~$1.52/month (vs $11.40)
```python
# In keepa_ingestor.py, change schedule line:
schedule.every().monday.at("03:00").do(daily_update_job)
```

**Bi-weekly:** ~$0.76/month
```python
# Run every 2 weeks
schedule.every(14).days.at("03:00").do(daily_update_job)
```

---

**Status:** Ready to start! Choose your preferred method above. 🚀





