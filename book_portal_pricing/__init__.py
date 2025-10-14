"""
Book Portal Pricing Package
----------------------------
Purpose:
- Calculate wholesale quotes for book sellers
- Implement smooth continuous ROI strategy (no harsh tier jumps)
- Generate Excel reports for quote analysis
- Support UK (GBP) and US (USD) marketplaces

Main Entry Point:
    from book_portal_pricing import calculate_quote
    
    outputs, excel_bytes, mime_type = calculate_quote(
        repo=my_repo,
        product_id='ASIN123',
        marketplace='UK',
        m=0.10,
        fx_gbp_to_usd=1.30
    )

Package Structure:
- money.py: Decimal-based currency utilities
- tiers.py: Fulfillment and shipping cost calculations
- calculator.py: Core quote decision logic (smooth continuous ROI)
- repo.py: Database interface for fetching product data
- excel_export.py: Excel/CSV export functionality
- examples.py: CLI testing tool
"""

from .calculator import calculate_quote, decide_quote, Inputs, Outputs

__all__ = [
    'calculate_quote',
    'decide_quote', 
    'Inputs',
    'Outputs',
]



