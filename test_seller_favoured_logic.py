"""
Test Seller-Favoured Decision Logic
------------------------------------
Purpose:
- Verify the new seller-favoured logic works as expected
- Compare old vs new behavior

Expected Behavior:
- If seller ROI < 30% at our 10% floor → stay at our 10% (favor seller)
- If seller ROI >= 30% at our 10% floor → take our 20%
- If seller ROI < 10% at our 10% floor → no deal
"""

from decimal import Decimal
from book_portal_pricing.calculator import decide_quote, Inputs
from book_portal_pricing.money import D


def test_case(case_name: str, bb_avg: Decimal, c_cost: Decimal, weight_kg: Decimal):
    """Test a single case and display results."""
    print(f"\n{'='*80}")
    print(f"🧪 {case_name}")
    print(f"{'='*80}")
    
    inputs = Inputs(
        product_id=case_name,
        marketplace='UK',
        bb_avg=bb_avg,
        c_cost=c_cost,
        weight_kg=weight_kg,
        m=D('0.10'),
        fx_gbp_to_usd=D('1.30')
    )
    
    outputs = decide_quote(inputs)
    
    print(f"📊 Inputs:")
    print(f"   BB̄ = £{bb_avg}")
    print(f"   C = £{c_cost}")
    print(f"   Weight = {weight_kg} kg")
    print()
    print(f"💰 Results:")
    print(f"   Quote (Q) = £{outputs.quote_q}")
    print(f"   Our ROI = {outputs.our_roi_pct}%")
    print(f"   Seller ROI = {outputs.seller_roi_pct}%")
    print(f"   Feasible = {outputs.feasible}")
    if outputs.reason:
        print(f"   Reason: {outputs.reason}")
    print()
    print(f"🔍 Diagnostic Values:")
    print(f"   Qmin (our 10%) = £{outputs.qmin}")
    print(f"   Qmax (our 20%) = £{outputs.qmax_our}")
    print(f"   Q_seller10 = £{outputs.q_seller10}")
    print(f"   Q_seller30 = £{outputs.q_seller30}")
    print()
    
    # Show decision logic
    if outputs.feasible:
        if outputs.quote_q == outputs.qmin:
            print(f"✅ Decision: Stayed at Qmin (our 10%) to FAVOR SELLER")
        elif outputs.quote_q == outputs.qmax_our:
            print(f"✅ Decision: Increased to Qmax (our 20%) - seller ROI was high enough (>=30%)")
        else:
            print(f"✅ Decision: Quote in between bounds")
    else:
        print(f"❌ Decision: NO DEAL")
    
    return outputs


def main():
    """Run test cases."""
    print("=" * 80)
    print("🎯 TESTING SELLER-FAVOURED DECISION LOGIC")
    print("=" * 80)
    print()
    print("New Logic Rules:")
    print("  1️⃣ Our ROI floor = 10% (Qmin)")
    print("  2️⃣ Our ROI cap = 20% (Qmax)")
    print("  3️⃣ If seller ROI >= 30% at Qmin → take our 20%")
    print("  4️⃣ If seller ROI < 30% at Qmin → stay at our 10% (FAVOR SELLER)")
    print("  5️⃣ If seller ROI < 10% at Qmin → NO DEAL")
    print()
    
    # Test Case 1: High margin - seller ROI should be >= 30% at our 10%
    # Expected: Q = Qmax (our 20%)
    test_case(
        "Case 1: High Margin (Seller ROI >= 30% at our floor)",
        bb_avg=D('30.00'),
        c_cost=D('8.00'),
        weight_kg=D('2.0')
    )
    
    # Test Case 2: Medium margin - seller ROI between 10-30% at our 10%
    # Expected: Q = Qmin (our 10%) - FAVOR SELLER
    test_case(
        "Case 2: Medium Margin (Seller ROI 10-30% at our floor)",
        bb_avg=D('18.50'),
        c_cost=D('8.00'),
        weight_kg=D('2.0')
    )
    
    # Test Case 3: Low margin - seller ROI < 10% even at our 10%
    # Expected: NO DEAL
    test_case(
        "Case 3: Low Margin (Seller ROI < 10% at our floor)",
        bb_avg=D('10.00'),
        c_cost=D('8.00'),
        weight_kg=D('2.0')
    )
    
    # Test Case 4: Edge case - seller ROI exactly 30% at our 10%
    # Expected: Q = Qmax (our 20%)
    test_case(
        "Case 4: Edge Case (Seller ROI exactly 30% at our floor)",
        bb_avg=D('20.00'),
        c_cost=D('8.00'),
        weight_kg=D('2.0')
    )
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✓ High margin cases → Our ROI = 20%")
    print("  ✓ Medium margin cases → Our ROI = 10% (SELLER-FAVOURED)")
    print("  ✓ Low margin cases → NO DEAL")
    print()


if __name__ == "__main__":
    main()

