"""
Tier Calculations - Fulfillment and Shipping Costs
---------------------------------------------------
Purpose:
- Calculate marketplace-specific fulfillment costs (FC)
- Calculate marketplace-specific shipping costs to seller (SC)
- Support UK (GBP) and US (USD) marketplaces

Fulfillment Cost (FC):
- Tiered by weight and marketplace
- Covers Amazon FBA or similar fulfillment services
- UK rates in GBP, US rates in USD

Shipping Cost to Seller (SC):
- Our cost to ship inventory to the seller
- Excluded from wholesale quote Q (seller pays separately)
- UK: flat £0.50
- US: £6.00 converted to USD via exchange rate

Usage:
    from book_portal_pricing.tiers import compute_fc, compute_sc
    from book_portal_pricing.money import D
    
    # Calculate UK fulfillment cost for 2kg item
    fc = compute_fc(D('2.0'), 'UK')  # Returns Decimal('3.50')
    
    # Calculate US shipping cost to seller
    sc = compute_sc('US', fx_gbp_to_usd=D('1.30'))  # Returns Decimal('7.80')
"""

from decimal import Decimal
from typing import Literal

# Type alias for supported marketplaces
# Only UK and US are currently supported
Marketplace = Literal["UK", "US"]


def fc_uk(weight_kg: Decimal) -> Decimal:
    """
    Calculate UK fulfillment cost based on item weight.
    
    Purpose:
    - Provide weight-tiered fulfillment pricing for UK marketplace
    - All costs in GBP (British Pounds)
    
    Tier Structure:
    - 0-1kg: £3.00
    - 1-2kg: £3.50
    - 2-5kg: £4.50
    - 5-8kg: £5.75
    - >8kg: £6.50 + £0.50 per kg over 8kg
    
    Args:
        weight_kg: Item weight in kilograms (must be positive)
    
    Returns:
        Decimal: Fulfillment cost in GBP
    
    Raises:
        ValueError: If weight is zero or negative
    
    Example:
        >>> fc_uk(D('0.5'))
        Decimal('3.00')
        >>> fc_uk(D('2.5'))
        Decimal('4.50')
        >>> fc_uk(D('10.0'))
        Decimal('7.50')  # 6.50 + (2 * 0.50)
    
    Note:
        Weights are checked at boundaries (<=1, <=2, etc.)
        A weight of exactly 1kg falls in the 0-1kg tier.
    """
    # Validate weight is positive
    if weight_kg <= 0:
        raise ValueError("Weight must be positive.")
    
    # Apply tier structure (check from smallest to largest)
    if weight_kg <= 1:
        return Decimal("3.00")
    if weight_kg <= 2:
        return Decimal("3.50")
    if weight_kg <= 5:
        return Decimal("4.50")
    if weight_kg <= 8:
        return Decimal("5.75")
    
    # For weight > 8kg: base cost + extra per kg
    extra = weight_kg - Decimal("8")
    return Decimal("6.50") + extra * Decimal("0.50")


def fc_us(weight_kg: Decimal) -> Decimal:
    """
    Calculate US fulfillment cost based on item weight.
    
    Purpose:
    - Provide weight-tiered fulfillment pricing for US marketplace
    - All costs in USD (US Dollars)
    
    Tier Structure:
    - 0-1kg: $4.25
    - 1-2kg: $4.95
    - 2-5kg: $6.25
    - 5-8kg: $7.75
    - >8kg: $8.50 + $0.50 per kg over 8kg
    
    Args:
        weight_kg: Item weight in kilograms (must be positive)
    
    Returns:
        Decimal: Fulfillment cost in USD
    
    Raises:
        ValueError: If weight is zero or negative
    
    Example:
        >>> fc_us(D('0.8'))
        Decimal('4.25')
        >>> fc_us(D('3.0'))
        Decimal('6.25')
        >>> fc_us(D('12.0'))
        Decimal('10.50')  # 8.50 + (4 * 0.50)
    
    Note:
        US rates are higher than UK due to different fulfillment costs.
        Tier boundaries are the same for both marketplaces.
    """
    # Validate weight is positive
    if weight_kg <= 0:
        raise ValueError("Weight must be positive.")
    
    # Apply tier structure (check from smallest to largest)
    if weight_kg <= 1:
        return Decimal("4.25")
    if weight_kg <= 2:
        return Decimal("4.95")
    if weight_kg <= 5:
        return Decimal("6.25")
    if weight_kg <= 8:
        return Decimal("7.75")
    
    # For weight > 8kg: base cost + extra per kg
    extra = weight_kg - Decimal("8")
    return Decimal("8.50") + extra * Decimal("0.50")


def compute_fc(weight_kg: Decimal, marketplace: Marketplace) -> Decimal:
    """
    Calculate fulfillment cost for given weight and marketplace.
    
    Purpose:
    - Route to correct FC function based on marketplace
    - Provide single entry point for FC calculations
    
    Args:
        weight_kg: Item weight in kilograms (must be positive)
        marketplace: 'UK' or 'US'
    
    Returns:
        Decimal: Fulfillment cost in marketplace currency (GBP or USD)
    
    Raises:
        ValueError: If weight is zero or negative
    
    Example:
        >>> compute_fc(D('2.0'), 'UK')
        Decimal('3.50')
        >>> compute_fc(D('2.0'), 'US')
        Decimal('4.95')
    
    Note:
        This function routes to fc_uk() or fc_us() based on marketplace.
        Use this function in calculator.py for cleaner code.
    """
    return fc_uk(weight_kg) if marketplace == "UK" else fc_us(weight_kg)


def compute_sc(marketplace: Marketplace, fx_gbp_to_usd: Decimal = Decimal("1.30")) -> Decimal:
    """
    Calculate shipping cost to seller (SC).
    
    Purpose:
    - Our cost to ship inventory to the seller's warehouse
    - Excluded from wholesale quote Q (seller pays separately)
    - Used in ROI calculations to determine seller's total cost
    
    Rates:
    - UK: £0.50 (flat rate)
    - US: £6.00 converted to USD via exchange rate
    
    Args:
        marketplace: 'UK' or 'US'
        fx_gbp_to_usd: GBP to USD exchange rate (default 1.30)
    
    Returns:
        Decimal: Shipping cost in marketplace currency (GBP or USD)
    
    Example:
        >>> compute_sc('UK')
        Decimal('0.50')
        >>> compute_sc('US', fx_gbp_to_usd=D('1.30'))
        Decimal('7.80')  # 6.00 * 1.30
        >>> compute_sc('US', fx_gbp_to_usd=D('1.25'))
        Decimal('7.50')  # 6.00 * 1.25
    
    Note:
        SC is excluded from the wholesale quote Q, but included in S (seller costs).
        This means seller pays SC separately, but it affects their ROI calculation.
        The GBP base of £6.00 for US is converted using the provided exchange rate.
    """
    # UK shipping is a flat rate in GBP
    if marketplace == "UK":
        return Decimal("0.50")
    
    # US shipping: convert GBP base to USD using exchange rate
    return Decimal("6.00") * fx_gbp_to_usd




