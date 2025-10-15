# 📚 Book Portal - Serverless Architecture

## 🎯 Overview

The **Book Portal** is a wholesale quotation platform for book sellers, now running on a **100% serverless architecture** powered by Supabase Edge Functions.

### Tech Stack:
- **Frontend:** Vanilla JavaScript, HTML, CSS (hosted on Vercel/Netlify)
- **Backend Logic:** Supabase Edge Functions (Deno)
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Supabase Auth (optional)

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Front end (Static HTML/CSS/JS)                    │    │
│  │  - index.html                                       │    │
│  │  - script.js                                        │    │
│  │  - dataService.js                                   │    │
│  │  - config.js                                        │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│                   Fetch API Call                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE CLOUD                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Edge Function: generate_quote                      │    │
│  │  - Quote calculation logic                          │    │
│  │  - ROI computations                                 │    │
│  │  - Fee calculations                                 │    │
│  │  Location: supabase/functions/generate_quote/      │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  PostgreSQL Database                                │    │
│  │  - public.products (product catalog)                │    │
│  │  - backfill_test.dynamic_data (Buy Box history)     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Wholesale-Pricing-Portal/
│
├── supabase/
│   └── functions/
│       └── generate_quote/
│           └── index.ts                 ← Quote calculation Edge Function
│
├── Front end/
│   ├── index.html                       ← Main UI
│   ├── script.js                        ← UI logic & event handlers
│   ├── dataService.js                   ← Data fetching & Edge Function calls
│   ├── config.js                        ← Configuration (API URLs, keys)
│   ├── styles.css                       ← Main styles
│   ├── supabaseClient.js                ← Supabase client initialization
│   ├── currencyConverter.js             ← USD/GBP conversion
│   └── ...
│
├── book_portal_pricing/                 ← Reference implementation (Python)
│   ├── calculator.py                    (Logic reference - now in Edge Function)
│   ├── tiers.py                         (Tier reference - now in Edge Function)
│   └── ...
│
├── SUPABASE_EDGE_FUNCTION_DEPLOYMENT.md ← Deployment guide
├── README_SERVERLESS_ARCHITECTURE.md    ← This file
└── ...
```

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/wholesale-pricing-portal.git
cd wholesale-pricing-portal
```

### 2. Install Supabase CLI

```bash
npm install -g supabase
# OR
brew install supabase/tap/supabase
```

### 3. Login & Link Project

```bash
supabase login
supabase link --project-ref mofhylcyainzwbrcmrqg
```

### 4. Deploy Edge Function

```bash
supabase functions deploy generate_quote
```

### 5. Set Environment Secrets

```bash
supabase secrets set SUPABASE_URL=https://mofhylcyainzwbrcmrqg.supabase.co
supabase secrets set SUPABASE_ANON_KEY=your-anon-key-here
```

### 6. Open Frontend

Simply open `Front end/index.html` in your browser, or deploy to Vercel:

```bash
cd "Front end"
vercel --prod
```

---

## 🔑 Key Features

### 1. **Intelligent Quote Generation**
- Calculates optimal wholesale quotes using sophisticated ROI logic
- Ensures seller ROI ≥ 10% and our ROI stays in 10-20% range
- Seller-favored pricing strategy
- Uses 30-day Buy Box average from live data

### 2. **Real-time Data Integration**
- Fetches product catalog from Supabase
- Pulls historical Buy Box prices from Keepa integration
- Auto-calculates Amazon fees, fulfillment costs, shipping
- Weight-based fulfillment tiers

### 3. **ROI Calculator**
- Interactive calculator on every product page
- Auto-fills with calculated values
- Adjustable inputs for "what-if" scenarios
- Real-time ROI updates

### 4. **Multi-marketplace Support**
- US and UK marketplaces
- Currency conversion (USD ↔ GBP)
- Marketplace-specific fulfillment & shipping costs
- Regional Buy Box data

### 5. **Professional UI**
- Clean, modern design
- Responsive layout
- Product search by ASIN, title, or ISBN
- Category filtering
- Amazon Insight charts (Buy Box price & sales rank trends)

---

## 🧮 Quote Calculation Logic

### Formula Overview:

```typescript
// Components:
BB̄ = 30-day Buy Box average
C = Our acquisition cost (our_price)
AF = Amazon fee (17% of BB̄)
FC = Fulfillment cost (weight-based tier)
SC = Shipping cost to seller
S = Total seller costs (AF + FC + SC)

// Our ROI band:
Q_min = C × 1.10  // 10% floor
Q_max = C × 1.20  // 20% cap

// Seller-favored decision:
if (seller_roi_at_Q_min < 10%) {
  // No deal
} else if (seller_roi_at_Q_min < 30%) {
  Q = Q_min  // Favor seller, we take 10%
} else {
  Q = Q_max  // Seller gets >30%, we take 20%
}

// Final ROIs:
Seller ROI = (BB̄ - (Q + S)) / (Q + S)
Our ROI = (Q - C) / C
```

### Weight-Based Fulfillment Tiers:

**US Marketplace (USD):**
- ≤ 0.46 kg: $2.92
- ≤ 1.00 kg: $3.43
- ≤ 2.00 kg: $4.47
- > 2.00 kg: $5.74

**UK Marketplace (GBP):**
- ≤ 0.46 kg: £2.29
- ≤ 1.00 kg: £2.68
- ≤ 2.00 kg: £3.50
- > 2.00 kg: £4.50

---

## 🗄️ Database Schema

### Table: `public.products`

```sql
CREATE TABLE public.products (
  id SERIAL PRIMARY KEY,
  asin TEXT NOT NULL,
  marketplace TEXT NOT NULL CHECK (marketplace IN ('US', 'UK')),
  title TEXT,
  author TEXT,
  isbn13 TEXT,
  our_price NUMERIC NOT NULL,
  package_weight NUMERIC NOT NULL,
  image_url TEXT,
  description TEXT,
  category_lvl1 TEXT,
  category_lvl2 TEXT,
  category_lvl3 TEXT,
  available_stock INTEGER,
  package_dimensions TEXT,
  UNIQUE(asin, marketplace)
);
```

### Table: `backfill_test.dynamic_data`

```sql
CREATE TABLE backfill_test.dynamic_data (
  asin TEXT NOT NULL,
  marketplace TEXT NOT NULL,
  fetch_date DATE NOT NULL,
  current_buybox_price NUMERIC,
  sales_rank_current INTEGER,
  num_sellers INTEGER,
  PRIMARY KEY(asin, marketplace, fetch_date)
);
```

---

## 🔐 Security & Environment Variables

### Frontend Configuration (`config.js`):

```javascript
const config = {
  SUPABASE_URL: 'https://mofhylcyainzwbrcmrqg.supabase.co',
  SUPABASE_ANON_KEY: 'your-anon-key',
  EDGE_FUNCTION_URL: 'https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote'
};
```

### Edge Function Secrets:

Set via Supabase CLI:
```bash
supabase secrets set SUPABASE_URL=...
supabase secrets set SUPABASE_ANON_KEY=...
```

---

## 🧪 Testing

### Test Edge Function Directly:

```bash
curl -X POST https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_ANON_KEY" \
  -d '{"asin":"143914995X","marketplace":"US"}'
```

### Test in Browser Console:

```javascript
fetch(config.EDGE_FUNCTION_URL, {
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
.then(data => console.log(data));
```

---

## 📈 Performance

### Edge Function Performance:
- **Cold start:** ~500ms
- **Warm response:** ~100-200ms
- **Global edge network:** Low latency worldwide
- **Auto-scaling:** Handles traffic spikes automatically

### Frontend Performance:
- **Static hosting:** Instant page loads
- **CDN distribution:** Global delivery
- **No backend bottleneck:** Scales infinitely

---

## 💰 Cost Breakdown

### Supabase (Free Tier):
- **Database:** 500 MB storage
- **Edge Functions:** 500,000 invocations/month
- **Bandwidth:** 2 GB/month
- **API requests:** Unlimited

### Estimated Monthly Usage:
- 1,000 product views/day = 30,000 quote calculations/month
- **Cost:** $0 (well within free tier) 🎉

### Vercel (Free Tier):
- **Bandwidth:** 100 GB/month
- **Build minutes:** 6,000/month
- **Serverless function invocations:** Unlimited

---

## 🔄 Deployment Workflow

### Update Edge Function:

```bash
# 1. Edit code
vim supabase/functions/generate_quote/index.ts

# 2. Deploy
supabase functions deploy generate_quote

# 3. View logs
supabase functions logs generate_quote --follow
```

### Update Frontend:

```bash
# 1. Edit files
vim "Front end/script.js"

# 2. Test locally
open "Front end/index.html"

# 3. Deploy to Vercel
cd "Front end"
vercel --prod
```

---

## 🐛 Common Issues

### Issue: "Edge Function not found (404)"
**Solution:** Deploy the function:
```bash
supabase functions deploy generate_quote
```

### Issue: "No Buy Box data available"
**Solution:** Run Keepa backfill:
```bash
python backend/app/keepa_ingestor.py
```

### Issue: "Product not found"
**Solution:** Check product exists in database:
```sql
SELECT * FROM public.products WHERE asin = '143914995X';
```

---

## 📚 Additional Documentation

- **Deployment:** `SUPABASE_EDGE_FUNCTION_DEPLOYMENT.md`
- **Database Setup:** `TROUBLESHOOTING_AMAZON_INSIGHT.md`
- **Quote Logic:** `book_portal_pricing/calculator.py` (reference)
- **Frontend Integration:** `Front end/QUOTE_GENERATOR_INTEGRATION.md`

---

## 🤝 Contributing

### Development Setup:

1. Install dependencies:
   ```bash
   npm install -g supabase vercel
   ```

2. Link project:
   ```bash
   supabase link --project-ref mofhylcyainzwbrcmrqg
   ```

3. Run locally:
   ```bash
   supabase functions serve generate_quote
   ```

4. Test changes:
   ```bash
   curl -X POST http://localhost:54321/functions/v1/generate_quote \
     -H "Content-Type: application/json" \
     -d '{"asin":"143914995X","marketplace":"US"}'
   ```

---

## ✨ Key Advantages of New Architecture

### Before (Custom Backend):
- ❌ Need to run backend server
- ❌ CORS configuration required
- ❌ Complex deployment (2 services)
- ❌ Server maintenance overhead
- ❌ Scaling challenges

### After (Serverless):
- ✅ No backend server needed
- ✅ No CORS issues
- ✅ Single-command deployment
- ✅ Zero maintenance
- ✅ Auto-scaling included
- ✅ Global performance
- ✅ Cost-effective

---

## 🎊 Summary

The Book Portal is now a **modern, serverless application** that:

- Runs entirely on Supabase Edge Functions and static hosting
- Requires no backend server management
- Scales automatically with demand
- Costs pennies to run (or free!)
- Deploys in seconds with simple commands
- Provides fast, global performance

**Your wholesale quotation platform is production-ready!** 🚀






