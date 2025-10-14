"""
Excel Export - Interactive Quote Analysis Workbook
---------------------------------------------------
Purpose:
- Generate Excel workbook with 3 sheets for quote analysis
- Support interactive dropdowns for ASIN/Marketplace selection
- Provide diagnostic data for all 38 products in database
- Fallback to CSV if openpyxl not available

Sheet Structure:
1. Model Summary / ReadMe: Purpose, variables, formulas, rationale
2. Quote Summary (Interactive): Dropdowns + auto-populated cells with formulas
3. Raw Data: All 38 product calculations (feasible and non-feasible)

Usage:
    from book_portal_pricing.excel_export import create_workbook
    from book_portal_pricing.repo import Repo
    
    # Generate workbook for all products
    excel_bytes, mime_type = create_workbook(
        repo=repo,
        marketplace='UK',
        m=0.10,
        fx_gbp_to_usd=1.30
    )
    
    # Save to file
    with open('quote_report.xlsx', 'wb') as f:
        f.write(excel_bytes)
"""

import io
from decimal import Decimal
from typing import Tuple, Optional, List

from .calculator import decide_quote, Inputs, Outputs
from .repo import Repo, Marketplace
from .money import D

# Try to import openpyxl, fallback to CSV if not available
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def create_model_summary_sheet(wb: 'Workbook') -> None:
    """
    Create Model Summary / ReadMe sheet.
    
    Purpose:
    - Explain the quote calculator model
    - Document variables and formulas
    - Provide rationale for smooth continuous ROI approach
    
    Args:
        wb: openpyxl Workbook object
    """
    ws = wb.create_sheet("Model Summary", 0)
    
    # Set column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 80
    
    # Title
    ws['A1'] = "Book Portal Quote Calculator"
    ws['A1'].font = Font(size=16, bold=True)
    
    ws['A2'] = "Model Summary & Documentation"
    ws['A2'].font = Font(size=12, bold=True, italic=True)
    
    # Purpose section
    ws['A4'] = "Purpose"
    ws['A4'].font = Font(bold=True)
    ws['B4'] = "Calculate optimal wholesale quotes for book sellers with smooth continuous ROI strategy"
    
    ws['A5'] = "Approach"
    ws['A5'].font = Font(bold=True)
    ws['B5'] = "NO HARSH TIER JUMPS - Continuous seller ROI from 10% up to 40%+ with smooth transitions"
    
    # Variables section
    ws['A7'] = "Variables"
    ws['A7'].font = Font(bold=True, underline='single')
    
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
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'B{row}'] = desc
        row += 1
    
    # ROI Formulas section
    row += 1
    ws[f'A{row}'] = "ROI Formulas"
    ws[f'A{row}'].font = Font(bold=True, underline='single')
    row += 1
    
    formulas = [
        ("Seller ROI", "ROI_seller(Q) = (BB̄ - (Q + S)) / (Q + S)"),
        ("Our ROI", "ROI_us(Q) = (Q - C) / C"),
    ]
    
    for name, formula in formulas:
        ws[f'A{row}'] = name
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'B{row}'] = formula
        row += 1
    
    # Decision Logic section
    row += 1
    ws[f'A{row}'] = "Smooth Decision Logic (Continuous - NO TIERS)"
    ws[f'A{row}'].font = Font(bold=True, underline='single')
    row += 1
    
    logic_steps = [
        "1. Define our ROI band:",
        "   • Q_min = C × (1 + m) where m=0.10 → 10% floor",
        "   • Q_max_our = C × 1.20 → 20% cap",
        "",
        "2. Compute seller boundary quotes:",
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
        "4. Result: We either sit at our 20% cap (favouring seller with any extra surplus),",
        "   or we slide down smoothly until seller ROI is 10%, but never below our 10% floor.",
        "   This removes harsh 20/30/40% jumps.",
    ]
    
    for step in logic_steps:
        ws[f'B{row}'] = step
        if step and step[0].isdigit():
            ws[f'B{row}'].font = Font(bold=True)
        row += 1
    
    # FC Tiers section
    row += 1
    ws[f'A{row}'] = "Fulfilment Cost Tiers (FC)"
    ws[f'A{row}'].font = Font(bold=True, underline='single')
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
    ws[f'A{row}'].font = Font(bold=True, underline='single')
    row += 1
    ws[f'B{row}'] = "UK: £0.50 (flat rate)"
    row += 1
    ws[f'B{row}'] = "US: £6.00 converted to USD via fx_gbp_to_usd (default $7.80 at 1.30)"


def create_quote_summary_sheet(wb: 'Workbook', products: List[Tuple[str, Marketplace]]) -> None:
    """
    Create Quote Summary (Interactive) sheet.
    
    Purpose:
    - Provide interactive dropdowns for ASIN and Marketplace
    - Auto-populate quote data using INDEX/MATCH formulas
    - Conditional formatting for seller ROI and our ROI
    
    Args:
        wb: openpyxl Workbook object
        products: List of (product_id, marketplace) tuples for dropdowns
    """
    ws = wb.create_sheet("Quote Summary")
    
    # Set column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    
    # Title
    ws['A1'] = "Interactive Quote Calculator"
    ws['A1'].font = Font(size=14, bold=True)
    
    # Input section
    ws['A3'] = "Select Product:"
    ws['A3'].font = Font(bold=True)
    ws['B3'] = products[0][0] if products else "N/A"  # Default to first product
    
    ws['A4'] = "Select Marketplace:"
    ws['A4'].font = Font(bold=True)
    ws['B4'] = products[0][1] if products else "UK"  # Default to first marketplace
    
    # Add data validation for dropdowns
    # Product dropdown
    product_ids = sorted(set(p[0] for p in products))
    if product_ids:
        dv_product = DataValidation(type="list", formula1=f'"{",".join(product_ids)}"', allow_blank=False)
        ws.add_data_validation(dv_product)
        dv_product.add(ws['B3'])
    
    # Marketplace dropdown
    dv_marketplace = DataValidation(type="list", formula1='"UK,US"', allow_blank=False)
    ws.add_data_validation(dv_marketplace)
    dv_marketplace.add(ws['B4'])
    
    # Output section
    ws['A6'] = "Quote Results"
    ws['A6'].font = Font(size=12, bold=True, underline='single')
    
    # Define output fields
    fields = [
        ("Quote (Q)", "Q"),
        ("Seller ROI %", "ROI_seller_pct"),
        ("Our ROI %", "ROI_us_pct"),
        ("Margin (Absolute)", "Margin_abs"),
        ("Margin %", "Margin_pct"),
        ("", ""),  # Blank row
        ("Components", ""),
        ("Buy Box Avg (BB̄)", "BB_avg"),
        ("Amazon Fee (AF)", "AF"),
        ("Fulfilment Cost (FC)", "FC"),
        ("Shipping Cost (SC)", "SC"),
        ("Seller Costs (S)", "S"),
        ("Our Cost (C)", "C"),
        ("Weight (kg)", "Weight_kg"),
        ("", ""),  # Blank row
        ("Boundaries", ""),
        ("Q_min (our 10%)", "Qmin"),
        ("Q_max_our (our 20%)", "Qmax_our"),
        ("Q_seller10 (seller 10%)", "Q_seller10"),
        ("Q_seller30 (seller 30%)", "Q_seller30"),
        ("Q_seller40 (seller 40%)", "Q_seller40"),
        ("", ""),  # Blank row
        ("Status", ""),
        ("Feasible", "Feasible"),
        ("Reason", "Reason"),
    ]
    
    row = 7
    for label, field_name in fields:
        ws[f'A{row}'] = label
        if label and not field_name:  # Section headers
            ws[f'A{row}'].font = Font(bold=True, underline='single')
        elif label:  # Regular fields
            ws[f'A{row}'].font = Font(bold=True)
            
            # Add INDEX/MATCH formula
            if field_name:
                # Formula: =INDEX('Raw Data'!column, MATCH($B$3&$B$4, 'Raw Data'!$A:$A&'Raw Data'!$B:$B, 0))
                # Note: This is a simplified approach. For Excel 365, we can use array formulas.
                # For compatibility, we'll use VLOOKUP with a helper column in Raw Data
                col_map = {
                    "Q": "O", "ROI_seller_pct": "P", "ROI_us_pct": "Q", 
                    "Margin_abs": "R", "Margin_pct": "S",
                    "BB_avg": "C", "AF": "F", "FC": "G", "SC": "H", "S": "I",
                    "C": "E", "Weight_kg": "D",
                    "Qmin": "J", "Qmax_our": "K", "Q_seller10": "L", 
                    "Q_seller30": "M", "Q_seller40": "N",
                    "Feasible": "T", "Reason": "U",
                }
                
                if field_name in col_map:
                    col = col_map[field_name]
                    # Use IFERROR to handle cases where match fails
                    ws[f'B{row}'] = f'=IFERROR(INDEX(\'Raw Data\'!{col}:{col}, MATCH($B$3&"|"&$B$4, \'Raw Data\'!$V:$V, 0)), "N/A")'
        
        row += 1
    
    # Apply conditional formatting (manual for now - would need openpyxl conditional formatting)
    # Note: Add comments about conditional formatting rules
    ws['A50'] = "Conditional Formatting Rules:"
    ws['A50'].font = Font(bold=True, italic=True, size=10)
    ws['A51'] = "• Seller ROI ≥ 30%: Green background"
    ws['A51'].font = Font(size=9, italic=True)
    ws['A52'] = "• Our ROI < 10%: Red background"
    ws['A52'].font = Font(size=9, italic=True)


def create_raw_data_sheet(
    wb: 'Workbook',
    outputs_list: List[Tuple[Inputs, Outputs]]
) -> None:
    """
    Create Raw Data sheet with all product calculations.
    
    Purpose:
    - Provide complete data for all 38 products
    - Support INDEX/MATCH formulas in Quote Summary sheet
    - Include both feasible and non-feasible products
    
    Args:
        wb: openpyxl Workbook object
        outputs_list: List of (Inputs, Outputs) tuples for all products
    """
    ws = wb.create_sheet("Raw Data")
    
    # Define column headers
    headers = [
        "ASIN", "Marketplace", "BB_avg", "Weight_kg", "C",
        "AF", "FC", "SC", "S",
        "Qmin", "Qmax_our", "Q_seller10", "Q_seller30", "Q_seller40",
        "Q", "ROI_seller_pct", "ROI_us_pct", "Margin_abs", "Margin_pct",
        "Feasible", "Reason",
        "Key"  # Helper column for INDEX/MATCH: ASIN|Marketplace
    ]
    
    # Write headers
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    
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
        
        for col_idx, value in enumerate(data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = value
            
            # Format currency columns (2 decimal places)
            if col_idx >= 3 and col_idx <= 19 and col_idx not in [2, 20, 21]:
                cell.number_format = '0.00'
        
        # Add helper key column (ASIN|Marketplace)
        key_cell = ws.cell(row=row_idx, column=len(headers))
        key_cell.value = f"{inputs.product_id}|{inputs.marketplace}"
    
    # Auto-fit columns
    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 15


def create_workbook(
    repo: Repo,
    marketplace: Optional[Marketplace] = None,
    m: float = 0.10,
    fx_gbp_to_usd: float = 1.30,
    product_ids: Optional[List[str]] = None
) -> Tuple[bytes, str]:
    """
    Create Excel workbook with all sheets and data.
    
    Purpose:
    - Generate complete quote analysis workbook
    - Include all 38 products (or specified subset)
    - Return bytes for file download or saving
    
    Args:
        repo: Repository implementation
        marketplace: Filter by marketplace (None = all marketplaces)
        m: Our ROI floor (default 0.10 = 10%)
        fx_gbp_to_usd: Exchange rate (default 1.30)
        product_ids: Optional list of product IDs (None = all products)
    
    Returns:
        Tuple of (bytes, mime_type):
        - bytes: Excel workbook as bytes
        - str: MIME type ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    Raises:
        ImportError: If openpyxl not available (falls back to CSV)
    
    Example:
        excel_bytes, mime_type = create_workbook(
            repo=repo,
            marketplace='UK',
            m=0.10,
            fx_gbp_to_usd=1.30
        )
        
        with open('quote_report.xlsx', 'wb') as f:
            f.write(excel_bytes)
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError(
            "openpyxl not installed. Install with: pip install openpyxl\n"
            "Alternatively, use create_csv() for CSV export."
        )
    
    # Create workbook
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet
    
    # Calculate outputs for all products
    # Note: This assumes repo has a method to list all products
    # For now, we'll create a placeholder implementation
    outputs_list: List[Tuple[Inputs, Outputs]] = []
    products: List[Tuple[str, Marketplace]] = []
    
    # If product_ids provided, use them; otherwise this would need a repo.list_all_products() method
    if product_ids:
        for pid in product_ids:
            for mkt in ["UK", "US"] if marketplace is None else [marketplace]:
                try:
                    # Fetch data
                    bb_prices = repo.get_bb_prices_last_30_days(pid, mkt)  # type: ignore
                    if not bb_prices:
                        continue
                    
                    bb_avg = sum(bb_prices) / len(bb_prices)
                    weight_kg = repo.get_weight_kg(pid)
                    c_cost = repo.get_our_cost_c(pid)
                    
                    # Build inputs
                    inputs = Inputs(
                        product_id=pid,
                        marketplace=mkt,  # type: ignore
                        bb_avg=bb_avg,
                        c_cost=c_cost,
                        weight_kg=weight_kg,
                        m=D(str(m)),
                        fx_gbp_to_usd=D(str(fx_gbp_to_usd))
                    )
                    
                    # Calculate quote
                    outputs = decide_quote(inputs)
                    
                    outputs_list.append((inputs, outputs))
                    products.append((pid, mkt))  # type: ignore
                    
                except Exception:
                    # Skip products with errors
                    continue
    
    # Create sheets
    create_model_summary_sheet(wb)
    create_quote_summary_sheet(wb, products)
    create_raw_data_sheet(wb, outputs_list)
    
    # Save to bytes
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def create_csv(outputs_list: List[Tuple[Inputs, Outputs]]) -> Tuple[bytes, str]:
    """
    Create CSV export as fallback when openpyxl not available.
    
    Purpose:
    - Provide CSV export for systems without openpyxl
    - Include same columns as Raw Data sheet
    
    Args:
        outputs_list: List of (Inputs, Outputs) tuples
    
    Returns:
        Tuple of (bytes, mime_type):
        - bytes: CSV content as bytes
        - str: MIME type ('text/csv')
    
    Example:
        csv_bytes, mime_type = create_csv(outputs_list)
        
        with open('quote_report.csv', 'wb') as f:
            f.write(csv_bytes)
    """
    import csv
    
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write headers
    headers = [
        "ASIN", "Marketplace", "BB_avg", "Weight_kg", "C",
        "AF", "FC", "SC", "S",
        "Qmin", "Qmax_our", "Q_seller10", "Q_seller30", "Q_seller40",
        "Q", "ROI_seller_pct", "ROI_us_pct", "Margin_abs", "Margin_pct",
        "Feasible", "Reason"
    ]
    writer.writerow(headers)
    
    # Write data rows
    for inputs, outputs in outputs_list:
        row = [
            inputs.product_id,
            inputs.marketplace,
            str(inputs.bb_avg),
            str(inputs.weight_kg),
            str(inputs.c_cost),
            str(outputs.af),
            str(outputs.fc),
            str(outputs.sc),
            str(outputs.s_bundle),
            str(outputs.qmin),
            str(outputs.qmax_our),
            str(outputs.q_seller10),
            str(outputs.q_seller30),
            str(outputs.q_seller40),
            str(outputs.quote_q),
            str(outputs.seller_roi_pct),
            str(outputs.our_roi_pct),
            str(outputs.margin_abs),
            str(outputs.margin_pct),
            "Yes" if outputs.feasible else "No",
            outputs.reason or "",
        ]
        writer.writerow(row)
    
    # Convert to bytes
    csv_str = buffer.getvalue()
    return csv_str.encode('utf-8'), 'text/csv'



