"""
Test Suite - Tier Calculations (FC and SC)
-------------------------------------------
Purpose:
- Test fulfillment cost (FC) tier boundaries for UK and US
- Test shipping cost (SC) calculations
- Validate weight-based tier transitions
- Test edge cases and error handling

Test Coverage:
- UK FC tiers: ≤1kg, ≤2kg, ≤5kg, ≤8kg, >8kg
- US FC tiers: ≤1kg, ≤2kg, ≤5kg, ≤8kg, >8kg
- SC calculations for UK and US
- Exchange rate variations
- Error cases (zero/negative weight)
"""

import pytest
from decimal import Decimal

from book_portal_pricing.tiers import fc_uk, fc_us, compute_fc, compute_sc
from book_portal_pricing.money import D


class TestFCUK:
    """Test UK fulfillment cost tiers."""
    
    def test_fc_uk_tier_1_boundary_low(self):
        """Test UK FC at lower boundary of tier 1 (0.1kg)."""
        # Weight 0.1kg should be in tier 1 (≤1kg): £3.00
        assert fc_uk(D('0.1')) == D('3.00')
    
    def test_fc_uk_tier_1_boundary_high(self):
        """Test UK FC at upper boundary of tier 1 (1.0kg exactly)."""
        # Weight exactly 1.0kg should be in tier 1 (≤1kg): £3.00
        assert fc_uk(D('1.0')) == D('3.00')
    
    def test_fc_uk_tier_2_just_above(self):
        """Test UK FC just above tier 1 boundary (1.1kg)."""
        # Weight 1.1kg should be in tier 2 (1-2kg): £3.50
        assert fc_uk(D('1.1')) == D('3.50')
    
    def test_fc_uk_tier_2_boundary_high(self):
        """Test UK FC at upper boundary of tier 2 (2.0kg exactly)."""
        # Weight exactly 2.0kg should be in tier 2 (≤2kg): £3.50
        assert fc_uk(D('2.0')) == D('3.50')
    
    def test_fc_uk_tier_3_just_above(self):
        """Test UK FC just above tier 2 boundary (2.5kg)."""
        # Weight 2.5kg should be in tier 3 (2-5kg): £4.50
        assert fc_uk(D('2.5')) == D('4.50')
    
    def test_fc_uk_tier_3_boundary_high(self):
        """Test UK FC at upper boundary of tier 3 (5.0kg exactly)."""
        # Weight exactly 5.0kg should be in tier 3 (≤5kg): £4.50
        assert fc_uk(D('5.0')) == D('4.50')
    
    def test_fc_uk_tier_4_just_above(self):
        """Test UK FC just above tier 3 boundary (6.0kg)."""
        # Weight 6.0kg should be in tier 4 (5-8kg): £5.75
        assert fc_uk(D('6.0')) == D('5.75')
    
    def test_fc_uk_tier_4_boundary_high(self):
        """Test UK FC at upper boundary of tier 4 (8.0kg exactly)."""
        # Weight exactly 8.0kg should be in tier 4 (≤8kg): £5.75
        assert fc_uk(D('8.0')) == D('5.75')
    
    def test_fc_uk_tier_5_just_above(self):
        """Test UK FC just above tier 4 boundary (9.0kg)."""
        # Weight 9.0kg should be in tier 5 (>8kg): £6.50 + £0.50 * 1 = £7.00
        assert fc_uk(D('9.0')) == D('7.00')
    
    def test_fc_uk_tier_5_larger(self):
        """Test UK FC for larger weight in tier 5 (12.0kg)."""
        # Weight 12.0kg: £6.50 + £0.50 * 4 = £8.50
        assert fc_uk(D('12.0')) == D('8.50')
    
    def test_fc_uk_zero_weight(self):
        """Test UK FC raises error for zero weight."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            fc_uk(D('0'))
    
    def test_fc_uk_negative_weight(self):
        """Test UK FC raises error for negative weight."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            fc_uk(D('-1.0'))


class TestFCUS:
    """Test US fulfillment cost tiers."""
    
    def test_fc_us_tier_1_boundary_low(self):
        """Test US FC at lower boundary of tier 1 (0.1kg)."""
        # Weight 0.1kg should be in tier 1 (≤1kg): $4.25
        assert fc_us(D('0.1')) == D('4.25')
    
    def test_fc_us_tier_1_boundary_high(self):
        """Test US FC at upper boundary of tier 1 (1.0kg exactly)."""
        # Weight exactly 1.0kg should be in tier 1 (≤1kg): $4.25
        assert fc_us(D('1.0')) == D('4.25')
    
    def test_fc_us_tier_2_just_above(self):
        """Test US FC just above tier 1 boundary (1.5kg)."""
        # Weight 1.5kg should be in tier 2 (1-2kg): $4.95
        assert fc_us(D('1.5')) == D('4.95')
    
    def test_fc_us_tier_2_boundary_high(self):
        """Test US FC at upper boundary of tier 2 (2.0kg exactly)."""
        # Weight exactly 2.0kg should be in tier 2 (≤2kg): $4.95
        assert fc_us(D('2.0')) == D('4.95')
    
    def test_fc_us_tier_3_middle(self):
        """Test US FC in middle of tier 3 (3.5kg)."""
        # Weight 3.5kg should be in tier 3 (2-5kg): $6.25
        assert fc_us(D('3.5')) == D('6.25')
    
    def test_fc_us_tier_3_boundary_high(self):
        """Test US FC at upper boundary of tier 3 (5.0kg exactly)."""
        # Weight exactly 5.0kg should be in tier 3 (≤5kg): $6.25
        assert fc_us(D('5.0')) == D('6.25')
    
    def test_fc_us_tier_4_middle(self):
        """Test US FC in middle of tier 4 (7.0kg)."""
        # Weight 7.0kg should be in tier 4 (5-8kg): $7.75
        assert fc_us(D('7.0')) == D('7.75')
    
    def test_fc_us_tier_4_boundary_high(self):
        """Test US FC at upper boundary of tier 4 (8.0kg exactly)."""
        # Weight exactly 8.0kg should be in tier 4 (≤8kg): $7.75
        assert fc_us(D('8.0')) == D('7.75')
    
    def test_fc_us_tier_5_just_above(self):
        """Test US FC just above tier 4 boundary (10.0kg)."""
        # Weight 10.0kg should be in tier 5 (>8kg): $8.50 + $0.50 * 2 = $9.50
        assert fc_us(D('10.0')) == D('9.50')
    
    def test_fc_us_tier_5_larger(self):
        """Test US FC for larger weight in tier 5 (15.0kg)."""
        # Weight 15.0kg: $8.50 + $0.50 * 7 = $12.00
        assert fc_us(D('15.0')) == D('12.00')
    
    def test_fc_us_zero_weight(self):
        """Test US FC raises error for zero weight."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            fc_us(D('0'))
    
    def test_fc_us_negative_weight(self):
        """Test US FC raises error for negative weight."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            fc_us(D('-0.5'))


class TestComputeFC:
    """Test marketplace-specific FC routing."""
    
    def test_compute_fc_uk(self):
        """Test compute_fc routes to UK tiers correctly."""
        # Test a few weights to ensure routing works
        assert compute_fc(D('2.0'), 'UK') == D('3.50')
        assert compute_fc(D('6.0'), 'UK') == D('5.75')
    
    def test_compute_fc_us(self):
        """Test compute_fc routes to US tiers correctly."""
        # Test a few weights to ensure routing works
        assert compute_fc(D('2.0'), 'US') == D('4.95')
        assert compute_fc(D('6.0'), 'US') == D('7.75')
    
    def test_compute_fc_different_results(self):
        """Test UK and US tiers produce different results for same weight."""
        # Same weight should give different costs for UK vs US
        weight = D('2.0')
        uk_fc = compute_fc(weight, 'UK')
        us_fc = compute_fc(weight, 'US')
        assert uk_fc != us_fc
        assert uk_fc == D('3.50')
        assert us_fc == D('4.95')


class TestComputeSC:
    """Test shipping cost to seller calculations."""
    
    def test_compute_sc_uk(self):
        """Test UK shipping cost is flat £0.50."""
        # UK SC should always be £0.50 regardless of exchange rate
        assert compute_sc('UK') == D('0.50')
        assert compute_sc('UK', fx_gbp_to_usd=D('1.50')) == D('0.50')
    
    def test_compute_sc_us_default_fx(self):
        """Test US shipping cost with default exchange rate."""
        # US SC: £6.00 * 1.30 = $7.80
        assert compute_sc('US') == D('7.80')
    
    def test_compute_sc_us_custom_fx(self):
        """Test US shipping cost with custom exchange rate."""
        # US SC: £6.00 * 1.25 = $7.50
        assert compute_sc('US', fx_gbp_to_usd=D('1.25')) == D('7.50')
    
    def test_compute_sc_us_higher_fx(self):
        """Test US shipping cost with higher exchange rate."""
        # US SC: £6.00 * 1.40 = $8.40
        assert compute_sc('US', fx_gbp_to_usd=D('1.40')) == D('8.40')
    
    def test_compute_sc_us_lower_fx(self):
        """Test US shipping cost with lower exchange rate."""
        # US SC: £6.00 * 1.20 = $7.20
        assert compute_sc('US', fx_gbp_to_usd=D('1.20')) == D('7.20')


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_fc_very_small_weight(self):
        """Test FC with very small weight (0.01kg)."""
        # Very small weights should still work
        assert fc_uk(D('0.01')) == D('3.00')
        assert fc_us(D('0.01')) == D('4.25')
    
    def test_fc_very_large_weight(self):
        """Test FC with very large weight (100kg)."""
        # UK: £6.50 + £0.50 * 92 = £52.50
        assert fc_uk(D('100.0')) == D('52.50')
        # US: $8.50 + $0.50 * 92 = $54.50
        assert fc_us(D('100.0')) == D('54.50')
    
    def test_fc_exact_tier_boundaries(self):
        """Test FC at exact tier boundaries for both marketplaces."""
        # Test all tier boundaries produce expected results
        boundaries = [
            (D('1.0'), D('3.00'), D('4.25')),
            (D('2.0'), D('3.50'), D('4.95')),
            (D('5.0'), D('4.50'), D('6.25')),
            (D('8.0'), D('5.75'), D('7.75')),
        ]
        
        for weight, expected_uk, expected_us in boundaries:
            assert fc_uk(weight) == expected_uk
            assert fc_us(weight) == expected_us
    
    def test_sc_exchange_rate_precision(self):
        """Test SC with precise exchange rate."""
        # Test with precise decimal exchange rate
        fx = D('1.2567')
        expected = D('6.00') * fx
        assert compute_sc('US', fx_gbp_to_usd=fx) == expected



