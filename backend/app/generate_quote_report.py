"""
Book Portal Quote Report Generator
-----------------------------------
Purpose:
- Generate comprehensive Excel report for all products in database
- Each product is processed with its specified marketplace (UK or US)
- No duplication - exactly one quote per product record
- Create interactive Summary sheet with dropdowns
- Create Raw Data sheet with all calculations

Usage:
    python generate_quote_report.py
    python generate_quote_report.py --fx 1.30 --m 0.10
    python generate_quote_report.py --output Book_Portal_Quote_Report_Fixed.xlsx
    python generate_quote_report.py --csv-only  # Generate CSV instead
    
Note:
    Each record in catalog_rows already has its marketplace specified.
    The script processes each product exactly once (no synthetic duplication).
"""

import sys
from pathlib import Path
import argparse
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
import csv

# Add pricing module to path
sys.path.insert(0, str(Path(__file__).parent))

from pricing.calculator import decide_quote, Inputs, Outputs
from pricing.repo import SupabaseRepo
from pricing.money import D
from db import SessionLocal
from sqlalchemy import text


def fetch_all_products(session) -> List[Dict[str, Any]]:
    """
    Fetch all products from database WITH their marketplace
    -------------------------------------------------------
    Each product already has its marketplace specified in the database.
    Returns list of products with ASIN, marketplace, and basic info.
    
    Returns:
        List of dicts with product information (one per ASIN + marketplace combo)
    """
    print("📊 Fetching products from database...")
    
    # Query all products with their marketplace
    # Each row in catalog_rows already has a marketplace (UK or US)
    # We process each record exactly once
    query = text("""
        SELECT 
            asin,
            marketplace,
            title,
            package_weight,
            our_price
        FROM catalog_rows
        WHERE asin IS NOT NULL
          AND marketplace IS NOT NULL
          AND package_weight IS NOT NULL
          AND our_price IS NOT NULL
        ORDER BY asin, marketplace
    """)
    
    result = session.execute(query)
    products = []
    
    for row in result.fetchall():
        products.append({
            'asin': row[0],
            'marketplace': row[1],  # NEW: Get marketplace from database
            'title': row[2],
            'weight_lbs': row[3],
            'our_price': row[4]
        })
    
    print(f"✅ Found {len(products)} products (each with specified marketplace)")
    return products


def calculate_all_quotes(repo, products: List[Dict], 
                        fx_gbp_to_usd: float = 1.30, m: float = 0.0) -> List[Dict]:
    """
    Calculate quotes for all products (each with its specified marketplace)
    -----------------------------------------------------------------------
    Each product already has its marketplace from the database.
    We process each product exactly once.
    
    Args:
        repo: Repository instance
        products: List of product dicts (each has asin + marketplace)
        fx_gbp_to_usd: Exchange rate
        m: Our margin target
    
    Returns:
        List of dicts with all calculation results
    """
    print(f"\n💰 Calculating quotes for {len(products)} products...")
    
    results = []
    total = len(products)
    
    for current, product in enumerate(products, 1):
        asin = product['asin']
        marketplace = product['marketplace']  # Get marketplace from product (not looping)
        
        print(f"  [{current}/{total}] {asin} ({marketplace})...", end='')
        
        try:
            # Get buy box prices
            bb_prices = repo.get_bb_prices_last_30_days(asin, marketplace)
            
            if not bb_prices or len(bb_prices) == 0:
                print(" ⚠️  No buy box data")
                # Create a result with no data
                results.append({
                    'asin': asin,
                    'title': product.get('title', ''),
                    'marketplace': marketplace,
                    'error': 'No buy box data available',
                    'feasible': False
                })
                continue
            
            # Calculate average
            bb_avg = sum(bb_prices) / Decimal(str(len(bb_prices)))
            
            # Get weight (convert lbs to kg)
            weight_lbs = D(str(product['weight_lbs']))
            weight_kg = weight_lbs * D('0.453592')
            
            # Get cost
            c_cost = D(str(product['our_price']))
            
            # Create inputs
            inputs = Inputs(
                product_id=asin,
                marketplace=marketplace,
                bb_avg=bb_avg,
                c_cost=c_cost,
                weight_kg=weight_kg,
                m=D(str(m)),
                fx_gbp_to_usd=D(str(fx_gbp_to_usd))
            )
            
            # Calculate quote
            outputs = decide_quote(inputs)
            
            # Build result dict
            result = {
                # Identifiers
                'asin': asin,
                'title': product.get('title', '')[:50],  # Truncate long titles
                'marketplace': marketplace,
                
                # Inputs
                'weight_kg': float(weight_kg),
                'bb_avg': float(bb_avg),
                'c_cost': float(c_cost),
                'm': float(inputs.m),
                'fx_gbp_to_usd': float(inputs.fx_gbp_to_usd),
                
                # Components
                'af': float(outputs.af),
                'fc': float(outputs.fc),
                'sc': float(outputs.sc),
                's_bundle': float(outputs.s_bundle),
                
                # Bounds
                'qmin': float(outputs.qmin),
                'qmax_20': float(outputs.qmax20),
                'qmax_15': float(outputs.qmax15),
                'qmax_10': float(outputs.qmax10),
                
                # Results
                'r_used': float(outputs.r_used) if outputs.r_used else None,
                'quote_q': float(outputs.quote_q),
                'seller_roi_pct': float(outputs.seller_roi_pct),
                'our_roi_pct': float(outputs.our_roi_pct),
                'margin_abs': float(outputs.our_margin_abs),
                'margin_pct': float(outputs.our_margin_pct),
                'feasible': outputs.feasible,
                'reason': outputs.reason if not outputs.feasible else ''
            }
            
            results.append(result)
            
            # Status indicator
            if outputs.feasible:
                print(f" ✅ Q={outputs.quote_q:.2f}")
            else:
                print(f" ❌ No deal")
            
        except Exception as e:
            print(f" ❌ Error: {str(e)[:50]}")
            results.append({
                'asin': asin,
                'title': product.get('title', ''),
                'marketplace': marketplace,
                'error': str(e),
                'feasible': False
            })
    
    print(f"\n✅ Calculated {len(results)} quotes")
    return results


def generate_excel_report(results: List[Dict], output_file: str):
    """
    Generate Excel workbook with Summary and Raw Data sheets
    --------------------------------------------------------
    
    Args:
        results: List of calculation results
        output_file: Path to output Excel file
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.datavalidation import DataValidation
    except ImportError:
        print("❌ openpyxl not available. Falling back to CSV...")
        generate_csv_report(results, output_file.replace('.xlsx', '.csv'))
        return
    
    print(f"\n📊 Generating Excel report...")
    
    wb = Workbook()
    
    # Remove default sheet
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])
    
    # ========== SHEET 2: RAW DATA (create first so Summary can reference it) ==========
    ws_raw = wb.create_sheet("Raw Data", 0)
    
    print("  📋 Creating Raw Data sheet...")
    
    # Define columns
    columns = [
        'ASIN', 'Title', 'Marketplace', 'Weight_kg', 'BB_avg', 'C_cost', 'm', 'fx_gbp_to_usd',
        'AF', 'FC', 'SC', 'S_bundle',
        'Q_balanced', 'ROI_seller_pct', 'ROI_us_pct',
        'Margin_abs', 'Margin_pct',
        'Feasible', 'Reason'
    ]
    
    # Header row
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    
    for col_idx, col_name in enumerate(columns, 1):
        cell = ws_raw.cell(row=1, column=col_idx)
        cell.value = col_name
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Data rows
    for row_idx, result in enumerate(results, 2):
        # Handle errors
        if 'error' in result and result.get('error'):
            ws_raw.cell(row=row_idx, column=1).value = result.get('asin', 'ERROR')
            ws_raw.cell(row=row_idx, column=2).value = result.get('title', '')
            ws_raw.cell(row=row_idx, column=3).value = result.get('marketplace', '')
            ws_raw.cell(row=row_idx, column=18).value = False
            ws_raw.cell(row=row_idx, column=19).value = result.get('error', 'Unknown error')
            continue
        
        # ASIN, Title, Marketplace
        ws_raw.cell(row=row_idx, column=1).value = result['asin']
        ws_raw.cell(row=row_idx, column=2).value = result.get('title', '')
        ws_raw.cell(row=row_idx, column=3).value = result['marketplace']
        
        # Inputs
        ws_raw.cell(row=row_idx, column=4).value = result.get('weight_kg', 0)
        ws_raw.cell(row=row_idx, column=5).value = result.get('bb_avg', 0)
        ws_raw.cell(row=row_idx, column=6).value = result.get('c_cost', 0)
        ws_raw.cell(row=row_idx, column=7).value = result.get('m', 0)
        ws_raw.cell(row=row_idx, column=8).value = result.get('fx_gbp_to_usd', 1.30)
        
        # Components
        ws_raw.cell(row=row_idx, column=9).value = result.get('af', 0)
        ws_raw.cell(row=row_idx, column=10).value = result.get('fc', 0)
        ws_raw.cell(row=row_idx, column=11).value = result.get('sc', 0)
        ws_raw.cell(row=row_idx, column=12).value = result.get('s_bundle', 0)
        
        # Results (smooth model)
        ws_raw.cell(row=row_idx, column=13).value = result.get('quote_q', 0)
        ws_raw.cell(row=row_idx, column=14).value = result.get('seller_roi_pct', 0)
        ws_raw.cell(row=row_idx, column=15).value = result.get('our_roi_pct', 0)
        ws_raw.cell(row=row_idx, column=16).value = result.get('margin_abs', 0)
        ws_raw.cell(row=row_idx, column=17).value = result.get('margin_pct', 0)
        ws_raw.cell(row=row_idx, column=18).value = result.get('feasible', False)
        ws_raw.cell(row=row_idx, column=19).value = result.get('reason', '')
    
    # Format currency columns (2 decimal places)
    currency_cols = [5, 6, 9, 10, 11, 12, 13, 16]  # BB_avg, C, AF, FC, SC, S, Q_balanced, Margin_abs
    for col_idx in currency_cols:
        for row_idx in range(2, len(results) + 2):
            ws_raw.cell(row=row_idx, column=col_idx).number_format = '0.00'
    
    # Format percentage columns
    percent_cols = [7, 14, 15, 17]  # m, ROI_seller_pct, ROI_us_pct, Margin_%
    for col_idx in percent_cols:
        for row_idx in range(2, len(results) + 2):
            cell = ws_raw.cell(row=row_idx, column=col_idx)
            if cell.value is not None:
                cell.number_format = '0.00'
    
    # Enable auto-filter
    ws_raw.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(results) + 1}"
    
    # Set column widths
    ws_raw.column_dimensions['A'].width = 15  # ASIN
    ws_raw.column_dimensions['B'].width = 30  # Title
    ws_raw.column_dimensions['C'].width = 12  # Marketplace
    for col in range(4, len(columns) + 1):
        ws_raw.column_dimensions[get_column_letter(col)].width = 12
    
    # ========== SHEET 1: MODEL SUMMARY / README ==========
    ws_model = wb.create_sheet("Model Summary", 0)
    
    print("  📘 Creating Model Summary sheet...")
    
    # Title
    ws_model['A1'] = "Book Portal Quote Model - ROI Tier System"
    ws_model['A1'].font = Font(bold=True, size=16, color="366092")
    ws_model.merge_cells('A1:F1')
    
    # Variables section (matching screenshot)
    ws_model['A3'] = "📊 VARIABLES"
    ws_model['A3'].font = Font(bold=True, size=12)
    ws_model['A3'].fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
    
    # Variable table headers
    ws_model['A5'] = "Variable"
    ws_model['B5'] = "Meaning"
    ws_model['A5'].font = Font(bold=True)
    ws_model['B5'].font = Font(bold=True)
    
    # Variable definitions (from screenshot)
    variables = [
        ("BB̄", "30-day average Buy Box price"),
        ("AF", "17% × BB̄ (Amazon fee)"),
        ("FC", "Fulfilment cost to end customer (tiered by weight & marketplace)"),
        ("SC", "Shipping from wholesaler to seller"),
        ("C", "Acquisition cost (our cost)"),
        ("S", "FC + AF + SC (total seller costs)"),
        ("Qmin", "Floor (10% ROI for us)"),
        ("Qmax_our", "soft cap at (25% ROI for us)"),
        ("Qmax(r)", "Seller ROI tier range (40-30 %, 30-20%, 20-15%, 15-10%)"),
        ("r_used", "Seller ROI actually achieved"),
        ("Q", "Final quote chosen"),
        ("ROI_seller", "Seller ROI at BB̄"),
        ("ROI_us", "Our ROI at Q"),
        ("Feasible", "True if both ROI conditions met")
    ]
    
    for i, (var, meaning) in enumerate(variables, 6):
        ws_model[f'A{i}'] = var
        ws_model[f'B{i}'] = meaning
    
    # ROI Model section (matching screenshot)
    ws_model['A21'] = "🎯 ROI MODEL"
    ws_model['A21'].font = Font(bold=True, size=12)
    ws_model['A21'].fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
    
    ws_model['A23'] = "Our ROI Range:"
    ws_model['A23'].font = Font(bold=True)
    ws_model['A24'] = "• Minimum ROI floor: 10%"
    ws_model['A25'] = "• Target / soft cap: 25%"
    ws_model['A26'] = "• Qmin = C × (1 + 0.10)"
    ws_model['A27'] = "• Qmax_our = C × (1 + 0.25)"
    
    ws_model['A29'] = "Seller ROI Tiers:"
    ws_model['A29'].font = Font(bold=True)
    ws_model['A30'] = "• Try r ∈ [40-30 %, 30-20%, 20-15%, 15-10%]"
    ws_model['A31'] = "• Qmax(r) = (BB̄ - (1+r) × S) / (1+r)"
    
    ws_model['A33'] = "Decision Logic (Seller-Prioritized):"
    ws_model['A33'].font = Font(bold=True)
    ws_model['A34'] = "• PRIORITY: Try seller ROI ≥20% first (40-30%, 30-20% tiers)"
    ws_model['A35'] = "• For each tier: Compute Qmax(r) and check our ROI"
    ws_model['A36'] = "• HARD FLOOR: Skip any tier where our ROI < 10%"
    ws_model['A37'] = "• If Qmin ≤ Qmax(r) ≤ Qmax_our: Use Qmax(r)"
    ws_model['A38'] = "• If Qmax(r) > Qmax_our: Clamp to Qmax_our (cap our ROI at 25%)"
    ws_model['A39'] = "• Only try seller ROI <20% if no ≥20% tier gives us ≥10% ROI"
    ws_model['A40'] = "• If no tier achieves our 10% ROI minimum: No-deal"
    
    # Set column widths
    ws_model.column_dimensions['A'].width = 15
    ws_model.column_dimensions['B'].width = 50
    
    # ========== SHEET 2: QUOTE SUMMARY (Interactive) ==========
    ws_summary = wb.create_sheet("Quote Summary", 0)
    
    print("  🎯 Creating Quote Summary sheet...")
    
    # Title
    ws_summary['A1'] = "Book Portal Quote Calculator - Interactive Summary"
    ws_summary['A1'].font = Font(bold=True, size=14)
    ws_summary.merge_cells('A1:D1')
    
    # Selection dropdowns
    ws_summary['A3'] = "Select ASIN:"
    ws_summary['A3'].font = Font(bold=True)
    ws_summary['B3'] = results[0]['asin']  # Default first ASIN
    
    ws_summary['A4'] = "Select Marketplace:"
    ws_summary['A4'].font = Font(bold=True)
    ws_summary['B4'] = "UK"  # Default UK
    
    # Create data validation for ASIN (dropdown)
    unique_asins = sorted(list(set([r['asin'] for r in results if 'asin' in r])))
    asin_dv = DataValidation(type="list", formula1=f'"{",".join(unique_asins)}"', allow_blank=False)
    asin_dv.add(ws_summary['B3'])
    ws_summary.add_data_validation(asin_dv)
    
    # Create data validation for Marketplace (dropdown)
    marketplace_dv = DataValidation(type="list", formula1='"UK,US"', allow_blank=False)
    marketplace_dv.add(ws_summary['B4'])
    ws_summary.add_data_validation(marketplace_dv)
    
    # Section headers
    section_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    section_font = Font(bold=True, color="FFFFFF", size=11)
    
    row = 6
    
    # INPUTS Section
    ws_summary[f'A{row}'] = "INPUTS"
    ws_summary[f'A{row}'].fill = section_fill
    ws_summary[f'A{row}'].font = section_font
    ws_summary.merge_cells(f'A{row}:D{row}')
    row += 1
    
    # Use XLOOKUP or INDEX/MATCH to pull data from Raw Data sheet
    # Format: =INDEX('Raw Data'!$E:$E, MATCH(1, ('Raw Data'!$A:$A=$B$3)*('Raw Data'!$C:$C=$B$4), 0))
    
    summary_fields = [
        ('ASIN', '=B3'),
        ('Marketplace', '=B4'),
        ('Buy Box Avg (BB̄)', '=IFERROR(INDEX(\'Raw Data\'!$E:$E, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), "N/A")'),
        ('Weight (kg)', '=IFERROR(INDEX(\'Raw Data\'!$D:$D, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), "N/A")'),
        ('Our Cost (C)', '=IFERROR(INDEX(\'Raw Data\'!$F:$F, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), "N/A")'),
    ]
    
    for label, formula in summary_fields:
        ws_summary[f'A{row}'] = label
        ws_summary[f'B{row}'] = formula
        row += 1
    
    row += 1  # Blank row
    
    # COMPONENTS Section
    ws_summary[f'A{row}'] = "COMPONENTS"
    ws_summary[f'A{row}'].fill = section_fill
    ws_summary[f'A{row}'].font = section_font
    ws_summary.merge_cells(f'A{row}:D{row}')
    row += 1
    
    component_fields = [
        ('Amazon Fee (AF)', '=IFERROR(INDEX(\'Raw Data\'!$I:$I, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
        ('Fulfilment Cost (FC)', '=IFERROR(INDEX(\'Raw Data\'!$J:$J, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
        ('Shipping to Seller (SC)', '=IFERROR(INDEX(\'Raw Data\'!$K:$K, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
        ('Total Seller Costs (S)', '=IFERROR(INDEX(\'Raw Data\'!$L:$L, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
    ]
    
    for label, formula in component_fields:
        ws_summary[f'A{row}'] = label
        ws_summary[f'B{row}'] = formula
        ws_summary[f'B{row}'].number_format = '0.00'
        row += 1
    
    row += 1  # Blank row
    
    # BOUNDS Section
    ws_summary[f'A{row}'] = "BOUNDS"
    ws_summary[f'A{row}'].fill = section_fill
    ws_summary[f'A{row}'].font = section_font
    ws_summary.merge_cells(f'A{row}:D{row}')
    row += 1
    
    bound_fields = [
        ('Q_balanced (Smooth)', '=IFERROR(INDEX(\'Raw Data\'!$M:$M, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
    ]
    
    for label, formula in bound_fields:
        ws_summary[f'A{row}'] = label
        ws_summary[f'B{row}'] = formula
        ws_summary[f'B{row}'].number_format = '0.00'
        row += 1
    
    row += 1  # Blank row
    
    # RESULTS Section
    ws_summary[f'A{row}'] = "FINAL QUOTE & RESULTS"
    ws_summary[f'A{row}'].fill = section_fill
    ws_summary[f'A{row}'].font = section_font
    ws_summary.merge_cells(f'A{row}:D{row}')
    row += 1
    
    result_fields = [
        ('Feasible?', '=IFERROR(IF(INDEX(\'Raw Data\'!$R:$R, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), "YES", "NO"), "N/A")'),
        ('Q_balanced', '=IFERROR(INDEX(\'Raw Data\'!$M:$M, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
        ('Seller ROI (%)', '=IFERROR(INDEX(\'Raw Data\'!$N:$N, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
        ('Our ROI (%)', '=IFERROR(INDEX(\'Raw Data\'!$O:$O, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
        ('Our Margin (Absolute)', '=IFERROR(INDEX(\'Raw Data\'!$P:$P, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
        ('Our Margin (%)', '=IFERROR(INDEX(\'Raw Data\'!$Q:$Q, MATCH(B3&B4, \'Raw Data\'!$A:$A&\'Raw Data\'!$C:$C, 0)), 0)'),
    ]
    
    for label, formula in result_fields:
        ws_summary[f'A{row}'] = label
        ws_summary[f'A{row}'].font = Font(bold=True) if 'Quote' in label else Font()
        ws_summary[f'B{row}'] = formula
        if 'Feasible' not in label and 'ROI Tier' not in label:
            ws_summary[f'B{row}'].number_format = '0.00'
        if 'Quote' in label:
            ws_summary[f'B{row}'].font = Font(bold=True, size=12, color="00B050")
        row += 1
    
    # Set column widths
    ws_summary.column_dimensions['A'].width = 30
    ws_summary.column_dimensions['B'].width = 20
    ws_summary.column_dimensions['C'].width = 15
    ws_summary.column_dimensions['D'].width = 15
    
    # Save workbook
    wb.save(output_file)
    print(f"\n✅ Excel report saved: {output_file}")
    print(f"   - Sheet 1: Quote Summary (interactive)")
    print(f"   - Sheet 2: Raw Data ({len(results)} rows)")


def generate_csv_report(results: List[Dict], output_file: str):
    """
    Generate CSV report as fallback
    --------------------------------
    
    Args:
        results: List of calculation results
        output_file: Path to output CSV file
    """
    print(f"\n📊 Generating CSV report...")
    
    # Define columns
    columns = [
        'ASIN', 'Title', 'Marketplace', 'Weight_kg', 'BB_avg', 'C_cost', 'm', 'fx_gbp_to_usd',
        'AF', 'FC', 'SC', 'S_bundle',
        'Q_balanced', 'ROI_seller_pct', 'ROI_us_pct',
        'Margin_abs', 'Margin_pct',
        'Feasible', 'Reason'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        
        for result in results:
            # Handle errors
            if 'error' in result and result.get('error'):
                writer.writerow({
                    'ASIN': result.get('asin', ''),
                    'Title': result.get('title', ''),
                    'Marketplace': result.get('marketplace', ''),
                    'Feasible': False,
                    'Reason': result.get('error', '')
                })
                continue
            
            # Write full row
            writer.writerow({
                'ASIN': result['asin'],
                'Title': result.get('title', ''),
                'Marketplace': result['marketplace'],
                'Weight_kg': result.get('weight_kg', 0),
                'BB_avg': result.get('bb_avg', 0),
                'C_cost': result.get('c_cost', 0),
                'm': result.get('m', 0),
                'fx_gbp_to_usd': result.get('fx_gbp_to_usd', 1.30),
                'AF': result.get('af', 0),
                'FC': result.get('fc', 0),
                'SC': result.get('sc', 0),
                'S_bundle': result.get('s_bundle', 0),
                'Q_balanced': result.get('quote_q', 0),
                'ROI_seller_pct': result.get('seller_roi_pct', 0),
                'ROI_us_pct': result.get('our_roi_pct', 0),
                'Margin_abs': result.get('margin_abs', 0),
                'Margin_pct': result.get('margin_pct', 0),
                'Feasible': result.get('feasible', False),
                'Reason': result.get('reason', '')
            })
    
    print(f"✅ CSV report saved: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate comprehensive quote report for all products',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--fx', type=float, default=1.30,
                       help='GBP to USD exchange rate (default: 1.30)')
    parser.add_argument('--m', type=float, default=0.0,
                       help='Our internal ROI target (default: 0.0)')
    parser.add_argument('--output', type=str,
                       help='Output filename (default: book_portal_quote_report_YYYYMMDD.xlsx)')
    parser.add_argument('--csv-only', action='store_true',
                       help='Generate CSV only (skip Excel)')
    
    args = parser.parse_args()
    
    # Generate default filename with timestamp
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d')
        args.output = f'book_portal_quote_report_{timestamp}.xlsx'
    
    print("=" * 70)
    print("📚 BOOK PORTAL QUOTE REPORT GENERATOR")
    print("=" * 70)
    print(f"\nParameters:")
    print(f"  - FX Rate (GBP→USD): {args.fx}")
    print(f"  - Our Margin Target (m): {args.m}")
    print(f"  - Mode: Each product processed with its database marketplace")
    print(f"  - Output: {args.output}")
    print()
    
    try:
        # Connect to database
        with SessionLocal() as session:
            repo = SupabaseRepo(session)
            
            # Fetch all products
            products = fetch_all_products(session)
            
            if not products:
                print("❌ No products found in database!")
                return 1
            
            # Calculate quotes (each product already has its marketplace)
            results = calculate_all_quotes(
                repo=repo,
                products=products,
                fx_gbp_to_usd=args.fx,
                m=args.m
            )
            
            # Generate report
            if args.csv_only:
                csv_file = args.output.replace('.xlsx', '.csv')
                generate_csv_report(results, csv_file)
            else:
                generate_excel_report(results, args.output)
                
                # Also generate CSV as backup
                csv_file = args.output.replace('.xlsx', '.csv')
                generate_csv_report(results, csv_file)
                print(f"📄 CSV backup also saved: {csv_file}")
            
            print("\n" + "=" * 70)
            print("✅ REPORT GENERATION COMPLETE!")
            print("=" * 70)
            print(f"\nSummary:")
            print(f"  - Products processed: {len(products)}")
            print(f"  - Total quotes calculated: {len(results)}")
            print(f"  - Feasible quotes: {sum(1 for r in results if r.get('feasible', False))}")
            print(f"  - No-deal scenarios: {sum(1 for r in results if not r.get('feasible', False))}")
            print()
            
            return 0
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

