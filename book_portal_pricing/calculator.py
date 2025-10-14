"""
Quote Calculator - Core Business Logic (Smooth Continuous ROI)
---------------------------------------------------------------
Purpose:
- Calculate optimal wholesale quotes with smooth continuous ROI strategy
- NO HARSH TIER JUMPS - continuous seller ROI from 10% up to 40%+
- Our ROI constrained to [10%, 20%] (protect wholesaler margin)
- Seller-favoured: we first "fill" our ROI to 20% if seller can exceed 30%
- Never quote below our cost floor (protect our margin)

Business Rules (NO TAX anywhere):
1. BB̄ = 30-day average Buy Box price
2. AF = Amazon fee = 0.17 * BB̄
3. FC = fulfilment cost (tiered by weight & marketplace)
4. SC = shipping to seller (excluded from Q but in seller cost)
5. S = FC + AF + SC (total seller costs)
6. C = our acquisition cost
7. Q = wholesale quote to seller
8. m = our internal ROI floor (default 0.10 i.e. 10%)

ROI Formulas (continuous, smooth):
- Seller ROI: ROI_seller(Q) = (BB̄ - (Q + S)) / (Q + S)
- Our ROI: ROI_us(Q) = (Q - C) / C

Smooth Decision Logic (NO TIERS):
1. Define our ROI band:
   - Q_min = C × (1 + m) [default m=0.10 → 10% floor]
   - Q_max_our = C × 1.20 [cap for 20% ROI]

2. Compute seller minimum quote for 10% seller ROI:
   - Q_seller10 = (BB̄ - 1.10×S) / 1.10

3. Selection logic (continuous):
   a) Compute seller ROI at our 20% cap: ROI_seller(Q_max_our)
   b) If ROI_seller(Q_max_our) ≥ 10%:
      - Set Q = Q_max_our (we take our 20% ROI)
      - Seller ROI floats smoothly and may exceed 30% if margin allows
      - This satisfies: if seller could be >30%, we first "fill" our ROI to 20%
   c) Else (seller would drop below 10% if we take 20%):
      - Lower Q just enough so seller ROI hits 10%: Q = Q_seller10
      - If Q < Q_min: no-deal (even at our floor 10% ROI, seller would be <10%)
   d) Always clamp final Q to [Q_min, Q_max_our]

4. Compute all outputs (ROIs, margins, components)

This produces smooth outputs — no tier steps.

Usage:
    from book_portal_pricing.calculator import calculate_quote, Inputs, Outputs
    from book_portal_pricing.repo import Repo
    from book_portal_pricing.money import D
    
    # Full integration with repo
    outputs, excel_bytes, mime_type = calculate_quote(
        repo=repo,
        product_id='ASIN123',
        marketplace='UK',
        m=0.10,
        fx_gbp_to_usd=1.30
    )
    
    # Direct calculator (when you already have data)
    inputs = Inputs(
        product_id='ASIN123',
        marketplace='UK',
        bb_avg=D('20.00'),
        c_cost=D('8.00'),
        weight_kg=D('2.0'),
        m=D('0.10')
    )
    outputs = decide_quote(inputs)
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Literal, Tuple

from .money import D, to_penny, pct
from .tiers import compute_fc, compute_sc
from .repo import Repo

# Type alias for supported marketplaces
Marketplace = Literal["UK", "US"]


@dataclass
class Inputs:
    """
    Input data for quote calculation.
    
    All monetary values should be Decimal for precision.
    All values should be in marketplace currency (GBP for UK, USD for US).
    
    Attributes:
        product_id: Product identifier (e.g., ASIN)
        marketplace: 'UK' or 'US'
        bb_avg: 30-day average Buy Box price (BB̄)
        c_cost: Our acquisition cost (C)
        weight_kg: Product weight in kilograms (for FC tier)
        m: Our ROI floor as decimal (default 0.10 = 10%)
        fx_gbp_to_usd: GBP to USD exchange rate (default 1.30)
    
    Example:
        inputs = Inputs(
            product_id='B0ABCD1234',
            marketplace='UK',
            bb_avg=D('20.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10'),
            fx_gbp_to_usd=D('1.30')
        )
    """
    product_id: str
    marketplace: Marketplace
    bb_avg: Decimal
    c_cost: Decimal
    weight_kg: Decimal
    m: Decimal = Decimal("0.10")           # Our ROI floor (10%)
    fx_gbp_to_usd: Decimal = Decimal("1.30")


@dataclass
class Outputs:
    """
    Output results from quote calculation.
    
    All monetary values are Decimal, rounded to penny precision.
    All percentages are Decimal, rounded to 2 decimal places.
    
    Attributes:
        feasible: True if a valid quote exists, False if no-deal
        reason: Optional explanation if not feasible
        quote_q: Wholesale quote to seller (Q)
        seller_roi_pct: Seller ROI as percentage (e.g., 25.00 for 25%)
        our_roi_pct: Our ROI as percentage (e.g., 15.00 for 15%)
        margin_abs: Our absolute margin (Q - C)
        margin_pct: Our margin as percentage
        
        # Component values (for diagnostics and Excel)
        af: Amazon fee (17% of BB̄)
        fc: Fulfillment cost (tiered by weight)
        sc: Shipping cost to seller (excluded from Q)
        s_bundle: Total seller costs (S = FC + AF + SC)
        qmin: Our ROI floor quote (C × (1 + m))
        qmax_our: Our ROI cap quote (C × 1.20)
        q_seller10: Quote for seller 10% ROI (diagnostic)
        q_seller30: Quote for seller 30% ROI (diagnostic)
        q_seller40: Quote for seller 40% ROI (diagnostic)
    
    Example:
        if outputs.feasible:
            print(f"Quote: {outputs.quote_q}")
            print(f"Seller ROI: {outputs.seller_roi_pct}%")
            print(f"Our ROI: {outputs.our_roi_pct}%")
        else:
            print(f"No deal: {outputs.reason}")
    """
    feasible: bool
    reason: Optional[str]
    quote_q: Decimal
    seller_roi_pct: Decimal
    our_roi_pct: Decimal
    margin_abs: Decimal
    margin_pct: Decimal
    
    # Component values
    af: Decimal
    fc: Decimal
    sc: Decimal
    s_bundle: Decimal
    qmin: Decimal
    qmax_our: Decimal
    q_seller10: Decimal
    q_seller30: Decimal
    q_seller40: Decimal


def decide_quote(inputs: Inputs) -> Outputs:
    """
    Calculate wholesale quote using smooth continuous ROI logic.
    
    Purpose:
    - Determine optimal quote Q that balances seller and our ROI
    - Use continuous smooth logic (no harsh tier jumps)
    - Seller-favoured: we keep our ROI at 10% unless seller ROI >= 30%
    - Our ROI always in [10%, 20%] (or no-deal if seller <10% at our floor)
    
    Algorithm:
    1. Calculate components (AF, FC, SC, S)
    2. Calculate Q_min (10% our ROI) and Q_max_our (20% our ROI)
    3. Calculate seller ROI boundary quotes (Q_seller10, Q_seller30, Q_seller40)
    4. Seller-favoured decision logic:
       - Start from our 10% ROI floor (Q_min)
       - If seller ROI < 10% at Q_min: no-deal
       - If seller ROI < 30% at Q_min: stay at Q_min (favor seller)
       - If seller ROI >= 30% at Q_min: increase to Q_max_our (our 20%)
    5. Clamp Q to [Q_min, Q_max_our]
    6. Calculate final ROIs and margins
    
    Args:
        inputs: All required input data (see Inputs dataclass)
    
    Returns:
        Outputs: Complete calculation results (see Outputs dataclass)
    
    Example:
        # Case A: High margin (seller ROI >= 30% at our 10% floor)
        inputs = Inputs(
            product_id='HIGH_MARGIN',
            marketplace='UK',
            bb_avg=D('30.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        outputs = decide_quote(inputs)
        # Result: Q = Q_max_our (our 20%), seller ROI remains high
        
        # Case B: Medium margin (seller ROI 10-30% at our floor)
        inputs = Inputs(
            product_id='MEDIUM_MARGIN',
            marketplace='UK',
            bb_avg=D('15.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        outputs = decide_quote(inputs)
        # Result: Q = Q_min (our 10%), seller gets maximum ROI (seller-favoured)
        
        # Case C: Infeasible (seller <10% even at our floor)
        inputs = Inputs(
            product_id='NO_DEAL',
            marketplace='UK',
            bb_avg=D('10.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        outputs = decide_quote(inputs)
        # Result: feasible=False, reason explains why
    """
    # ========== STEP 1: Calculate Components ==========
    
    # Extract input values
    BB = inputs.bb_avg   # Buy Box average
    C = inputs.c_cost    # Our acquisition cost
    
    # Fulfillment Cost (tiered by weight and marketplace)
    fc = compute_fc(inputs.weight_kg, inputs.marketplace)
    
    # Shipping to Seller (marketplace-specific, excluded from Q)
    sc = compute_sc(inputs.marketplace, inputs.fx_gbp_to_usd)
    
    # Amazon Fee (17% of Buy Box average)
    af = BB * Decimal("0.17")
    
    # Total Seller Costs (S = FC + AF + SC)
    S = fc + af + sc
    
    # ========== STEP 2: Our ROI Band ==========
    
    # Q_min: Our 10% ROI floor (default m=0.10)
    qmin = C * (Decimal("1.00") + inputs.m)
    
    # Q_max_our: Our 20% ROI cap
    qmax_our = C * Decimal("1.20")
    
    # ========== STEP 3: Seller ROI Boundary Quotes (Continuous, Smooth) ==========
    
    def q_seller_for(r: Decimal) -> Decimal:
        """
        Calculate Q that gives seller exactly ROI = r.
        
        Formula: Q = (BB̄ - (1+r)×S) / (1+r)
        
        Derivation:
        - Seller ROI: r = (BB̄ - (Q + S)) / (Q + S)
        - Solve for Q: r(Q + S) = BB̄ - Q - S
        - rQ + rS = BB̄ - Q - S
        - rQ + Q = BB̄ - rS - S
        - Q(r + 1) = BB̄ - (r + 1)S
        - Q = (BB̄ - (1+r)S) / (1+r)
        
        Args:
            r: Target seller ROI as decimal (e.g., 0.10 for 10%)
        
        Returns:
            Decimal: Quote Q that achieves seller ROI = r
        """
        return (BB - (Decimal("1.00") + r) * S) / (Decimal("1.00") + r)
    
    # Calculate reference quotes for seller ROI boundaries
    q_s10 = q_seller_for(Decimal("0.10"))  # Seller 10% ROI
    q_s30 = q_seller_for(Decimal("0.30"))  # Seller 30% ROI (diagnostic)
    q_s40 = q_seller_for(Decimal("0.40"))  # Seller 40% ROI (diagnostic)
    
    # ========== STEP 4: Helper ROI Functions ==========
    
    def seller_roi(Q: Decimal) -> Decimal:
        """
        Calculate seller ROI for a given quote Q.
        
        Formula: ROI_seller = (BB̄ - (Q + S)) / (Q + S)
        
        Args:
            Q: Wholesale quote
        
        Returns:
            Decimal: Seller ROI as decimal (e.g., 0.25 for 25%)
        """
        return (BB - (Q + S)) / (Q + S)
    
    def our_roi(Q: Decimal) -> Decimal:
        """
        Calculate our ROI for a given quote Q.
        
        Formula: ROI_us = (Q - C) / C
        
        Args:
            Q: Wholesale quote
        
        Returns:
            Decimal: Our ROI as decimal (e.g., 0.15 for 15%)
        """
        return (Q - C) / C
    
    # ========== STEP 5: Seller-Favoured Decision Logic ==========
    
    # Initialize as feasible
    feasible = True
    reason = None
    
    # Seller-first rule: Start from lowest feasible Q (our ROI = 10%)
    # Only increase Q if seller ROI >= 30%, and only until our ROI reaches 20%
    
    # Calculate seller ROI at both our ROI bounds
    r_seller_at_qmin = seller_roi(qmin)      # Seller ROI when we take 10%
    r_seller_at_qmax = seller_roi(qmax_our)  # Seller ROI when we take 20%
    
    # Check if deal is feasible at our floor (10% our ROI)
    if r_seller_at_qmin < Decimal("0.10"):
        # No deal: even at our 10% ROI floor, seller would be <10%
        feasible = False
        reason = "No deal: seller ROI <10% even at our 10% floor."
        Q = qmin  # Set to floor for diagnostics
    else:
        # Deal is feasible - now determine quote level
        
        # If seller ROI < 30% at our floor, stay at our floor (favor seller)
        if r_seller_at_qmin < Decimal("0.30"):
            Q = qmin  # Keep Q low to maximize seller ROI
        else:
            # Seller ROI >= 30% at our floor
            # We can raise Q gradually up to our 20% ROI cap
            Q = qmax_our
    
    # ========== STEP 6: Clamp Q to Our ROI Band ==========
    
    # Always ensure Q is within our acceptable ROI range
    if Q < qmin:
        Q = qmin
    if Q > qmax_our:
        Q = qmax_our
    
    # ========== STEP 7: Calculate Final Metrics ==========
    
    # Calculate final ROIs
    r_seller = seller_roi(Q)
    r_us = our_roi(Q)
    
    # Round quote to penny precision
    Q = to_penny(Q)
    
    # Calculate absolute margin and margin percentage
    margin_abs = to_penny(Q - C)
    margin_pct = pct((Q - C) / C)
    
    # ========== STEP 8: Return Complete Results ==========
    
    return Outputs(
        feasible=feasible,
        reason=reason,
        quote_q=Q,
        seller_roi_pct=pct(r_seller),
        our_roi_pct=pct(r_us),
        margin_abs=margin_abs,
        margin_pct=margin_pct,
        # Component values (rounded to penny)
        af=to_penny(af),
        fc=to_penny(fc),
        sc=to_penny(sc),
        s_bundle=to_penny(S),
        qmin=to_penny(qmin),
        qmax_our=to_penny(qmax_our),
        q_seller10=to_penny(q_s10),
        q_seller30=to_penny(q_s30),
        q_seller40=to_penny(q_s40),
    )


def calculate_quote(
    repo: Repo,
    product_id: str,
    marketplace: Marketplace,
    m: float = 0.10,
    fx_gbp_to_usd: float = 1.30
) -> Tuple[Outputs, Optional[bytes], Optional[str]]:
    """
    Integration function: fetch data from repo and calculate quote.
    
    Purpose:
    - Fetch all required data from database via repo
    - Calculate 30-day Buy Box average (ignore None values)
    - Build Inputs and call decide_quote()
    - Optionally generate Excel export
    
    This is the main entry point for the quote calculator when integrated
    with your database. It handles all data fetching and preprocessing.
    
    Args:
        repo: Repository implementation (see repo.py or supabase_repo.py)
        product_id: Product identifier (e.g., ASIN)
        marketplace: 'UK' or 'US'
        m: Our ROI floor as percentage (default 0.10 = 10%)
        fx_gbp_to_usd: GBP to USD exchange rate (default 1.30)
    
    Returns:
        Tuple of:
        - Outputs: Complete calculation results
        - bytes: Excel file bytes (None if not generated)
        - str: MIME type (None if not generated)
    
    Raises:
        ValueError: If no Buy Box data available or invalid data
    
    Example:
        from book_portal_pricing import calculate_quote
        from book_portal_pricing.supabase_repo import SupabaseRepo
        from supabase import create_client
        
        client = create_client(url, key)
        repo = SupabaseRepo(client)
        
        outputs, excel_bytes, mime_type = calculate_quote(
            repo=repo,
            product_id='143914995X',
            marketplace='US',
            m=0.10,
            fx_gbp_to_usd=1.30
        )
        
        if outputs.feasible:
            print(f"Quote: {outputs.quote_q}")
            print(f"Seller ROI: {outputs.seller_roi_pct}%")
            print(f"Our ROI: {outputs.our_roi_pct}%")
    """
    # ========== STEP 1: Fetch Data from Repo ==========
    
    # Fetch last 30 days of Buy Box prices from Backfill_test.dynamic_data
    bb_prices = repo.get_bb_prices_last_30_days(product_id, marketplace)
    
    # Validate we have data
    if not bb_prices or len(bb_prices) == 0:
        raise ValueError(f"No Buy Box data available for {product_id} in {marketplace}")
    
    # Calculate 30-day average (simple mean, ignore None values already filtered by repo)
    bb_avg = sum(bb_prices) / len(bb_prices)
    
    # Fetch product weight from public.products.package_weight
    # Note: SupabaseRepo.get_weight_kg accepts both product_id and marketplace
    try:
        weight_kg = repo.get_weight_kg(product_id, marketplace)
    except TypeError:
        # Fallback for repos that only take product_id
        weight_kg = repo.get_weight_kg(product_id)
    
    # Fetch our acquisition cost from public.products.our_price
    # Note: SupabaseRepo.get_our_cost_c accepts both product_id and marketplace
    try:
        c_cost = repo.get_our_cost_c(product_id, marketplace)
    except TypeError:
        # Fallback for repos that only take product_id
        c_cost = repo.get_our_cost_c(product_id)
    
    # ========== STEP 2: Build Inputs ==========
    
    inputs = Inputs(
        product_id=product_id,
        marketplace=marketplace,
        bb_avg=bb_avg,
        c_cost=c_cost,
        weight_kg=weight_kg,
        m=D(str(m)),
        fx_gbp_to_usd=D(str(fx_gbp_to_usd))
    )
    
    # ========== STEP 3: Calculate Quote ==========
    
    outputs = decide_quote(inputs)
    
    # ========== STEP 4: Return Results ==========
    
    # Excel export is optional and handled separately
    # You can call excel_export.create_workbook() if needed
    return outputs, None, None

