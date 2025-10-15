# 📊 Excel Reports Guide - Book Portal Quote Calculator

## ✅ Files Generated

I've created **two Excel files** for you to review all the logic, variables, and calculations:

### 1. `Book_Portal_Quote_Report.xlsx` - **MAIN REPORT** (37 products × 2 marketplaces = 74 quotes)

**Location:** Project root  
**Size:** 15 KB  
**Products:** All 37 items from your database  
**Marketplaces:** UK and US  
**Created:** October 14, 2025

### 2. `Quote_Calculator_UK_Example.xlsx` - **SINGLE EXAMPLE**

**Location:** Project root  
**Size:** 5.8 KB  
**Purpose:** Shows one complete example calculation (UK marketplace)

---

## 📚 Main Report Structure (`Book_Portal_Quote_Report.xlsx`)

### Sheet 1: "Quote Summary" - **INTERACTIVE** ✨

This sheet lets you **select any product and marketplace** using dropdown menus to see all calculations.

#### How to Use:

1. **Open the file in Excel**
2. **Cell B3** - Click dropdown to select any ASIN (37 products available)
3. **Cell B4** - Click dropdown to select marketplace (UK or US)
4. **Watch the calculations update automatically!**

#### What You'll See:

```
┌─────────────────────────────────────────────────┐
│ Book Portal Quote Calculator - Interactive      │
│                                                  │
│ Select ASIN:        [Dropdown: 37 ASINs]       │
│ Select Marketplace: [Dropdown: UK / US]        │
│                                                  │
│ ┌───────────────────────────────────────────┐  │
│ │ INPUTS                                     │  │
│ ├───────────────────────────────────────────┤  │
│ │ ASIN              → Auto-filled            │  │
│ │ Marketplace       → Auto-filled            │  │
│ │ Buy Box Avg (BB̄) → From database          │  │
│ │ Weight (kg)       → From database          │  │
│ │ Our Cost (C)      → From database          │  │
│ └───────────────────────────────────────────┘  │
│                                                  │
│ ┌───────────────────────────────────────────┐  │
│ │ COMPONENTS                                 │  │
│ ├───────────────────────────────────────────┤  │
│ │ Amazon Fee (AF)          → 17% of BB̄      │  │
│ │ Fulfilment Cost (FC)     → UK/US tiers    │  │
│ │ Shipping to Seller (SC)  → UK/US rates    │  │
│ │ Total Seller Costs (S)   → FC+AF+SC       │  │
│ └───────────────────────────────────────────┘  │
│                                                  │
│ ┌───────────────────────────────────────────┐  │
│ │ BOUNDS                                     │  │
│ ├───────────────────────────────────────────┤  │
│ │ Qmin (Our Floor)          → Calculated    │  │
│ │ Qmax @ 20% Seller ROI     → Calculated    │  │
│ │ Qmax @ 15% Seller ROI     → Calculated    │  │
│ │ Qmax @ 10% Seller ROI     → Calculated    │  │
│ └───────────────────────────────────────────┘  │
│                                                  │
│ ┌───────────────────────────────────────────┐  │
│ │ FINAL QUOTE & RESULTS                      │  │
│ ├───────────────────────────────────────────┤  │
│ │ Feasible?                → YES/NO          │  │
│ │ ROI Tier Used (%)        → 20/15/10       │  │
│ │ Wholesale Quote (Q)      → FINAL PRICE    │  │
│ │ Seller ROI (%)           → Performance    │  │
│ │ Our ROI (%)              → Our profit     │  │
│ │ Our Margin (Absolute)    → Q - C          │  │
│ │ Our Margin (%)           → Percentage     │  │
│ └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

#### Key Features:

- ✅ **Automatic Updates** - All values update when you change ASIN or marketplace
- ✅ **Excel Formulas** - All calculations use Excel formulas (you can see them in formula bar)
- ✅ **No Manual Entry** - Everything pulls from Raw Data sheet
- ✅ **Clear Sections** - Organized by Inputs, Components, Bounds, Results

---

### Sheet 2: "Raw Data" - **COMPLETE DATA TABLE**

This sheet contains **all 74 calculations** (37 products × 2 marketplaces) in a filterable table.

#### Columns Explained:

| Column Group | Columns | Description |
|--------------|---------|-------------|
| **Identifiers** | ASIN, Title, Marketplace | Product identification |
| **Inputs** | Weight_kg, BB_avg, C_cost, m, fx_gbp_to_usd | Base data from database |
| **Components** | AF, FC, SC, S_bundle | Calculated cost components |
| **Bounds** | Qmin, Qmax_20, Qmax_15, Qmax_10 | Price boundaries |
| **Results** | r_used, Quote_Q, Seller_ROI_%, Our_ROI_%, Margin_abs, Margin_%, Feasible, Reason | Final calculations |

#### What Each Column Means:

**Identifiers:**
- `ASIN` - Product identifier
- `Title` - Product title (truncated to 50 chars)
- `Marketplace` - UK or US

**Inputs (from database):**
- `Weight_kg` - Product weight in kilograms (converted from pounds)
- `BB_avg` - 30-day average Buy Box price
- `C_cost` - Our acquisition cost (what we pay)
- `m` - Our margin target (0.10 = 10%)
- `fx_gbp_to_usd` - Exchange rate (1.30)

**Components (calculated):**
- `AF` - Amazon Fee = 17% × BB_avg
- `FC` - Fulfilment Cost (tiered by weight & marketplace)
- `SC` - Shipping to Seller (UK: £0.50, US: £6×1.30=$7.80)
- `S_bundle` - Total Seller Costs = FC + AF + SC

**Bounds (calculated):**
- `Qmin` - Our floor price = max(C_cost, C_cost × (1+m))
- `Qmax_20` - Max quote at 20% seller ROI
- `Qmax_15` - Max quote at 15% seller ROI
- `Qmax_10` - Max quote at 10% seller ROI

**Results (final):**
- `r_used` - Which ROI tier was used (0.20, 0.15, or 0.10)
- `Quote_Q` - **THE WHOLESALE QUOTE** (what we charge seller)
- `Seller_ROI_%` - Seller's return on investment
- `Our_ROI_%` - Our return on investment
- `Margin_abs` - Our absolute margin (Quote_Q - C_cost)
- `Margin_%` - Our margin as percentage
- `Feasible` - Can we make a deal? (TRUE/FALSE)
- `Reason` - If not feasible, why not

#### How to Use Raw Data Sheet:

1. **Filter** - Click dropdown arrows in header row to filter by:
   - Marketplace (UK or US)
   - Feasible (YES or NO)
   - Specific ASINs

2. **Sort** - Click column headers to sort by:
   - Highest Quote_Q
   - Best Seller_ROI_%
   - Best Our_ROI_%
   - Products with most margin

3. **Analyze** - Use Excel features:
   - Conditional formatting to highlight profitable items
   - Pivot tables to summarize by marketplace
   - Charts to visualize margins

---

## 🔍 Understanding the Calculations

### Example Row Breakdown (UK Marketplace):

```
ASIN: 0076697940
Marketplace: UK
Weight_kg: 2.18
BB_avg: £65.00
C_cost: £44.95
m: 0.10
```

**Step 1: Calculate Components**
```
AF = 0.17 × £65.00 = £11.05
FC = £3.50 (2.18kg falls in 1-2kg UK tier)
SC = £0.50 (UK flat rate)
S_bundle = £11.05 + £3.50 + £0.50 = £15.05
```

**Step 2: Calculate Bounds**
```
Qmin = max(£44.95, £44.95 × 1.10) = £49.45
```

**Step 3: Try ROI Tiers**
```
Qmax(20%) = (£65.00 - 1.2 × £15.05) / 1.2 = £39.92
Qmax(15%) = (£65.00 - 1.15 × £15.05) / 1.15 = £41.49
Qmax(10%) = (£65.00 - 1.10 × £15.05) / 1.10 = £43.94

Since Qmin (£49.45) > all Qmax values:
→ NOT FEASIBLE
```

**Result:**
```
Feasible: FALSE
Reason: Even at 10% seller ROI, Qmax < Qmin
Quote_Q: £49.45 (defaults to Qmin for info)
```

---

## 📊 Key Insights from Your Data

### Overall Statistics:

- **Total Products:** 37 unique items
- **Total Quotes Calculated:** 74 (37 × 2 marketplaces)
- **Feasible Quotes:** 22 (30%)
- **No-Deal Scenarios:** 52 (70%)

### Why So Many "No Buy Box Data"?

Many products show "⚠️ No buy box data" because:
1. Product exists in UK but not US (or vice versa)
2. No Keepa data for that marketplace yet
3. Product may need backfill from Keepa API

**This is normal** - not all products sell in both marketplaces.

### Feasibility Breakdown:

**Feasible (22 quotes):**
- These are products where we CAN offer a competitive quote
- Seller gets 10-20% ROI
- We maintain our 10% margin target

**Not Feasible (5 quotes marked as "No deal"):**
- Our cost is too high relative to market price
- Even at 10% seller ROI, we'd lose money
- Quote would be below our cost floor

**No Data (47 entries):**
- Missing buy box price history
- May need to backfill Keepa data
- Or product doesn't sell in that marketplace

---

## 🎯 How to Check Specific Calculations

### Method 1: Interactive Summary Sheet

1. Open `Book_Portal_Quote_Report.xlsx`
2. Go to "Quote Summary" sheet
3. Select ASIN from dropdown (B3)
4. Select Marketplace from dropdown (B4)
5. Review all calculations displayed

### Method 2: Raw Data Sheet

1. Open `Book_Portal_Quote_Report.xlsx`
2. Go to "Raw Data" sheet
3. Find your product (use Ctrl+F or filter)
4. Read across the row to see all values

### Method 3: Excel Formulas

1. Click any cell in "Quote Summary" sheet
2. Look at formula bar (top of Excel)
3. See how it references "Raw Data" sheet
4. Example: `=INDEX('Raw Data'!$E:$E, MATCH(B3&B4, 'Raw Data'!$A:$A&'Raw Data'!$C:$C, 0))`

---

## 💡 Marketplace Differences Visible in Excel

### UK vs US Comparison for Same Product:

Open the Raw Data sheet and compare two rows with same ASIN:

| Field | UK Example | US Example | Notes |
|-------|-----------|-----------|-------|
| **FC** | £3.50 | $4.95 | Different tier rates |
| **SC** | £0.50 | $7.80 | US costs more to ship |
| **S_bundle** | Lower | Higher | US has higher seller costs |
| **Quote_Q** | May be feasible | May not be feasible | US harder due to high SC |

**Key Insight:** Same product can be:
- ✅ Feasible in UK (lower costs)
- ❌ Not feasible in US (higher shipping)

---

## 📝 CSV Backup File

Also included: `Book_Portal_Quote_Report.csv`

- Same data as "Raw Data" sheet
- Can open in Excel, Google Sheets, or any spreadsheet
- Good for importing into other systems
- Plain text format (no formulas)

---

## 🚀 Next Steps

### 1. Review Feasible Products

Filter "Raw Data" sheet by:
- `Feasible = TRUE`
- Sort by `Our_ROI_%` descending

These are your **best opportunities**.

### 2. Investigate No-Deal Products

Filter by:
- `Feasible = FALSE`
- `Reason` contains text

Analyze why:
- Is our cost too high?
- Is buy box price too low?
- Can we negotiate better cost?

### 3. Check Missing Data

Filter by:
- `Reason` contains "No buy box data"

These need:
- Keepa backfill for that marketplace
- Or confirmation product doesn't sell there

### 4. Test Different Scenarios

Regenerate report with different parameters:

```bash
# Lower margin requirement
python generate_quote_report.py --m 0.05

# Different FX rate
python generate_quote_report.py --fx 1.35

# Both
python generate_quote_report.py --m 0.05 --fx 1.35
```

---

## 📞 Quick Reference

### File Locations:

```
Wholesale-Pricing-Portal/
├── Book_Portal_Quote_Report.xlsx  ← Main report (74 quotes)
├── Book_Portal_Quote_Report.csv   ← CSV backup
├── Quote_Calculator_UK_Example.xlsx ← Single example
└── backend/app/
    └── generate_quote_report.py   ← Generator script
```

### Command to Regenerate:

```bash
cd backend/app
python generate_quote_report.py --fx 1.30 --m 0.10
```

### What Each File Shows:

- **Main Report Excel** - All products, both marketplaces, interactive
- **CSV** - Same data, plain text format
- **UK Example** - Single calculation walkthrough

---

## ✅ Verification Checklist

To verify all logic is correct, check these in the Excel:

- [ ] AF = 17% of BB_avg (check any row)
- [ ] FC matches weight tier (2kg UK = £3.50, US = $4.95)
- [ ] SC = £0.50 UK, $7.80 US (at fx=1.30)
- [ ] S_bundle = AF + FC + SC
- [ ] Qmin = C_cost × 1.10 (when m=0.10)
- [ ] Quote_Q ≤ Qmax_20/15/10 (whichever tier used)
- [ ] Quote_Q ≥ Qmin (always, even if not feasible)
- [ ] Seller_ROI_% ≈ 20/15/10 (for feasible quotes)
- [ ] Our_ROI_% ≈ 10% (our target)
- [ ] Margin_abs = Quote_Q - C_cost
- [ ] Feasible = TRUE only when Qmin ≤ Qmax

---

**All calculations are now visible in the Excel files for your review!** 

Open `Book_Portal_Quote_Report.xlsx` and use the dropdowns in "Quote Summary" sheet to explore different products and marketplaces. 📊✨





