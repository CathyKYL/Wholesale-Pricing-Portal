# 🚀 Cloud Deployment Guide - Wholesale Pricing Portal

This guide shows you how to deploy your Wholesale Pricing Portal from local development to cloud production.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Local Development Setup](#local-development-setup)
3. [Cloud Deployment Options](#cloud-deployment-options)
4. [Railway Deployment (Recommended)](#railway-deployment-recommended)
5. [Netlify Frontend Deployment](#netlify-frontend-deployment)
6. [Environment Variables Reference](#environment-variables-reference)
7. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### Production Stack
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Frontend (Netlify)                                         │
│  - Static website hosting                                   │
│  - React/Vue/Angular/HTML                                   │
│  - Makes API calls to backend                               │
│                                                             │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTPS
                 │ (CORS enabled)
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Backend API (Railway/Render/Heroku)                        │
│  - FastAPI application                                      │
│  - Serves REST API endpoints                                │
│  - Handles business logic                                   │
│                                                             │
└────────────────┬────────────────────────────────────────────┘
                 │ PostgreSQL
                 │ protocol
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Database (Railway Postgres/Supabase/AWS RDS)               │
│  - PostgreSQL database                                      │
│  - Stores catalog data                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Local Development Setup

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-username/Wholesale-Pricing-Portal.git
cd Wholesale-Pricing-Portal

# Install Python dependencies
pip install -r requirements.txt

# Create .env file from template
cp env.template .env
```

### 2. Configure .env File

Edit `.env` and set your local values:

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/wholesale_portal
KEEPA_API_KEY=your_keepa_api_key
EXCEL_PATH=Data.xlsx
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. Run Database Setup

```bash
# Navigate to backend/app
cd backend/app

# Run smoke test (creates tables and loads data)
python smoke_test.py
```

### 4. Start Development Server

```bash
# From backend/app directory
uvicorn main:app --reload --port 8000

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

---

## ☁️ Cloud Deployment Options

| Platform | Backend | Database | Difficulty | Free Tier | Notes |
|----------|---------|----------|------------|-----------|-------|
| **Railway** | ✅ Yes | ✅ Included | ⭐ Easy | ✅ $5/month credit | **Recommended** |
| **Render** | ✅ Yes | ✅ Included | ⭐ Easy | ✅ Yes | Good alternative |
| **Heroku** | ✅ Yes | ✅ Add-on | ⭐⭐ Medium | ❌ Paid only | Classic choice |
| **Supabase + Vercel** | ⚠️ Serverless | ✅ Yes | ⭐⭐⭐ Hard | ✅ Yes | For advanced users |

---

## 🚂 Railway Deployment (Recommended)

Railway is the easiest platform for deploying Python + PostgreSQL applications.

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Create a new project

### Step 2: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway automatically creates the database
4. The `DATABASE_URL` environment variable is auto-provided

### Step 3: Deploy Backend

#### Option A: Deploy from GitHub (Recommended)

1. Push your code to GitHub
2. In Railway, click **"+ New"** → **"GitHub Repo"**
3. Select your repository
4. Railway will auto-detect it's a Python project

#### Option B: Deploy from CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy
railway up
```

### Step 4: Configure Environment Variables

In Railway dashboard, go to **Variables** and add:

```env
ENVIRONMENT=production
KEEPA_API_KEY=your_keepa_api_key_here
FRONTEND_URL=https://your-app.netlify.app
SECRET_KEY=generate_random_string_here
CORS_ORIGINS=https://your-app.netlify.app
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Set Python Start Command

In Railway settings, set **Custom Start Command:**

```bash
cd backend/app && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Step 6: Initialize Database

After deployment, open Railway's terminal and run:

```bash
cd backend/app
python smoke_test.py
```

This creates tables and loads initial data.

### Step 7: Get Your API URL

Railway provides a public URL like: `https://your-app.railway.app`

Test it: `https://your-app.railway.app/health`

---

## 🌐 Netlify Frontend Deployment

### Step 1: Build Your Frontend

Create a simple frontend or use existing React/Vue/Angular app:

**Example: Simple HTML Frontend**

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Wholesale Pricing Portal</title>
</head>
<body>
    <h1>Wholesale Pricing Portal</h1>
    <div id="catalog"></div>
    
    <script>
        // Replace with your Railway API URL
        const API_URL = 'https://your-app.railway.app';
        
        async function loadCatalog() {
            const response = await fetch(`${API_URL}/api/catalog`);
            const data = await response.json();
            
            const catalogDiv = document.getElementById('catalog');
            data.forEach(item => {
                catalogDiv.innerHTML += `
                    <div>
                        <h3>${item.title}</h3>
                        <p>Author: ${item.author}</p>
                        <p>Price: £${item.our_price}</p>
                    </div>
                `;
            });
        }
        
        loadCatalog();
    </script>
</body>
</html>
```

### Step 2: Deploy to Netlify

#### Option A: Drag & Drop
1. Go to [netlify.com](https://netlify.com)
2. Drag your `index.html` file into the deploy area
3. Done!

#### Option B: Git Integration
1. Push frontend code to GitHub
2. In Netlify, click **"New site from Git"**
3. Select your repository
4. Configure build settings
5. Deploy

### Step 3: Configure Frontend Environment

In your frontend code, use your Railway API URL:

```javascript
// For React/Vue/Angular
const API_URL = import.meta.env.VITE_API_URL || 'https://your-app.railway.app';

// Or set in Netlify environment variables
// Site settings → Environment variables → Add variable
// VITE_API_URL = https://your-app.railway.app
```

### Step 4: Update Backend CORS

Make sure your Railway backend has the Netlify URL in CORS_ORIGINS:

```env
CORS_ORIGINS=https://your-app.netlify.app
FRONTEND_URL=https://your-app.netlify.app
```

---

## 📝 Environment Variables Reference

### Required Variables

| Variable | Local Example | Cloud Example | Description |
|----------|---------------|---------------|-------------|
| `DATABASE_URL` | `postgresql://postgres:pass@localhost:5432/wholesale_portal` | Auto-provided by Railway | PostgreSQL connection string |
| `KEEPA_API_KEY` | `your_key_here` | `your_key_here` | Keepa API key |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development`, `staging`, or `production` |
| `CORS_ORIGINS` | Local ports | Comma-separated allowed origins |
| `FRONTEND_URL` | None | Your Netlify domain |
| `SECRET_KEY` | Dev key | Random string for production |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `EXCEL_PATH` | `Data.xlsx` | Path or URL to Excel file |

---

## 🔧 Troubleshooting

### Problem: "CORS Error" in Browser Console

**Cause:** Frontend can't connect to backend due to CORS restrictions.

**Solution:**
```env
# In Railway, add your Netlify URL:
CORS_ORIGINS=https://your-app.netlify.app
FRONTEND_URL=https://your-app.netlify.app
```

### Problem: "Database connection failed"

**Cause:** DATABASE_URL is incorrect or database isn't running.

**Solution:**
1. Check Railway database is running
2. Verify DATABASE_URL is auto-set
3. Check database logs in Railway

### Problem: "Module not found" errors

**Cause:** Dependencies not installed.

**Solution:**
```bash
# Make sure requirements.txt includes all packages
pip freeze > requirements.txt

# Railway automatically installs from requirements.txt
```

### Problem: Can't access /docs or /redoc

**Cause:** FastAPI docs might be disabled in production.

**Solution:** Docs are enabled. Access at:
- Swagger UI: `https://your-app.railway.app/docs`
- ReDoc: `https://your-app.railway.app/redoc`

### Problem: "Excel file not found" in cloud

**Cause:** Local file path doesn't exist in cloud.

**Solution:** Either:
1. Include Data.xlsx in your git repo
2. Upload to cloud storage (S3, Google Cloud Storage)
3. Create an API endpoint for file upload

---

## ✅ Deployment Checklist

### Before Deploying

- [ ] All sensitive data in environment variables (not hardcoded)
- [ ] `.env` file in `.gitignore`
- [ ] `requirements.txt` is up to date
- [ ] Code tested locally with `python smoke_test.py`
- [ ] Database schema finalized

### After Deploying Backend

- [ ] Database initialized (`python smoke_test.py`)
- [ ] Health check returns 200: `/health`
- [ ] API docs accessible: `/docs`
- [ ] Test endpoint: `/api/catalog`

### After Deploying Frontend

- [ ] Frontend can reach backend API
- [ ] No CORS errors in browser console
- [ ] Data displays correctly
- [ ] All features working

---

## 🎯 Next Steps

1. **Add Authentication**
   - Implement JWT tokens
   - Protect admin endpoints
   - Add user management

2. **Enhance API**
   - Add filtering and sorting
   - Implement caching
   - Add rate limiting

3. **Monitoring**
   - Set up error tracking (Sentry)
   - Add logging (LogDNA, Papertrail)
   - Monitor performance

4. **CI/CD**
   - Set up automated testing
   - Deploy on git push
   - Add staging environment

---

## 🆘 Need Help?

- **Railway Docs:** https://docs.railway.app
- **Netlify Docs:** https://docs.netlify.com
- **FastAPI Docs:** https://fastapi.tiangolo.com

---

**Your application is now cloud-ready! 🚀**

The same code runs locally and in production without any changes.
Just configure environment variables and deploy!

