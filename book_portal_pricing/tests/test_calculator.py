"""
Test Suite - Quote Calculator Logic
------------------------------------
Purpose:
- Test smooth continuous ROI decision logic
- Validate seller-favoured priority (we secure 20% first if seller >30%)
- Test our ROI constraints [10%, 20%]
- Test boundary conditions and edge cases

Test Scenarios:
- Case A: High margin → Q = Q_max_our, seller ROI ≥ 30% (smooth)
- Case B: Tight margin → Q = Q_seller10, our ROI ≥ 10%
- Case C: Infeasible → seller <10% even at our floor
- Edge cases: boundary conditions, extreme values
"""

import pytest
from decimal import Decimal

from book_portal_pricing.calculator import decide_quote, Inputs, Outputs
from book_portal_pricing.money import D


class TestCaseA_HighMargin:
    """
    Test Case A: High Margin Scenarios.
    
    Seller ROI could exceed 30% if we took less.
    We should take our 20% ROI cap (seller-favoured priority).
    Seller ROI floats smoothly and may exceed 30%.
    """
    
    def test_high_margin_uk(self):
        """Test high margin UK product: we take 20%, seller gets >30%."""
        inputs = Inputs(
            product_id='HIGH_UK',
            marketplace='UK',
            bb_avg=D('30.00'),     # High Buy Box
            c_cost=D('8.00'),      # Low cost
            weight_kg=D('2.0'),    # Medium weight
            m=D('0.10')            # 10% our ROI floor
        )
        
        outputs = decide_quote(inputs)
        
        # Should be feasible
        assert outputs.feasible is True
        assert outputs.reason is None
        
        # We should take our 20% ROI cap
        # Q_max_our = 8.00 * 1.20 = 9.60
        assert outputs.qmax_our == D('9.60')
        assert outputs.quote_q == D('9.60')
        
        # Our ROI should be 20%
        assert outputs.our_roi_pct == D('20.00')
        
        # Seller ROI should be well above 30% (smooth, continuous)
        # With BB=30, Q=9.60, let's calculate S:
        # AF = 30 * 0.17 = 5.10
        # FC = 3.50 (2kg UK)
        # SC = 0.50
        # S = 9.10
        # Seller ROI = (30 - (9.60 + 9.10)) / (9.60 + 9.10)
        #            = 11.30 / 18.70 = 60.4%
        assert outputs.seller_roi_pct > D('30.00')
        assert outputs.seller_roi_pct < D('70.00')  # Reasonable upper bound
    
    def test_high_margin_us(self):
        """Test high margin US product: we take 20%, seller gets >30%."""
        inputs = Inputs(
            product_id='HIGH_US',
            marketplace='US',
            bb_avg=D('40.00'),     # High Buy Box
            c_cost=D('10.00'),     # Low cost
            weight_kg=D('2.0'),    # Medium weight
            m=D('0.10'),
            fx_gbp_to_usd=D('1.30')
        )
        
        outputs = decide_quote(inputs)
        
        # Should be feasible
        assert outputs.feasible is True
        
        # We should take our 20% ROI cap
        # Q_max_our = 10.00 * 1.20 = 12.00
        assert outputs.quote_q == D('12.00')
        assert outputs.our_roi_pct == D('20.00')
        
        # Seller ROI should be well above 30%
        assert outputs.seller_roi_pct > D('30.00')
    
    def test_seller_favoured_priority(self):
        """Test seller-favoured priority: we fill our 20% first when seller >30%."""
        inputs = Inputs(
            product_id='PRIORITY_TEST',
            marketplace='UK',
            bb_avg=D('25.00'),
            c_cost=D('8.00'),
            weight_kg=D('1.0'),    # Lighter weight
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Should take our 20% cap
        assert outputs.our_roi_pct == D('20.00')
        
        # Seller should still be well above 10% (and likely above 30%)
        assert outputs.seller_roi_pct > D('10.00')


class TestCaseB_TightMargin:
    """
    Test Case B: Tight Margin Scenarios.
    
    Seller ROI would drop below 10% if we took our 20%.
    We should lower Q to Q_seller10 (seller exactly 10%).
    Our ROI should be between 10% and 20%.
    """
    
    def test_tight_margin_uk(self):
        """Test tight margin UK product: lower to seller 10%, our ROI 10-20%."""
        inputs = Inputs(
            product_id='TIGHT_UK',
            marketplace='UK',
            bb_avg=D('15.00'),     # Moderate Buy Box
            c_cost=D('8.00'),      # Moderate cost
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Should be feasible
        assert outputs.feasible is True
        assert outputs.reason is None
        
        # Quote should be at Q_seller10 (seller exactly 10%)
        # Let's check seller ROI is close to 10%
        # (allowing small rounding differences)
        assert outputs.seller_roi_pct >= D('9.50')
        assert outputs.seller_roi_pct <= D('10.50')
        
        # Our ROI should be between 10% and 20%
        assert outputs.our_roi_pct >= D('10.00')
        assert outputs.our_roi_pct <= D('20.00')
        
        # Quote should be less than Q_max_our
        assert outputs.quote_q < outputs.qmax_our
        
        # Quote should be at least Q_min
        assert outputs.quote_q >= outputs.qmin
    
    def test_tight_margin_us(self):
        """Test tight margin US product: lower to seller 10%, our ROI 10-20%."""
        inputs = Inputs(
            product_id='TIGHT_US',
            marketplace='US',
            bb_avg=D('18.00'),     # Moderate Buy Box
            c_cost=D('10.00'),     # Moderate cost
            weight_kg=D('2.0'),
            m=D('0.10'),
            fx_gbp_to_usd=D('1.30')
        )
        
        outputs = decide_quote(inputs)
        
        # Should be feasible
        assert outputs.feasible is True
        
        # Seller ROI should be close to 10%
        assert outputs.seller_roi_pct >= D('9.50')
        assert outputs.seller_roi_pct <= D('10.50')
        
        # Our ROI should be between 10% and 20%
        assert outputs.our_roi_pct >= D('10.00')
        assert outputs.our_roi_pct <= D('20.00')
    
    def test_smooth_transition(self):
        """Test smooth transition between high and tight margins (no jumps)."""
        # Test a series of BB values to ensure smooth transitions
        base_inputs = {
            'product_id': 'SMOOTH_TEST',
            'marketplace': 'UK',
            'c_cost': D('8.00'),
            'weight_kg': D('2.0'),
            'm': D('0.10'),
        }
        
        # Test BB from 25 down to 15 in steps
        bb_values = [D(str(x)) for x in range(25, 14, -1)]
        prev_quote = None
        
        for bb in bb_values:
            inputs = Inputs(bb_avg=bb, **base_inputs)  # type: ignore
            outputs = decide_quote(inputs)
            
            if outputs.feasible:
                # Quote should decrease smoothly (no jumps)
                if prev_quote is not None:
                    # Allow small changes, but no harsh jumps
                    quote_change = abs(outputs.quote_q - prev_quote)
                    # Change should be small and gradual
                    assert quote_change < D('2.00'), f"Harsh jump at BB={bb}"
                
                prev_quote = outputs.quote_q


class TestCaseC_Infeasible:
    """
    Test Case C: Infeasible Scenarios.
    
    Seller ROI would be <10% even at our 10% floor.
    Should mark as not feasible with clear reason.
    """
    
    def test_infeasible_uk(self):
        """Test infeasible UK product: no deal, seller <10% at our floor."""
        inputs = Inputs(
            product_id='INFEASIBLE_UK',
            marketplace='UK',
            bb_avg=D('10.00'),     # Low Buy Box
            c_cost=D('8.00'),      # Moderate cost
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Should be infeasible
        assert outputs.feasible is False
        assert outputs.reason is not None
        assert "seller ROI <10%" in outputs.reason.lower()
        
        # Quote should be clamped to Q_min for diagnostics
        assert outputs.quote_q == outputs.qmin
        
        # Seller ROI would be very low
        assert outputs.seller_roi_pct < D('10.00')
        
        # Our ROI should be at floor (10%)
        assert outputs.our_roi_pct == D('10.00')
    
    def test_infeasible_us(self):
        """Test infeasible US product: no deal, seller <10% at our floor."""
        inputs = Inputs(
            product_id='INFEASIBLE_US',
            marketplace='US',
            bb_avg=D('12.00'),     # Low Buy Box
            c_cost=D('10.00'),     # Moderate cost
            weight_kg=D('2.0'),
            m=D('0.10'),
            fx_gbp_to_usd=D('1.30')
        )
        
        outputs = decide_quote(inputs)
        
        # Should be infeasible
        assert outputs.feasible is False
        assert outputs.reason is not None
        
        # Seller ROI would be very low
        assert outputs.seller_roi_pct < D('10.00')
    
    def test_infeasible_high_cost(self):
        """Test infeasible scenario: our cost is too high relative to BB."""
        inputs = Inputs(
            product_id='HIGH_COST',
            marketplace='UK',
            bb_avg=D('15.00'),
            c_cost=D('12.00'),     # Very high cost
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Should be infeasible
        assert outputs.feasible is False


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_seller_roi_exactly_10_percent(self):
        """Test case where seller ROI is exactly at 10% boundary."""
        # Need to find inputs where seller ROI = 10% at Q_max_our
        # This is tricky - we'll test the Q_seller10 calculation
        inputs = Inputs(
            product_id='BOUNDARY_10',
            marketplace='UK',
            bb_avg=D('14.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Should be feasible
        assert outputs.feasible is True
        
        # Seller ROI should be close to 10%
        # (may not be exact due to rounding and clamping)
        assert outputs.seller_roi_pct >= D('9.00')
        assert outputs.seller_roi_pct <= D('11.00')
    
    def test_our_roi_constraints(self):
        """Test our ROI is always within [10%, 20%] when feasible."""
        # Test multiple scenarios
        test_cases = [
            # (bb_avg, c_cost)
            (D('30.00'), D('8.00')),   # High margin
            (D('20.00'), D('8.00')),   # Medium margin
            (D('15.00'), D('8.00')),   # Lower margin
        ]
        
        for bb, cost in test_cases:
            inputs = Inputs(
                product_id='ROI_TEST',
                marketplace='UK',
                bb_avg=bb,
                c_cost=cost,
                weight_kg=D('2.0'),
                m=D('0.10')
            )
            
            outputs = decide_quote(inputs)
            
            if outputs.feasible:
                # Our ROI must be within [10%, 20%]
                assert outputs.our_roi_pct >= D('10.00'), f"BB={bb}, C={cost}"
                assert outputs.our_roi_pct <= D('20.00'), f"BB={bb}, C={cost}"
    
    def test_quote_within_bounds(self):
        """Test quote is always within [Q_min, Q_max_our]."""
        inputs = Inputs(
            product_id='BOUNDS_TEST',
            marketplace='UK',
            bb_avg=D('20.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Quote should be within our ROI band
        assert outputs.quote_q >= outputs.qmin
        assert outputs.quote_q <= outputs.qmax_our
    
    def test_heavy_weight(self):
        """Test calculator with heavy item (tier 5)."""
        inputs = Inputs(
            product_id='HEAVY',
            marketplace='UK',
            bb_avg=D('30.00'),
            c_cost=D('8.00'),
            weight_kg=D('10.0'),   # Heavy item
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Should still work
        assert outputs.feasible is True
        
        # FC should be in tier 5
        # UK 10kg: £6.50 + £0.50 * 2 = £7.00
        assert outputs.fc == D('7.00')
    
    def test_light_weight(self):
        """Test calculator with very light item (tier 1)."""
        inputs = Inputs(
            product_id='LIGHT',
            marketplace='UK',
            bb_avg=D('30.00'),
            c_cost=D('8.00'),
            weight_kg=D('0.5'),    # Very light item
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Should work
        assert outputs.feasible is True
        
        # FC should be in tier 1
        # UK ≤1kg: £3.00
        assert outputs.fc == D('3.00')


class TestComponentCalculations:
    """Test individual component calculations."""
    
    def test_amazon_fee_calculation(self):
        """Test Amazon fee is always 17% of Buy Box."""
        inputs = Inputs(
            product_id='AF_TEST',
            marketplace='UK',
            bb_avg=D('20.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # AF should be 17% of BB
        expected_af = inputs.bb_avg * D('0.17')
        assert outputs.af == D('3.40')  # 20.00 * 0.17 = 3.40
    
    def test_seller_costs_bundle(self):
        """Test S = FC + AF + SC."""
        inputs = Inputs(
            product_id='S_TEST',
            marketplace='UK',
            bb_avg=D('20.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # S should equal FC + AF + SC
        expected_s = outputs.fc + outputs.af + outputs.sc
        assert outputs.s_bundle == expected_s
    
    def test_margin_calculations(self):
        """Test margin calculations are consistent."""
        inputs = Inputs(
            product_id='MARGIN_TEST',
            marketplace='UK',
            bb_avg=D('20.00'),
            c_cost=D('8.00'),
            weight_kg=D('2.0'),
            m=D('0.10')
        )
        
        outputs = decide_quote(inputs)
        
        # Margin absolute should be Q - C
        expected_margin_abs = outputs.quote_q - inputs.c_cost
        assert outputs.margin_abs == expected_margin_abs
        
        # Margin percent should match our ROI
        assert outputs.margin_pct == outputs.our_roi_pct


class TestExchangeRateVariations:
    """Test US calculations with different exchange rates."""
    
    def test_us_low_exchange_rate(self):
        """Test US quote with low GBP/USD exchange rate."""
        inputs = Inputs(
            product_id='US_LOW_FX',
            marketplace='US',
            bb_avg=D('30.00'),
            c_cost=D('10.00'),
            weight_kg=D('2.0'),
            m=D('0.10'),
            fx_gbp_to_usd=D('1.20')  # Lower exchange rate
        )
        
        outputs = decide_quote(inputs)
        
        # SC should be lower with lower exchange rate
        # £6.00 * 1.20 = $7.20
        assert outputs.sc == D('7.20')
    
    def test_us_high_exchange_rate(self):
        """Test US quote with high GBP/USD exchange rate."""
        inputs = Inputs(
            product_id='US_HIGH_FX',
            marketplace='US',
            bb_avg=D('30.00'),
            c_cost=D('10.00'),
            weight_kg=D('2.0'),
            m=D('0.10'),
            fx_gbp_to_usd=D('1.50')  # Higher exchange rate
        )
        
        outputs = decide_quote(inputs)
        
        # SC should be higher with higher exchange rate
        # £6.00 * 1.50 = $9.00
        assert outputs.sc == D('9.00')




