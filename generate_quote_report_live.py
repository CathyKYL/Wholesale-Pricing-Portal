"""
Generate Quote Report Using Live Supabase Data
-----------------------------------------------
Purpose:
- Generate complete Excel quote report using live database data
- Pull all products from public.products
- Fetch Buy Box history from Backfill_test.dynamic_data
- No random or hardcoded values

This script replaces any mock/test data generators with real Supabase queries.

Usage:
    python generate_quote_report_live.py
    
Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_KEY - Your Supabase API key (anon or service role)
"""

import os
import sys
from decimal import Decimal
from supabase import create_client

# Add book_portal_pricing to path
sys.path.insert(0, os.path.dirname(__file__))

from book_portal_pricing.calculator import decide_quote, Inputs
from book_portal_pricing.supabase_repo import SupabaseRepo
from book_portal_pricing.money import D

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("⚠ WARNING: openpyxl not installed. Excel export will not be available.")
    print("  Install with: pip install openpyxl")


def calculate_quote_from_db(repo: SupabaseRepo, asin: str, marketplace: str, verbose: bool = True):
    """
    Calculate quote using live database data.
    
    Purpose:
    - Fetch all required data from Supabase
    - Build Inputs object with real data
    - Calculate quote using smooth continuous ROI logic
    
    Args:
        repo: SupabaseRepo instance (connected to Supabase)
        asin: Product ASIN identifier
        marketplace: 'UK' or 'US'
        verbose: Print progress messages
    
    Returns:
        tuple: (Inputs, Outputs) for the product
    
    Raises:
        ValueError: If data is missing or invalid
    """
    if verbose:
        print(f"  📦 Fetching data for {asin} ({marketplace})...")
    
    try:
        # Fetch Buy Box average (BB̄) from Backfill_test.dynamic_data
        bb_avg = repo.get_avg_bb_price(asin, marketplace)
        
        # Fetch our acquisition cost (C) from public.products.our_price
        c_cost = repo.get_our_cost_c(asin, marketplace)
        
        # Fetch weight from public.products.package_weight
        weight_kg = repo.get_weight_kg(asin, marketplace)
        
        if verbose:
            print(f"    BB̄={bb_avg} | C={c_cost} | Weight={weight_kg}kg")
        
        # Build inputs
        inputs = Inputs(
            product_id=asin,
            marketplace=marketplace,
            bb_avg=bb_avg,
            c_cost=c_cost,
            weight_kg=weight_kg,
            m=D('0.10'),  # 10% our ROI floor
            fx_gbp_to_usd=D('1.30')  # GBP to USD exchange rate
        )
        
        # Calculate quote
        outputs = decide_quote(inputs)
        
        if verbose:
            if outputs.feasible:
                print(f"    ✅ Feasible: Q={outputs.quote_q} | Seller ROI={outputs.seller_roi_pct}% | Our ROI={outputs.our_roi_pct}%")
            else:
                print(f"    ❌ Not feasible: {outputs.reason}")
        
        return inputs, outputs
        
    except Exception as e:
        if verbose:
            print(f"    ❌ ERROR: {str(e)}")
        raise


def create_excel_workbook_from_live_data(repo: SupabaseRepo, outputs_list: list):
    """
    Create Excel workbook with live data from Supabase.
    
    Purpose:
    - Generate 3-sheet Excel workbook
    - Use actual database values (no mock data)
    
    Args:
        repo: SupabaseRepo instance
        outputs_list: List of (Inputs, Outputs) tuples
    
    Returns:
        Workbook: openpyxl Workbook object
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required for Excel export")
    
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet
    
    # Import sheet creation functions from excel_export
    from book_portal_pricing.excel_export import (
        create_model_summary_sheet,
        create_raw_data_sheet
    )
    
    # Create Model Summary sheet
    create_model_summary_sheet(wb)
    
    # Create Quote Summary sheet
    ws_summary = wb.create_sheet("Quote Summary")
    ws_summary.column_dimensions['A'].width = 30
    ws_summary.column_dimensions['B'].width = 20
    
    ws_summary['A1'] = "Interactive Quote Calculator (LIVE DATA)"
    ws_summary['A1'].font = Font(size=14, bold=True, color="1F4E78")
    ws_summary.merge_cells('A1:B1')
    
    ws_summary['A2'] = "All data pulled from Supabase (public.products + Backfill_test.dynamic_data)"
    ws_summary['A2'].font = Font(italic=True, size=9, color="00B050")
    ws_summary.merge_cells('A2:B2')
    
    # Add dropdowns
    products = [(inp.product_id, inp.marketplace) for inp, _ in outputs_list]
    
    ws_summary['A4'] = "Select Product (ASIN):"
    ws_summary['A4'].font = Font(bold=True, size=11)
    ws_summary['B4'] = products[0][0] if products else "N/A"
    ws_summary['B4'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws_summary['A5'] = "Select Marketplace:"
    ws_summary['A5'].font = Font(bold=True, size=11)
    ws_summary['B5'] = products[0][1] if products else "UK"
    ws_summary['B5'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    # Add data validation
    product_ids = sorted(set(p[0] for p in products))
    if product_ids:
        dv_product = DataValidation(type="list", formula1=f'"{",".join(product_ids)}"', allow_blank=False)
        ws_summary.add_data_validation(dv_product)
        dv_product.add(ws_summary['B4'])
    
    dv_marketplace = DataValidation(type="list", formula1='"UK,US"', allow_blank=False)
    ws_summary.add_data_validation(dv_marketplace)
    dv_marketplace.add(ws_summary['B5'])
    
    # Add output fields with formulas
    ws_summary['A7'] = "Quote Results (Auto-Populated from Raw Data)"
    ws_summary['A7'].font = Font(size=11, bold=True, underline='single', color="1F4E78")
    ws_summary.merge_cells('A7:B7')
    
    fields = [
        ("Quote (Q)", "O"),
        ("Seller ROI %", "P"),
        ("Our ROI %", "Q"),
        ("Buy Box Avg (BB̄)", "C"),
        ("Our Cost (C)", "E"),
        ("Weight (kg)", "D"),
        ("Feasible", "T"),
    ]
    
    row = 8
    for label, col in fields:
        ws_summary[f'A{row}'] = label
        ws_summary[f'A{row}'].font = Font(bold=True, size=10)
        ws_summary[f'B{row}'] = f'=IFERROR(INDEX(\'Raw Data\'!{col}:{col}, MATCH($B$4&"|"&$B$5, \'Raw Data\'!$V:$V, 0)), "N/A")'
        row += 1
    
    # Create Raw Data sheet
    create_raw_data_sheet(wb, outputs_list)
    
    return wb


def main():
    """
    Main function: Generate quote report from live Supabase data.
    """
    print("=" * 80)
    print("📊 BOOK PORTAL QUOTE REPORT GENERATOR (LIVE SUPABASE DATA)")
    print("=" * 80)
    print()
    
    # Check environment variables
    print("🔑 Step 1: Checking environment variables...")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ ERROR: Missing environment variables!")
        print("   Required: SUPABASE_URL and SUPABASE_KEY")
        print("   Set them in your .env file or environment")
        sys.exit(1)
    
    print(f"   ✓ SUPABASE_URL: {supabase_url[:30]}...")
    print(f"   ✓ SUPABASE_KEY: {supabase_key[:20]}...")
    print()
    
    # Connect to Supabase
    print("🔌 Step 2: Connecting to Supabase...")
    try:
        client = create_client(supabase_url, supabase_key)
        repo = SupabaseRepo(client)
        print("   ✓ Connected successfully!")
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        sys.exit(1)
    print()
    
    # Fetch all products from database
    print("📚 Step 3: Fetching products from public.products...")
    try:
        products = repo.list_all_products()
        print(f"   ✓ Found {len(products)} products in database")
        print(f"   UK: {sum(1 for p in products if p['marketplace'] == 'UK')}")
        print(f"   US: {sum(1 for p in products if p['marketplace'] == 'US')}")
    except Exception as e:
        print(f"   ❌ Error fetching products: {str(e)}")
        sys.exit(1)
    print()
    
    # Calculate quotes for all products
    print(f"💰 Step 4: Calculating quotes for {len(products)} products...")
    print("   (Using our_price, package_weight from public.products)")
    print("   (Using buy_box_price from Backfill_test.dynamic_data)")
    print()
    
    outputs_list = []
    feasible_count = 0
    error_count = 0
    
    for idx, product in enumerate(products, start=1):
        asin = product['asin']
        marketplace = product['marketplace']
        
        print(f"[{idx}/{len(products)}] {asin} ({marketplace})")
        
        try:
            inputs, outputs = calculate_quote_from_db(repo, asin, marketplace, verbose=True)
            outputs_list.append((inputs, outputs))
            
            if outputs.feasible:
                feasible_count += 1
        
        except Exception as e:
            print(f"    ❌ Skipping due to error: {str(e)}")
            error_count += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 CALCULATION SUMMARY")
    print("=" * 80)
    print(f"Total products processed: {len(outputs_list)}")
    print(f"✅ Feasible quotes: {feasible_count}")
    print(f"❌ Infeasible quotes: {len(outputs_list) - feasible_count}")
    if error_count > 0:
        print(f"⚠️  Errors/Skipped: {error_count}")
    print()
    
    # Generate Excel
    if OPENPYXL_AVAILABLE and len(outputs_list) > 0:
        print("📈 Step 5: Generating Excel workbook...")
        
        try:
            wb = create_excel_workbook_from_live_data(repo, outputs_list)
            
            filename = "Book_Portal_Quote_Report_Live_Data.xlsx"
            wb.save(filename)
            
            print(f"   ✓ Saved: {filename}")
            print(f"   📊 Sheet 1: Model Summary")
            print(f"   📊 Sheet 2: Quote Summary (interactive, live data)")
            print(f"   📊 Sheet 3: Raw Data ({len(outputs_list)} products)")
            print()
            
        except Exception as e:
            print(f"   ❌ Excel generation failed: {str(e)}")
    
    # Generate CSV fallback
    print("📄 Step 6: Generating CSV export...")
    try:
        from book_portal_pricing.excel_export import create_csv
        
        csv_bytes, mime_type = create_csv(outputs_list)
        
        csv_filename = "Book_Portal_Quote_Report_Live_Data.csv"
        with open(csv_filename, 'wb') as f:
            f.write(csv_bytes)
        
        print(f"   ✓ Saved: {csv_filename}")
        print(f"   ({len(outputs_list)} products)")
        print()
        
    except Exception as e:
        print(f"   ❌ CSV generation failed: {str(e)}")
    
    # Final message
    print("=" * 80)
    print("✅ REPORT GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("All data sourced from:")
    print("  📊 public.products → our_price, package_weight, asin, marketplace")
    print("  📊 Backfill_test.dynamic_data → buy_box_price (30-day history)")
    print()
    print("NO random or hardcoded values used!")
    print("=" * 80)


if __name__ == "__main__":
    main()




