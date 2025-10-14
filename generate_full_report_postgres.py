"""
Generate Full Quote Report Using PostgreSQL Direct Connection
--------------------------------------------------------------
Purpose:
- Generate complete Excel quote report using PostgreSQL (no API key needed)
- Pull all 38 products from public.catalog_rows
- Fetch Buy Box history from backfill_test.dynamic_data
- 100% live database data

Usage:
    python generate_full_report_postgres.py
    
Environment Variables Required:
    DATABASE_URL - Your PostgreSQL connection string (already in your .env)
"""

import os
import sys
from decimal import Decimal

# Load .env file
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

from book_portal_pricing.postgres_repo import PostgresRepo
from book_portal_pricing.calculator import decide_quote, Inputs
from book_portal_pricing.money import D

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("⚠ WARNING: openpyxl not installed. Install with: pip install openpyxl")


def create_excel_report(outputs_list):
    """Create Excel workbook with all data."""
    wb = Workbook()
    wb.remove(wb.active)
    
    # Import sheet creators
    from book_portal_pricing.excel_export import create_model_summary_sheet
    
    # Sheet 1: Model Summary
    create_model_summary_sheet(wb)
    
    # Sheet 2: Quote Summary (Interactive)
    ws_summary = wb.create_sheet("Quote Summary")
    ws_summary.column_dimensions['A'].width = 30
    ws_summary.column_dimensions['B'].width = 20
    
    products = [(inp.product_id, inp.marketplace) for inp, _ in outputs_list]
    
    ws_summary['A1'] = "Interactive Quote Calculator (LIVE POSTGRESQL DATA)"
    ws_summary['A1'].font = Font(size=14, bold=True, color="1F4E78")
    ws_summary.merge_cells('A1:B1')
    
    ws_summary['A2'] = "All data from PostgreSQL (catalog_rows + backfill_test.dynamic_data)"
    ws_summary['A2'].font = Font(italic=True, size=9, color="00B050")
    ws_summary.merge_cells('A2:B2')
    
    # Dropdowns
    ws_summary['A4'] = "Select Product (ASIN):"
    ws_summary['A4'].font = Font(bold=True)
    ws_summary['B4'] = products[0][0] if products else "N/A"
    ws_summary['B4'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws_summary['A5'] = "Select Marketplace:"
    ws_summary['A5'].font = Font(bold=True)
    ws_summary['B5'] = products[0][1] if products else "UK"
    ws_summary['B5'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    # Data validation
    product_ids = sorted(set(p[0] for p in products))
    if product_ids:
        dv_product = DataValidation(type="list", formula1=f'"{",".join(product_ids)}"', allow_blank=False)
        ws_summary.add_data_validation(dv_product)
        dv_product.add(ws_summary['B4'])
    
    dv_marketplace = DataValidation(type="list", formula1='"UK,US"', allow_blank=False)
    ws_summary.add_data_validation(dv_marketplace)
    dv_marketplace.add(ws_summary['B5'])
    
    # Output fields
    ws_summary['A7'] = "Quote Results (Auto-Populated)"
    ws_summary['A7'].font = Font(size=11, bold=True, underline='single', color="1F4E78")
    
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
        ws_summary[f'A{row}'].font = Font(bold=True)
        ws_summary[f'B{row}'] = f'=IFERROR(INDEX(\'Raw Data\'!{col}:{col}, MATCH($B$4&"|"&$B$5, \'Raw Data\'!$V:$V, 0)), "N/A")'
        row += 1
    
    # Sheet 3: Raw Data
    ws_data = wb.create_sheet("Raw Data")
    
    headers = [
        "ASIN", "Marketplace", "BB_avg", "Weight_kg", "C",
        "AF", "FC", "SC", "S",
        "Qmin", "Qmax_our", "Q_seller10", "Q_seller30", "Q_seller40",
        "Q", "ROI_seller_pct", "ROI_us_pct", "Margin_abs", "Margin_pct",
        "Feasible", "Reason",
        "Key"
    ]
    
    # Headers
    for col_idx, header in enumerate(headers, start=1):
        cell = ws_data.cell(row=1, column=col_idx)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Data rows
    for row_idx, (inputs, outputs) in enumerate(outputs_list, start=2):
        data = [
            inputs.product_id,
            inputs.marketplace,
            float(inputs.bb_avg),
            float(inputs.weight_kg),
            float(inputs.c_cost),
            float(outputs.af),
            float(outputs.fc),
            float(outputs.sc),
            float(outputs.s_bundle),
            float(outputs.qmin),
            float(outputs.qmax_our),
            float(outputs.q_seller10),
            float(outputs.q_seller30),
            float(outputs.q_seller40),
            float(outputs.quote_q),
            float(outputs.seller_roi_pct),
            float(outputs.our_roi_pct),
            float(outputs.margin_abs),
            float(outputs.margin_pct),
            "Yes" if outputs.feasible else "No",
            outputs.reason or "",
        ]
        
        fill_color = "FFFFFF" if row_idx % 2 == 0 else "F2F2F2"
        
        for col_idx, value in enumerate(data, start=1):
            cell = ws_data.cell(row=row_idx, column=col_idx)
            cell.value = value
            cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            
            if col_idx >= 3 and col_idx <= 19:
                cell.number_format = '0.00'
            
            if col_idx == 20:
                if value == "Yes":
                    cell.font = Font(bold=True, color="00B050")
                else:
                    cell.font = Font(bold=True, color="C00000")
        
        # Key column
        key_cell = ws_data.cell(row=row_idx, column=len(headers))
        key_cell.value = f"{inputs.product_id}|{inputs.marketplace}"
        key_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    
    # Auto-fit columns
    for col_idx in range(1, len(headers) + 1):
        ws_data.column_dimensions[get_column_letter(col_idx)].width = 15
    
    return wb


def main():
    """Generate full report."""
    print("=" * 80)
    print("📊 BOOK PORTAL QUOTE REPORT - POSTGRESQL (ALL 38 PRODUCTS)")
    print("=" * 80)
    print()
    
    # Check DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in .env")
        sys.exit(1)
    
    print(f"✓ DATABASE_URL: {database_url[:50]}...")
    print()
    
    # Connect
    print("🔌 Step 1: Connecting to PostgreSQL...")
    try:
        repo = PostgresRepo(database_url)
        print("   ✓ Connected successfully!")
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        sys.exit(1)
    print()
    
    # Fetch products
    print("📚 Step 2: Fetching all products from public.catalog_rows...")
    try:
        products = repo.list_all_products()
        print(f"   ✓ Found {len(products)} products")
        uk_count = sum(1 for p in products if p['marketplace'] == 'UK')
        us_count = sum(1 for p in products if p['marketplace'] == 'US')
        print(f"   UK: {uk_count}, US: {us_count}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        sys.exit(1)
    print()
    
    # Calculate quotes
    print(f"💰 Step 3: Calculating quotes for {len(products)} products...")
    print()
    
    outputs_list = []
    feasible_count = 0
    error_count = 0
    
    for idx, product in enumerate(products, start=1):
        asin = product['asin']
        marketplace = product['marketplace']
        
        print(f"[{idx}/{len(products)}] {asin} ({marketplace})", end=" ")
        
        try:
            # Fetch data
            bb_avg = repo.get_avg_bb_price(asin, marketplace)
            c_cost = repo.get_our_cost_c(asin, marketplace)
            weight_kg = repo.get_weight_kg(asin, marketplace)
            
            # Build inputs
            inputs = Inputs(
                product_id=asin,
                marketplace=marketplace,
                bb_avg=bb_avg,
                c_cost=c_cost,
                weight_kg=weight_kg,
                m=D('0.10'),
                fx_gbp_to_usd=D('1.30')
            )
            
            # Calculate
            outputs = decide_quote(inputs)
            outputs_list.append((inputs, outputs))
            
            if outputs.feasible:
                feasible_count += 1
                print(f"✅ Q={outputs.quote_q} | Seller ROI={outputs.seller_roi_pct}% | Our ROI={outputs.our_roi_pct}%")
            else:
                print(f"❌ {outputs.reason}")
        
        except Exception as e:
            error_count += 1
            print(f"⚠️  Error: {str(e)}")
    
    print()
    print("=" * 80)
    print("📊 CALCULATION SUMMARY")
    print("=" * 80)
    print(f"Total products: {len(outputs_list)}")
    print(f"✅ Feasible: {feasible_count}")
    print(f"❌ Infeasible: {len(outputs_list) - feasible_count}")
    if error_count > 0:
        print(f"⚠️  Errors: {error_count}")
    print()
    
    # Generate Excel
    if OPENPYXL_AVAILABLE and len(outputs_list) > 0:
        print("📈 Step 4: Generating Excel workbook...")
        
        try:
            wb = create_excel_report(outputs_list)
            
            filename = "Book_Portal_Quote_Report_PostgreSQL_38_Products.xlsx"
            wb.save(filename)
            
            print(f"   ✓ Saved: {filename}")
            print(f"   📊 Sheet 1: Model Summary")
            print(f"   📊 Sheet 2: Quote Summary (interactive)")
            print(f"   📊 Sheet 3: Raw Data ({len(outputs_list)} products)")
            print()
        
        except Exception as e:
            print(f"   ❌ Excel generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # CSV fallback
    print("📄 Step 5: Generating CSV export...")
    try:
        from book_portal_pricing.excel_export import create_csv
        
        csv_bytes, _ = create_csv(outputs_list)
        
        csv_filename = "Book_Portal_Quote_Report_PostgreSQL_38_Products.csv"
        with open(csv_filename, 'wb') as f:
            f.write(csv_bytes)
        
        print(f"   ✓ Saved: {csv_filename}")
        print()
    
    except Exception as e:
        print(f"   ❌ CSV generation failed: {str(e)}")
    
    # Final summary
    print("=" * 80)
    print("✅ REPORT GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("All data sourced from:")
    print("  📊 public.catalog_rows → our_price, package_weight, asin, marketplace")
    print("  📊 backfill_test.dynamic_data → current_buybox_price (30-day history)")
    print()
    print("✨ NO SUPABASE API KEY NEEDED - Direct PostgreSQL Connection!")
    print("=" * 80)


if __name__ == "__main__":
    main()

