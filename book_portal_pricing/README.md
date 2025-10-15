# Book Portal Quote Calculator

**Python 3.11** quote calculator for wholesale book pricing with **smooth continuous ROI strategy** (no harsh tier jumps).

---

## 🎯 Overview

This package implements a **seller-favoured** pricing strategy with smooth, continuous ROI calculations:

- ✅ **NO HARSH TIER JUMPS** - Continuous seller ROI from 10% up to 40%+
- ✅ **Seller-Favoured Priority** - We secure our 20% ROI first when seller could exceed 30%
- ✅ **Our ROI Constrained** - Always within [10%, 20%] when feasible
- ✅ **No Tax/VAT** - All prices treated "as provided"
- ✅ **Dual Marketplace** - Support for UK (GBP) and US (USD)

---

## 📦 Project Structure

```
book_portal_pricing/
├── __init__.py              # Package exports
├── money.py                 # Decimal-based currency utilities
├── tiers.py                 # Fulfillment & shipping cost tiers
├── calculator.py            # Core quote decision logic (SMOOTH CONTINUOUS)
├── repo.py                  # Repository interface (Protocol)
├── excel_export.py          # Excel/CSV export (3 sheets)
├── examples.py              # CLI testing tool
├── verify_smooth_roi.py     # Verification script
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_tiers.py        # FC/SC tier boundary tests
│   └── test_calculator.py   # Quote logic tests (Case A/B/C)
└── README.md                # This file
```

---

## 🚀 Quick Start

### Installation

The package uses only standard library + optional dependencies:

```bash
# Required (standard library)
- decimal (built-in)

# Optional
pip install openpyxl  # For Excel export (falls back to CSV)
pip install pytest    # For running tests
```

### Basic Usage

```python
from book_portal_pricing import calculate_quote, decide_quote, Inputs
from book_portal_pricing.money import D

# Direct calculation (when you have data)
inputs = Inputs(
    product_id='B0ABCD1234',
    marketplace='UK',
    bb_avg=D('20.00'),      # 30-day Buy Box average
    c_cost=D('8.00'),       # Our acquisition cost
    weight_kg=D('2.0'),     # Product weight
    m=D('0.10'),            # Our ROI floor (10%)
    fx_gbp_to_usd=D('1.30') # Exchange rate
)

outputs = decide_quote(inputs)

if outputs.feasible:
    print(f"Quote: £{outputs.quote_q}")
    print(f"Seller ROI: {outputs.seller_roi_pct}%")
    print(f"Our ROI: {outputs.our_roi_pct}%")
else:
    print(f"No deal: {outputs.reason}")
```

### Integration with Database

```python
from book_portal_pricing import calculate_quote
from your_db_layer import YourRepo

# Implement Repo protocol (see repo.py)
repo = YourRepo(session)

# Calculate quote (automatically fetches data)
outputs, excel_bytes, mime_type = calculate_quote(
    repo=repo,
    product_id='B0ABCD1234',
    marketplace='UK',
    m=0.10,
    fx_gbp_to_usd=1.30
)
```

---

## 🧮 Business Rules

### Variables

| Symbol | Description |
|--------|-------------|
| **BB̄** | 30-day average Buy Box price (simple mean, ignore nulls) |
| **AF** | Amazon fee = 0.17 × BB̄ |
| **FC** | Fulfillment cost (tiered by weight & marketplace) |
| **SC** | Shipping to seller (excluded from Q, included in S) |
| **C** | Our acquisition cost |
| **Q** | Wholesale quote to seller |
| **S** | FC + AF + SC (total seller costs) |
| **m** | Our ROI floor (default 0.10 = 10%) |

### ROI Formulas (Smooth, Continuous)

**Seller ROI:**
```
ROI_seller(Q) = (BB̄ - (Q + S)) / (Q + S)
```

**Our ROI:**
```
ROI_us(Q) = (Q - C) / C
```

### Decision Logic (NO TIERS)

1. **Define our ROI band:**
   - Q_min = C × (1 + m) where m=0.10 → 10% floor
   - Q_max_our = C × 1.20 → 20% cap

2. **Compute seller boundary quotes:**
   - Q_seller10 = (BB̄ - 1.10×S) / 1.10
   - Q_seller30 = (BB̄ - 1.30×S) / 1.30
   - Q_seller40 = (BB̄ - 1.40×S) / 1.40

3. **Smooth decision (seller-favoured):**
   - a) Compute seller ROI at our 20% cap: ROI_seller(Q_max_our)
   - b) If ROI_seller(Q_max_our) ≥ 10%:
     - Set Q = Q_max_our (we take our 20% ROI)
     - Seller ROI floats smoothly and may exceed 30%
     - **This satisfies: if seller could be >30%, we first fill our ROI to 20%**
   - c) Else (seller would drop below 10% if we take 20%):
     - Lower Q just enough so seller ROI hits 10%: Q = Q_seller10
     - If Q < Q_min: no-deal
   - d) Always clamp final Q to [Q_min, Q_max_our]

**Result:** We either sit at our 20% cap (favouring seller with any extra surplus), or we slide down smoothly until seller ROI is 10%, but never below our 10% floor. **This removes harsh 20/30/40% jumps.**

---

## 📊 Fulfillment Cost Tiers

### UK (GBP)

| Weight Range | Cost |
|--------------|------|
| 0-1kg | £3.00 |
| 1-2kg | £3.50 |
| 2-5kg | £4.50 |
| 5-8kg | £5.75 |
| >8kg | £6.50 + £0.50 per kg over 8kg |

### US (USD)

| Weight Range | Cost |
|--------------|------|
| 0-1kg | $4.25 |
| 1-2kg | $4.95 |
| 2-5kg | $6.25 |
| 5-8kg | $7.75 |
| >8kg | $8.50 + $0.50 per kg over 8kg |

### Shipping Costs (SC)

- **UK:** £0.50 (flat rate)
- **US:** £6.00 × fx_gbp_to_usd (default $7.80 at 1.30)

---

## 📈 Excel Export

Generate interactive Excel workbook with 3 sheets:

```python
from book_portal_pricing.excel_export import create_workbook

excel_bytes, mime_type = create_workbook(
    repo=repo,
    marketplace='UK',
    product_ids=['ASIN1', 'ASIN2', ...]
)

# Save to file
with open('quote_report.xlsx', 'wb') as f:
    f.write(excel_bytes)
```

### Sheet 1: Model Summary

- Purpose, variables, formulas
- Rationale for smooth continuous ROI
- FC/SC tier structure

### Sheet 2: Quote Summary (Interactive)

- **Dropdowns:** Select ASIN and Marketplace
- **Auto-populated:** Quote, ROIs, margins, components
- **Formulas:** INDEX/MATCH from Raw Data sheet
- **Conditional formatting:**
  - Seller ROI ≥ 30% → Green
  - Our ROI < 10% → Red

### Sheet 3: Raw Data

- All products (38 rows from DB)
- Complete calculation components
- Both feasible and non-feasible products
- Helper column for INDEX/MATCH (ASIN|Marketplace)

---

## 🧪 Testing

### Run Examples

```bash
# Run CLI examples (no database required)
python -m book_portal_pricing.examples

# Run verification script (smooth ROI proof)
python -m book_portal_pricing.verify_smooth_roi
```

### Run Test Suite (requires pytest)

```bash
# Install pytest
pip install pytest

# Run all tests
python -m pytest book_portal_pricing/tests/ -v

# Run specific test module
python -m pytest book_portal_pricing/tests/test_tiers.py -v
python -m pytest book_portal_pricing/tests/test_calculator.py -v

# Run with coverage
python -m pytest --cov=book_portal_pricing book_portal_pricing/tests/
```

### Test Coverage

**test_tiers.py:**
- ✅ FC tier boundaries (UK/US, all 5 tiers)
- ✅ SC calculations (UK/US, exchange rates)
- ✅ Edge cases (zero/negative weight, very large weights)

**test_calculator.py:**
- ✅ **Case A:** High margin → Q = Q_max_our, seller ROI ≥ 30%
- ✅ **Case B:** Tight margin → Q = Q_seller10, our ROI ∈ [10%, 20%]
- ✅ **Case C:** Infeasible → no-deal (seller <10% at our floor)
- ✅ Smooth transitions (no harsh jumps)
- ✅ ROI constraints validation
- ✅ Component calculations
- ✅ Exchange rate variations

---

## 🔍 Verification Results

The verification script demonstrates **smooth continuous ROI** with no harsh tier jumps:

```
BB (£)   Q (£)    Seller ROI   Our ROI    Decision
------------------------------------------------------------------------
30       9.60     60.43%       20.00%     At our 20% cap (seller favoured)
29       9.60     56.50%       20.00%     At our 20% cap (seller favoured)
28       9.60     52.51%       20.00%     At our 20% cap (seller favoured)
...
23       9.60     31.35%       20.00%     At our 20% cap (seller favoured)
22       9.60     26.87%       20.00%     At our 20% cap (seller favoured)
21       9.60     22.31%       20.00%     At our 20% cap (seller favoured)
20       9.60     17.65%       20.00%     At our 20% cap (seller favoured)
19       9.60     12.89%       20.00%     At our 20% cap (seller favoured)
18       9.30     10.00%       16.30%     Lowered for seller 10% ROI
17       8.80     8.35%        10.00%     NO DEAL (seller <10% at our floor)
...
```

**Key Observations:**
1. ✅ No harsh tier jumps (20%/30%/40%) - ROI changes smoothly
2. ✅ Our ROI stays at 20% when seller can exceed 30% (seller-favoured)
3. ✅ Our ROI constrained to [10%, 20%] when feasible
4. ✅ Seller ROI floats continuously (no discrete tiers)

---

## 📝 Implementation Notes

### Repository Interface

Your database layer must implement the `Repo` protocol:

```python
from decimal import Decimal
from typing import Sequence, Literal

class YourRepo:
    def get_bb_prices_last_30_days(
        self, 
        product_id: str, 
        marketplace: Literal["UK", "US"]
    ) -> Sequence[Decimal]:
        """Return up to 30 daily Buy Box prices (filter out None)."""
        ...
    
    def get_weight_kg(self, product_id: str) -> Decimal:
        """Return product weight in kg."""
        ...
    
    def get_our_cost_c(self, product_id: str) -> Decimal:
        """Return our acquisition cost."""
        ...
```

### Decimal Precision

All monetary calculations use Python's `Decimal` type with 12-digit precision:

```python
from book_portal_pricing.money import D, to_penny, pct, mul_pct

# Create Decimal
price = D('19.99')

# Round to penny
rounded = to_penny(D('19.999'))  # → Decimal('20.00')

# Convert to percentage
roi_pct = pct(D('0.15'))  # → Decimal('15.00')

# Multiply by percentage
fee = mul_pct(D('100.00'), D('0.17'))  # → Decimal('17.00')
```

---

## 🎓 Usage Examples

### Example 1: High Margin Product

```python
inputs = Inputs(
    product_id='HIGH_MARGIN',
    marketplace='UK',
    bb_avg=D('30.00'),
    c_cost=D('8.00'),
    weight_kg=D('2.0'),
    m=D('0.10')
)
outputs = decide_quote(inputs)

# Result:
# - feasible: True
# - quote_q: £9.60
# - seller_roi_pct: 60.43% (smooth, no tiers!)
# - our_roi_pct: 20.00% (at our cap)
# Decision: We took our 20%, seller gets >30%
```

### Example 2: Tight Margin Product

```python
inputs = Inputs(
    product_id='TIGHT_MARGIN',
    marketplace='UK',
    bb_avg=D('18.50'),
    c_cost=D('8.00'),
    weight_kg=D('2.0'),
    m=D('0.10')
)
outputs = decide_quote(inputs)

# Result:
# - feasible: True
# - quote_q: £9.60
# - seller_roi_pct: 10.48% (lowered for seller)
# - our_roi_pct: 20.00% (still at cap due to margin)
# Decision: Lowered Q to ensure seller gets 10% ROI
```

### Example 3: Infeasible Product

```python
inputs = Inputs(
    product_id='NO_DEAL',
    marketplace='UK',
    bb_avg=D('10.00'),
    c_cost=D('8.00'),
    weight_kg=D('2.0'),
    m=D('0.10')
)
outputs = decide_quote(inputs)

# Result:
# - feasible: False
# - reason: "No deal: seller ROI <10% even at our 10% floor."
# - seller_roi_pct: -31.03% (would be negative)
# Decision: No deal, protect our 10% floor
```

---

## ✅ Acceptance Checklist

- [x] Old quote code removed
- [x] New structure created exactly as specified
- [x] Smooth range logic implemented (no harsh tiers)
- [x] Seller-favoured rule respected (we fill our 20% first if seller >30%)
- [x] Our ROI always in [10%, 20%] (or no-deal if seller <10% at our floor)
- [x] Excel: Model Summary, Quote Summary (interactive), Raw Data
- [x] Formulas in "Quote Summary" correctly populate from "Raw Data"
- [x] Comprehensive test suite (tiers + calculator)
- [x] Examples and verification scripts
- [x] No linter errors

---

## 📧 Support

For questions or issues:

1. Check examples: `python -m book_portal_pricing.examples`
2. Run verification: `python -m book_portal_pricing.verify_smooth_roi`
3. Review test suite: `book_portal_pricing/tests/`

---

**Built with ❤️ for the Wholesale Book Portal**

*Smooth continuous ROI strategy - because harsh tier jumps hurt everyone.*




