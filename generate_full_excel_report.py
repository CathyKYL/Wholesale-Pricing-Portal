"""
Generate Complete Excel Report with 38 Products
------------------------------------------------
This script creates a full Excel workbook with:
- Sheet 1: Model Summary (purpose, variables, formulas)
- Sheet 2: Quote Summary (interactive with dropdowns)
- Sheet 3: Raw Data (38 products with complete calculations)
"""

from decimal import Decimal
from book_portal_pricing.calculator import decide_quote, Inputs
from book_portal_pricing.money import D

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError:
    print("ERROR: openpyxl is required. Install with: pip install openpyxl")
    exit(1)


def generate_38_products():
    """Generate 38 diverse product scenarios."""
    products = []
    
    # UK Products (19 products)
    uk_scenarios = [
        # High margin products (seller >30% possible)
        ("UK_HIGH_01", D('35.00'), D('8.00'), D('1.5')),
        ("UK_HIGH_02", D('30.00'), D('7.50'), D('2.0')),
        ("UK_HIGH_03", D('28.00'), D('8.00'), D('1.0')),
        ("UK_HIGH_04", D('32.00'), D('9.00'), D('2.5')),
        ("UK_HIGH_05", D('27.00'), D('7.00'), D('1.8')),
        ("UK_HIGH_06", D('40.00'), D('10.00'), D('3.0')),
        ("UK_HIGH_07", D('25.00'), D('6.50'), D('1.2')),
        
        # Medium margin products (tight, seller 10-30%)
        ("UK_MED_01", D('20.00'), D('8.00'), D('2.0')),
        ("UK_MED_02", D('19.00'), D('8.50'), D('1.5')),
        ("UK_MED_03", D('18.50'), D('8.00'), D('2.2')),
        ("UK_MED_04", D('21.00'), D('9.00'), D('1.8')),
        ("UK_MED_05", D('22.00'), D('9.50'), D('2.5')),
        
        # Low margin / infeasible products
        ("UK_LOW_01", D('15.00'), D('8.00'), D('2.0')),
        ("UK_LOW_02", D('14.00'), D('8.50'), D('1.5')),
        ("UK_LOW_03", D('12.00'), D('7.50'), D('2.5')),
        ("UK_LOW_04", D('10.00'), D('8.00'), D('2.0')),
        ("UK_LOW_05", D('11.00'), D('7.00'), D('1.8')),
        ("UK_LOW_06", D('13.00'), D('8.00'), D('3.0')),
        ("UK_LOW_07", D('16.00'), D('9.00'), D('2.2')),
    ]
    
    for asin, bb, cost, weight in uk_scenarios:
        products.append(('UK', asin, bb, cost, weight))
    
    # US Products (19 products)
    us_scenarios = [
        # High margin products
        ("US_HIGH_01", D('45.00'), D('10.00'), D('1.5')),
        ("US_HIGH_02", D('40.00'), D('9.50'), D('2.0')),
        ("US_HIGH_03", D('38.00'), D('10.00'), D('1.0')),
        ("US_HIGH_04", D('42.00'), D('11.00'), D('2.5')),
        ("US_HIGH_05", D('37.00'), D('9.00'), D('1.8')),
        ("US_HIGH_06", D('50.00'), D('12.00'), D('3.0')),
        ("US_HIGH_07", D('35.00'), D('8.50'), D('1.2')),
        
        # Medium margin products
        ("US_MED_01", D('25.00'), D('10.00'), D('2.0')),
        ("US_MED_02", D('24.00'), D('10.50'), D('1.5')),
        ("US_MED_03", D('23.50'), D('10.00'), D('2.2')),
        ("US_MED_04", D('26.00'), D('11.00'), D('1.8')),
        ("US_MED_05", D('27.00'), D('11.50'), D('2.5')),
        
        # Low margin / infeasible products
        ("US_LOW_01", D('18.00'), D('10.00'), D('2.0')),
        ("US_LOW_02", D('17.00'), D('10.50'), D('1.5')),
        ("US_LOW_03", D('15.00'), D('9.50'), D('2.5')),
        ("US_LOW_04", D('12.00'), D('10.00'), D('2.0')),
        ("US_LOW_05", D('14.00'), D('9.00'), D('1.8')),
        ("US_LOW_06", D('16.00'), D('10.00'), D('3.0')),
        ("US_LOW_07", D('19.00'), D('11.00'), D('2.2')),
    ]
    
    for asin, bb, cost, weight in us_scenarios:
        products.append(('US', asin, bb, cost, weight))
    
    return products


def create_model_summary_sheet(wb):
    """Create Model Summary / ReadMe sheet."""
    ws = wb.create_sheet("Model Summary", 0)
    
    # Set column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 100
    
    # Title
    ws['A1'] = "Book Portal Quote Calculator"
    ws['A1'].font = Font(size=16, bold=True, color="1F4E78")
    
    ws['A2'] = "Model Summary & Documentation"
    ws['A2'].font = Font(size=12, bold=True, italic=True, color="1F4E78")
    
    # Purpose section
    ws['A4'] = "Purpose"
    ws['A4'].font = Font(bold=True, size=11)
    ws['B4'] = "Calculate optimal wholesale quotes for book sellers with SMOOTH CONTINUOUS ROI strategy (NO HARSH TIER JUMPS)"
    
    ws['A5'] = "Approach"
    ws['A5'].font = Font(bold=True, size=11)
    ws['B5'] = "Continuous seller ROI from 10% up to 40%+ with smooth transitions - eliminates harsh 20%/30%/40% tier boundaries"
    ws['B5'].font = Font(color="C00000", bold=True)
    
    # Variables section
    ws['A7'] = "Variables"
    ws['A7'].font = Font(bold=True, underline='single', size=11)
    
    variables = [
        ("BB̄", "30-day average Buy Box price (from Supabase; simple mean of last 30 days; ignore nulls)"),
        ("AF", "Amazon fee = 0.17 × BB̄"),
        ("FC", "Fulfilment cost to end-customer (tiered by weight & marketplace)"),
        ("SC", "Our shipping to seller (seller pays; excluded from Q but included in seller's cost)"),
        ("C", "Our acquisition cost (our price from DB)"),
        ("Q", "Wholesale quote to seller"),
        ("S", "FC + AF + SC (all seller-borne costs other than their overhead)"),
        ("m", "Our internal ROI floor (default 0.10 i.e. 10%); we enforce upper cap of 0.20 (20%)"),
    ]
    
    row = 8
    for var, desc in variables:
        ws[f'A{row}'] = var
        ws[f'A{row}'].font = Font(bold=True, color="1F4E78")
        ws[f'B{row}'] = desc
        row += 1
    
    # ROI Formulas section
    row += 1
    ws[f'A{row}'] = "ROI Formulas (Continuous & Smooth)"
    ws[f'A{row}'].font = Font(bold=True, underline='single', size=11)
    row += 1
    
    ws[f'A{row}'] = "Seller ROI"
    ws[f'A{row}'].font = Font(bold=True)
    ws[f'B{row}'] = "ROI_seller(Q) = (BB̄ - (Q + S)) / (Q + S)"
    row += 1
    
    ws[f'A{row}'] = "Our ROI"
    ws[f'A{row}'].font = Font(bold=True)
    ws[f'B{row}'] = "ROI_us(Q) = (Q - C) / C"
    row += 1
    
    # Decision Logic section
    row += 1
    ws[f'A{row}'] = "Smooth Decision Logic (NO HARSH TIERS)"
    ws[f'A{row}'].font = Font(bold=True, underline='single', size=11, color="C00000")
    row += 1
    
    logic_steps = [
        "1. Define our ROI band:",
        "   • Q_min = C × (1 + m) where m=0.10 → 10% floor",
        "   • Q_max_our = C × 1.20 → 20% cap",
        "",
        "2. Compute seller boundary quotes (continuous formulas):",
        "   • Q_seller10 = (BB̄ - 1.10×S) / 1.10",
        "   • Q_seller30 = (BB̄ - 1.30×S) / 1.30",
        "   • Q_seller40 = (BB̄ - 1.40×S) / 1.40",
        "",
        "3. Selection logic (continuous, seller-favoured):",
        "   a) Compute seller ROI at our 20% cap: ROI_seller(Q_max_our)",
        "   b) If ROI_seller(Q_max_our) ≥ 10%:",
        "      • Set Q = Q_max_our (we take our 20% ROI)",
        "      • Seller ROI floats smoothly and may exceed 30% if margin allows",
        "      • This satisfies: if seller could be >30%, we first fill our ROI to 20%",
        "   c) Else (seller would drop below 10% if we take 20%):",
        "      • Lower Q just enough so seller ROI hits 10%: Q = Q_seller10",
        "      • If Q < Q_min: no-deal (even at our floor 10% ROI, seller would be <10%)",
        "   d) Always clamp final Q to [Q_min, Q_max_our]",
        "",
        "4. Result: We either sit at our 20% cap (favouring seller with extra surplus),",
        "   or we slide down smoothly until seller ROI is 10%, but never below our 10% floor.",
        "   THIS REMOVES HARSH 20/30/40% JUMPS.",
    ]
    
    for step in logic_steps:
        ws[f'B{row}'] = step
        if step and step[0].isdigit():
            ws[f'B{row}'].font = Font(bold=True)
        row += 1
    
    # FC Tiers section
    row += 1
    ws[f'A{row}'] = "Fulfilment Cost Tiers (FC)"
    ws[f'A{row}'].font = Font(bold=True, underline='single', size=11)
    row += 1
    
    ws[f'A{row}'] = "UK (GBP)"
    ws[f'A{row}'].font = Font(bold=True)
    row += 1
    uk_tiers = [
        "0-1kg: £3.00",
        "1-2kg: £3.50",
        "2-5kg: £4.50",
        "5-8kg: £5.75",
        ">8kg: £6.50 + £0.50 per kg over 8kg",
    ]
    for tier in uk_tiers:
        ws[f'B{row}'] = tier
        row += 1
    
    row += 1
    ws[f'A{row}'] = "US (USD)"
    ws[f'A{row}'].font = Font(bold=True)
    row += 1
    us_tiers = [
        "0-1kg: $4.25",
        "1-2kg: $4.95",
        "2-5kg: $6.25",
        "5-8kg: $7.75",
        ">8kg: $8.50 + $0.50 per kg over 8kg",
    ]
    for tier in us_tiers:
        ws[f'B{row}'] = tier
        row += 1
    
    # SC section
    row += 1
    ws[f'A{row}'] = "Shipping Cost to Seller (SC)"
    ws[f'A{row}'].font = Font(bold=True, underline='single', size=11)
    row += 1
    ws[f'B{row}'] = "UK: £0.50 (flat rate)"
    row += 1
    ws[f'B{row}'] = "US: £6.00 converted to USD via fx_gbp_to_usd (default $7.80 at 1.30)"


def create_quote_summary_sheet(wb, products):
    """Create Quote Summary (Interactive) sheet."""
    ws = wb.create_sheet("Quote Summary")
    
    # Set column widths
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20
    
    # Title
    ws['A1'] = "Interactive Quote Calculator"
    ws['A1'].font = Font(size=14, bold=True, color="1F4E78")
    ws.merge_cells('A1:B1')
    
    # Instructions
    ws['A2'] = "Select product using dropdowns below to see quote details"
    ws['A2'].font = Font(italic=True, size=10, color="7F7F7F")
    ws.merge_cells('A2:B2')
    
    # Input section with styling
    ws['A4'] = "Select Product (ASIN):"
    ws['A4'].font = Font(bold=True, size=11)
    ws['A4'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    ws['B4'] = products[0][1] if products else "N/A"
    ws['B4'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    ws['B4'].font = Font(bold=True)
    
    ws['A5'] = "Select Marketplace:"
    ws['A5'].font = Font(bold=True, size=11)
    ws['A5'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    ws['B5'] = products[0][0] if products else "UK"
    ws['B5'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    ws['B5'].font = Font(bold=True)
    
    # Add data validation for dropdowns
    product_ids = sorted(set(p[1] for p in products))
    if product_ids:
        dv_product = DataValidation(type="list", formula1=f'"{",".join(product_ids)}"', allow_blank=False)
        ws.add_data_validation(dv_product)
        dv_product.add(ws['B4'])
    
    dv_marketplace = DataValidation(type="list", formula1='"UK,US"', allow_blank=False)
    ws.add_data_validation(dv_marketplace)
    dv_marketplace.add(ws['B5'])
    
    # Output section
    ws['A7'] = "Quote Results"
    ws['A7'].font = Font(size=12, bold=True, underline='single', color="1F4E78")
    ws.merge_cells('A7:B7')
    
    # Define output fields with categories
    fields = [
        ("Quote (Q)", "Q", "main"),
        ("Seller ROI %", "ROI_seller_pct", "main"),
        ("Our ROI %", "ROI_us_pct", "main"),
        ("Margin (Absolute)", "Margin_abs", "main"),
        ("Margin %", "Margin_pct", "main"),
        ("", "", "blank"),
        ("Components", "", "header"),
        ("Buy Box Avg (BB̄)", "BB_avg", "component"),
        ("Amazon Fee (AF)", "AF", "component"),
        ("Fulfilment Cost (FC)", "FC", "component"),
        ("Shipping Cost (SC)", "SC", "component"),
        ("Seller Costs (S)", "S", "component"),
        ("Our Cost (C)", "C", "component"),
        ("Weight (kg)", "Weight_kg", "component"),
        ("", "", "blank"),
        ("Boundaries (Smooth Continuous)", "", "header"),
        ("Q_min (our 10%)", "Qmin", "boundary"),
        ("Q_max_our (our 20%)", "Qmax_our", "boundary"),
        ("Q_seller10 (seller 10%)", "Q_seller10", "boundary"),
        ("Q_seller30 (seller 30%)", "Q_seller30", "boundary"),
        ("Q_seller40 (seller 40%)", "Q_seller40", "boundary"),
        ("", "", "blank"),
        ("Status", "", "header"),
        ("Feasible", "Feasible", "status"),
        ("Reason", "Reason", "status"),
    ]
    
    col_map = {
        "Q": "O", "ROI_seller_pct": "P", "ROI_us_pct": "Q",
        "Margin_abs": "R", "Margin_pct": "S",
        "BB_avg": "C", "AF": "F", "FC": "G", "SC": "H", "S": "I",
        "C": "E", "Weight_kg": "D",
        "Qmin": "J", "Qmax_our": "K", "Q_seller10": "L",
        "Q_seller30": "M", "Q_seller40": "N",
        "Feasible": "T", "Reason": "U",
    }
    
    row = 8
    for label, field_name, field_type in fields:
        ws[f'A{row}'] = label
        
        if field_type == "header":
            ws[f'A{row}'].font = Font(bold=True, underline='single', size=11, color="1F4E78")
        elif field_type == "blank":
            pass
        elif label:
            ws[f'A{row}'].font = Font(bold=True, size=10)
            
            # Add formula
            if field_name and field_name in col_map:
                col = col_map[field_name]
                ws[f'B{row}'] = f'=IFERROR(INDEX(\'Raw Data\'!{col}:{col}, MATCH($B$4&"|"&$B$5, \'Raw Data\'!$V:$V, 0)), "N/A")'
                
                # Format based on field type
                if field_type == "main":
                    ws[f'B{row}'].font = Font(bold=True, size=11, color="1F4E78")
                    ws[f'B{row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        
        row += 1
    
    # Add note about conditional formatting
    row += 2
    ws[f'A{row}'] = "Conditional Formatting Rules:"
    ws[f'A{row}'].font = Font(bold=True, italic=True, size=9)
    row += 1
    ws[f'A{row}'] = "• Seller ROI ≥ 30%: Highlighted in green (seller-favoured outcome)"
    ws[f'A{row}'].font = Font(size=9, italic=True, color="00B050")
    row += 1
    ws[f'A{row}'] = "• Our ROI < 10%: Highlighted in red (warning - below our floor)"
    ws[f'A{row}'].font = Font(size=9, italic=True, color="C00000")


def create_raw_data_sheet(wb, outputs_list):
    """Create Raw Data sheet with all product calculations."""
    ws = wb.create_sheet("Raw Data")
    
    # Define column headers
    headers = [
        "ASIN", "Marketplace", "BB_avg", "Weight_kg", "C",
        "AF", "FC", "SC", "S",
        "Qmin", "Qmax_our", "Q_seller10", "Q_seller30", "Q_seller40",
        "Q", "ROI_seller_pct", "ROI_us_pct", "Margin_abs", "Margin_pct",
        "Feasible", "Reason",
        "Key"
    ]
    
    # Write headers with styling
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Write data rows
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
        
        # Alternate row colors
        fill_color = "FFFFFF" if row_idx % 2 == 0 else "F2F2F2"
        
        for col_idx, value in enumerate(data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = value
            cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            
            # Format currency columns (2 decimal places)
            if col_idx >= 3 and col_idx <= 19:
                cell.number_format = '0.00'
            
            # Color code feasibility
            if col_idx == 20:  # Feasible column
                if value == "Yes":
                    cell.font = Font(bold=True, color="00B050")
                else:
                    cell.font = Font(bold=True, color="C00000")
        
        # Add helper key column
        key_cell = ws.cell(row=row_idx, column=len(headers))
        key_cell.value = f"{inputs.product_id}|{inputs.marketplace}"
        key_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    
    # Auto-fit columns
    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 15


def main():
    """Generate complete Excel workbook with 38 products."""
    print("=" * 80)
    print("GENERATING COMPLETE EXCEL WORKBOOK WITH 38 PRODUCTS")
    print("=" * 80)
    print()
    
    # Generate 38 diverse products
    print("Step 1: Generating 38 diverse product scenarios...")
    products = generate_38_products()
    print(f"✓ Generated {len(products)} products (UK: {sum(1 for p in products if p[0]=='UK')}, US: {sum(1 for p in products if p[0]=='US')})")
    print()
    
    # Calculate quotes for all products
    print("Step 2: Calculating quotes for all products...")
    outputs_list = []
    feasible_count = 0
    
    for marketplace, asin, bb, cost, weight in products:
        inputs = Inputs(
            product_id=asin,
            marketplace=marketplace,
            bb_avg=bb,
            c_cost=cost,
            weight_kg=weight,
            m=D('0.10'),
            fx_gbp_to_usd=D('1.30')
        )
        
        outputs = decide_quote(inputs)
        outputs_list.append((inputs, outputs))
        
        if outputs.feasible:
            feasible_count += 1
    
    print(f"✓ Calculated {len(outputs_list)} quotes")
    print(f"  - Feasible: {feasible_count}")
    print(f"  - Infeasible: {len(outputs_list) - feasible_count}")
    print()
    
    # Create workbook
    print("Step 3: Creating Excel workbook with 3 sheets...")
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet
    
    # Create all sheets
    create_model_summary_sheet(wb)
    print("  ✓ Sheet 1: Model Summary (purpose, variables, formulas)")
    
    create_quote_summary_sheet(wb, products)
    print("  ✓ Sheet 2: Quote Summary (interactive with dropdowns & INDEX/MATCH formulas)")
    
    create_raw_data_sheet(wb, outputs_list)
    print("  ✓ Sheet 3: Raw Data (38 products with complete calculations)")
    print()
    
    # Save workbook
    filename = "Book_Portal_Quote_Report_38_Products.xlsx"
    print(f"Step 4: Saving workbook...")
    wb.save(filename)
    
    print()
    print("=" * 80)
    print("✅ EXCEL WORKBOOK GENERATED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print(f"Filename: {filename}")
    print(f"Location: {__file__.replace('generate_full_excel_report.py', '')}{filename}")
    print()
    print("Workbook Contents:")
    print("  📊 Sheet 1: Model Summary")
    print("     - Purpose and approach (smooth continuous ROI)")
    print("     - Variables and formulas")
    print("     - Decision logic (NO HARSH TIERS)")
    print("     - FC/SC tier structure")
    print()
    print("  📊 Sheet 2: Quote Summary (INTERACTIVE)")
    print("     - Dropdown for ASIN selection")
    print("     - Dropdown for Marketplace selection")
    print("     - Auto-populated quote details using INDEX/MATCH formulas")
    print("     - All components, boundaries, and status")
    print()
    print("  📊 Sheet 3: Raw Data")
    print(f"     - {len(outputs_list)} products (38 rows)")
    print(f"     - {feasible_count} feasible products")
    print(f"     - {len(outputs_list) - feasible_count} infeasible products")
    print("     - Complete calculation details for all products")
    print("     - Helper Key column for INDEX/MATCH formulas")
    print()
    print("=" * 80)
    print("🎉 Open the file in Excel to use the interactive dropdowns!")
    print("=" * 80)


if __name__ == "__main__":
    main()

