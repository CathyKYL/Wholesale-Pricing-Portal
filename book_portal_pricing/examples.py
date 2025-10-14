"""
Examples - CLI Tool for Testing Quote Calculator
-------------------------------------------------
Purpose:
- Provide command-line interface for testing quote calculations
- Generate sample Excel reports
- Demonstrate usage of calculator API

This module can be run directly to test the quote calculator with mock data.

Usage:
    # Run with mock data
    python -m book_portal_pricing.examples
    
    # Or import and use in your own scripts
    from book_portal_pricing.examples import run_example
    run_example()
"""

from decimal import Decimal
from typing import List, Sequence

from .calculator import decide_quote, Inputs, Outputs
from .money import D
from .repo import Repo, Marketplace
from .excel_export import create_csv


class MockRepo:
    """
    Mock repository implementation for testing.
    
    Purpose:
    - Provide test data without requiring database connection
    - Demonstrate Repo interface implementation
    - Enable standalone testing and examples
    
    This mock repo contains 6 test products across different scenarios:
    - High margin cases (seller ROI > 30% possible)
    - Tight margin cases (seller ROI 10-30%)
    - Infeasible cases (no-deal scenarios)
    """
    
    def __init__(self):
        """Initialize mock data for 6 test products."""
        # Mock data: (product_id, marketplace) -> (bb_prices, weight_kg, cost_c)
        self.products = {
            # UK Products
            ("TEST_UK_HIGH", "UK"): {
                "bb_prices": [D('30.00')] * 30,  # High margin scenario
                "weight_kg": D('2.0'),
                "cost_c": D('8.00'),
            },
            ("TEST_UK_MEDIUM", "UK"): {
                "bb_prices": [D('15.00')] * 30,  # Medium margin scenario
                "weight_kg": D('2.0'),
                "cost_c": D('8.00'),
            },
            ("TEST_UK_LOW", "UK"): {
                "bb_prices": [D('10.00')] * 30,  # Low margin scenario (infeasible)
                "weight_kg": D('2.0'),
                "cost_c": D('8.00'),
            },
            
            # US Products
            ("TEST_US_HIGH", "US"): {
                "bb_prices": [D('40.00')] * 30,  # High margin scenario
                "weight_kg": D('2.0'),
                "cost_c": D('10.00'),
            },
            ("TEST_US_MEDIUM", "US"): {
                "bb_prices": [D('18.00')] * 30,  # Medium margin scenario
                "weight_kg": D('2.0'),
                "cost_c": D('10.00'),
            },
            ("TEST_US_LOW", "US"): {
                "bb_prices": [D('12.00')] * 30,  # Low margin scenario (infeasible)
                "weight_kg": D('2.0'),
                "cost_c": D('10.00'),
            },
        }
    
    def get_bb_prices_last_30_days(
        self, 
        product_id: str, 
        marketplace: Marketplace
    ) -> Sequence[Decimal]:
        """Return mock Buy Box prices for last 30 days."""
        key = (product_id, marketplace)
        if key not in self.products:
            return []
        return self.products[key]["bb_prices"]
    
    def get_weight_kg(self, product_id: str, marketplace: str = None) -> Decimal:
        """Return mock product weight."""
        # Find product across all marketplaces
        for (pid, _), data in self.products.items():
            if pid == product_id:
                return data["weight_kg"]
        raise ValueError(f"Product {product_id} not found")
    
    def get_our_cost_c(self, product_id: str, marketplace: str = None) -> Decimal:
        """Return mock acquisition cost."""
        # Find product across all marketplaces
        for (pid, _), data in self.products.items():
            if pid == product_id:
                return data["cost_c"]
        raise ValueError(f"Product {product_id} not found")
    
    def list_all_products(self) -> List[tuple]:
        """Return list of all (product_id, marketplace) pairs."""
        return list(self.products.keys())


def run_example():
    """
    Run example calculations and display results.
    
    Purpose:
    - Demonstrate calculator usage
    - Show different scenarios (high/medium/low margin)
    - Validate smooth continuous ROI logic
    """
    print("=" * 80)
    print("Book Portal Quote Calculator - Example Run")
    print("Smooth Continuous ROI Strategy (NO HARSH TIERS)")
    print("=" * 80)
    print()
    
    # Initialize mock repo
    repo = MockRepo()
    
    # Process all test products
    outputs_list: List[tuple[Inputs, Outputs]] = []
    
    for (product_id, marketplace), data in repo.products.items():
        print(f"\n{'─' * 80}")
        print(f"Product: {product_id} ({marketplace})")
        print(f"{'─' * 80}")
        
        # Calculate BB average
        bb_prices = data["bb_prices"]
        bb_avg = sum(bb_prices) / len(bb_prices)
        
        # Build inputs
        inputs = Inputs(
            product_id=product_id,
            marketplace=marketplace,  # type: ignore
            bb_avg=bb_avg,
            c_cost=data["cost_c"],
            weight_kg=data["weight_kg"],
            m=D('0.10'),  # 10% our ROI floor
            fx_gbp_to_usd=D('1.30')
        )
        
        # Calculate quote
        outputs = decide_quote(inputs)
        outputs_list.append((inputs, outputs))
        
        # Display results
        print(f"\nInputs:")
        print(f"  Buy Box Avg (BB̄):     {inputs.marketplace} {inputs.bb_avg}")
        print(f"  Our Cost (C):         {inputs.marketplace} {inputs.c_cost}")
        print(f"  Weight:               {inputs.weight_kg} kg")
        print(f"  Our ROI Floor (m):    {inputs.m * 100}%")
        
        print(f"\nComponents:")
        print(f"  Amazon Fee (AF):      {inputs.marketplace} {outputs.af} (17% of BB̄)")
        print(f"  Fulfilment Cost (FC): {inputs.marketplace} {outputs.fc}")
        print(f"  Shipping Cost (SC):   {inputs.marketplace} {outputs.sc}")
        print(f"  Seller Costs (S):     {inputs.marketplace} {outputs.s_bundle}")
        
        print(f"\nBoundaries (Smooth, Continuous):")
        print(f"  Q_min (our 10%):      {inputs.marketplace} {outputs.qmin}")
        print(f"  Q_max_our (our 20%):  {inputs.marketplace} {outputs.qmax_our}")
        print(f"  Q_seller10:           {inputs.marketplace} {outputs.q_seller10} (seller 10% ROI)")
        print(f"  Q_seller30:           {inputs.marketplace} {outputs.q_seller30} (seller 30% ROI)")
        print(f"  Q_seller40:           {inputs.marketplace} {outputs.q_seller40} (seller 40% ROI)")
        
        print(f"\nDecision:")
        if outputs.feasible:
            print(f"  ✓ FEASIBLE")
            print(f"  Quote (Q):            {inputs.marketplace} {outputs.quote_q}")
            print(f"  Seller ROI:           {outputs.seller_roi_pct}%")
            print(f"  Our ROI:              {outputs.our_roi_pct}%")
            print(f"  Our Margin:           {inputs.marketplace} {outputs.margin_abs} ({outputs.margin_pct}%)")
            
            # Explain decision
            if outputs.our_roi_pct >= D('19.90'):  # Close to 20%
                print(f"\n  → We took our 20% ROI cap (seller-favoured priority)")
                print(f"    Seller ROI floats smoothly: {outputs.seller_roi_pct}%")
            else:
                print(f"\n  → We lowered Q to ensure seller gets 10% ROI")
                print(f"    Our ROI: {outputs.our_roi_pct}% (between 10-20%)")
        else:
            print(f"  ✗ NOT FEASIBLE")
            print(f"  Reason: {outputs.reason}")
            print(f"  (Even at our 10% floor, seller would be <10%)")
    
    print(f"\n{'=' * 80}")
    print(f"Example complete! Processed {len(outputs_list)} products.")
    print(f"{'=' * 80}")
    
    # Generate CSV export
    print(f"\nGenerating CSV export...")
    csv_bytes, mime_type = create_csv(outputs_list)
    
    # Save CSV
    csv_filename = "book_portal_quote_report_example.csv"
    with open(csv_filename, 'wb') as f:
        f.write(csv_bytes)
    
    print(f"✓ Saved CSV report to: {csv_filename}")
    print(f"  ({len(csv_bytes)} bytes, {len(outputs_list)} products)")
    
    # Try to generate Excel if openpyxl available
    try:
        from .excel_export import OPENPYXL_AVAILABLE
        
        if OPENPYXL_AVAILABLE:
            print(f"\nGenerating Excel workbook...")
            from .excel_export import create_workbook
            
            # Note: create_workbook expects repo with product_ids
            # For now, we'll just inform the user
            print(f"  Note: Full Excel workbook generation requires database repo")
            print(f"  Use create_workbook(repo, product_ids=[...]) in your integration")
        else:
            print(f"\n⚠ openpyxl not installed - Excel export not available")
            print(f"  Install with: pip install openpyxl")
    except ImportError:
        print(f"\n⚠ Excel export not available (openpyxl not installed)")
    
    print()


if __name__ == "__main__":
    run_example()

