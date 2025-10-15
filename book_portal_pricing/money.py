"""
Money Utilities - Decimal-Based Currency Math
----------------------------------------------
Purpose:
- Provide safe, precise decimal arithmetic for money calculations
- Avoid floating-point rounding errors
- Round consistently to penny precision

All monetary values in this package use Python's Decimal type.
This ensures accurate calculations without floating-point drift.

Usage:
    from book_portal_pricing.money import D, to_penny, pct, mul_pct
    
    # Create a Decimal from string or number
    price = D('19.99')
    
    # Round to penny precision
    rounded = to_penny(D('19.999'))  # Returns Decimal('20.00')
    
    # Convert decimal to percentage (0.15 → 15.00)
    roi_pct = pct(D('0.15'))  # Returns Decimal('15.00')
    
    # Multiply amount by percentage and round to penny
    fee = mul_pct(D('100.00'), D('0.17'))  # Returns Decimal('17.00')
"""

from decimal import Decimal, ROUND_HALF_UP, getcontext

# Set precision to 12 decimal places for intermediate calculations
# This ensures accuracy for complex ROI calculations
getcontext().prec = 12


def D(x) -> Decimal:
    """
    Convert a number or string to Decimal.
    
    Purpose:
    - Safely create Decimal values from any input type
    - Avoid floating-point representation errors
    
    Args:
        x: Number, string, or Decimal to convert
    
    Returns:
        Decimal: Precise decimal representation
    
    Example:
        >>> D(19.99)
        Decimal('19.99')
        >>> D('0.17')
        Decimal('0.17')
    
    Note:
        Always use strings for exact values to avoid float precision issues.
        D('0.1') is better than D(0.1) because 0.1 cannot be represented exactly as a float.
    """
    return Decimal(str(x))


def to_penny(d: Decimal) -> Decimal:
    """
    Round a Decimal to penny precision (2 decimal places).
    
    Purpose:
    - Ensure all money values are rounded to cents/pence
    - Use ROUND_HALF_UP (standard banking rounding)
    
    Args:
        d: Decimal value to round
    
    Returns:
        Decimal: Value rounded to 2 decimal places
    
    Example:
        >>> to_penny(D('19.999'))
        Decimal('20.00')
        >>> to_penny(D('5.555'))
        Decimal('5.56')
    
    Note:
        Uses ROUND_HALF_UP: 0.5 rounds up to 1, -0.5 rounds up to 0.
        This is the standard rounding method for currency.
    """
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def pct(d: Decimal) -> Decimal:
    """
    Convert a decimal ratio to percentage (e.g., 0.15 → 15.00).
    
    Purpose:
    - Display ROI and margin values as percentages
    - Round to 2 decimal places for readability
    
    Args:
        d: Decimal ratio (e.g., 0.15 for 15%)
    
    Returns:
        Decimal: Percentage value with 2 decimal places
    
    Example:
        >>> pct(D('0.15'))
        Decimal('15.00')
        >>> pct(D('0.3542'))
        Decimal('35.42')
    
    Note:
        The input is a decimal ratio, not a percentage.
        0.15 represents 15%, not 0.15%.
    """
    return (d * Decimal("100")).quantize(Decimal("0.01"))


def mul_pct(amount: Decimal, rate: Decimal) -> Decimal:
    """
    Multiply an amount by a percentage rate and round to penny.
    
    Purpose:
    - Calculate fees, margins, and other percentage-based values
    - Ensure result is rounded to penny precision
    
    Args:
        amount: Base amount (e.g., £100.00)
        rate: Percentage rate as decimal (e.g., 0.17 for 17%)
    
    Returns:
        Decimal: Product rounded to 2 decimal places
    
    Example:
        >>> mul_pct(D('100.00'), D('0.17'))
        Decimal('17.00')
        >>> mul_pct(D('25.50'), D('0.15'))
        Decimal('3.83')
    
    Note:
        This is equivalent to: to_penny(amount * rate)
        Useful for calculating fees like Amazon's 17% commission.
    """
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)




