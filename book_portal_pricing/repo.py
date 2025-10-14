"""
Repository Interface - Database Access Layer
--------------------------------------------
Purpose:
- Define interface for accessing product and pricing data
- Decouple calculator from specific database implementation
- Support dependency injection for testing

This module defines a Protocol (interface) that any repository must implement.
Your actual database layer should implement this interface.

Usage:
    from book_portal_pricing.repo import Repo
    
    # Implement the Repo protocol for your database
    class SupabaseRepo:
        def __init__(self, session):
            self.session = session
        
        def get_bb_prices_last_30_days(self, product_id, marketplace):
            # Query your database for last 30 days of Buy Box prices
            # Return list of Decimal values (ignore None/null values)
            return [D('19.99'), D('20.50'), ...]
        
        def get_weight_kg(self, product_id):
            # Query your database for product weight
            return D('2.5')
        
        def get_our_cost_c(self, product_id):
            # Query your database for our acquisition cost
            return D('8.00')
"""

from decimal import Decimal
from typing import Protocol, Literal, Sequence

# Type alias for supported marketplaces
Marketplace = Literal["UK", "US"]


class Repo(Protocol):
    """
    Repository interface for accessing product and pricing data.
    
    Purpose:
    - Define contract that any database implementation must follow
    - Enable dependency injection and testing with mock repos
    - Keep calculator logic independent of database details
    
    Implementation Notes:
    - All methods should raise appropriate exceptions on errors
    - get_bb_prices_last_30_days should filter out None/null values
    - All numeric values should be returned as Decimal (not float)
    
    Example Implementation:
        class MockRepo:
            def get_bb_prices_last_30_days(self, product_id, marketplace):
                # Return test data
                return [Decimal('19.99')] * 30
            
            def get_weight_kg(self, product_id):
                return Decimal('2.0')
            
            def get_our_cost_c(self, product_id):
                return Decimal('8.00')
    """
    
    def get_bb_prices_last_30_days(
        self, 
        product_id: str, 
        marketplace: Marketplace
    ) -> Sequence[Decimal]:
        """
        Retrieve last 30 days of Buy Box prices for a product.
        
        Purpose:
        - Fetch daily Buy Box prices to calculate 30-day average
        - Filter out any None/null values (missing data days)
        - Return values as Decimal for precise calculations
        
        Args:
            product_id: Product identifier (e.g., ASIN)
            marketplace: 'UK' or 'US'
        
        Returns:
            Sequence[Decimal]: Up to 30 daily Buy Box prices (None values filtered out)
        
        Example:
            >>> repo.get_bb_prices_last_30_days('B0ABCD1234', 'UK')
            [Decimal('19.99'), Decimal('20.50'), ...]
        
        Note:
            - May return fewer than 30 values if data is unavailable
            - Must filter out None/null values before returning
            - Calculator will compute simple mean of returned values
        """
        ...
    
    def get_weight_kg(self, product_id: str, marketplace: str = None) -> Decimal:
        """
        Get product weight in kilograms.
        
        Purpose:
        - Retrieve weight for fulfillment cost tier calculation
        - Must be positive and non-zero
        
        Args:
            product_id: Product identifier (e.g., ASIN)
            marketplace: 'UK' or 'US' (optional, for matching by both ASIN & marketplace)
        
        Returns:
            Decimal: Weight in kilograms (must be > 0)
        
        Example:
            >>> repo.get_weight_kg('143914995X', 'US')
            Decimal('1.20')
        
        Note:
            Weight is used to determine FC tier.
            Must be converted to kg if stored in other units.
            SupabaseRepo uses public.products.package_weight
        """
        ...
    
    def get_our_cost_c(self, product_id: str, marketplace: str = None) -> Decimal:
        """
        Get our acquisition cost for the product.
        
        Purpose:
        - Retrieve our cost basis for ROI calculations
        - This is the price we pay to acquire the product
        
        Args:
            product_id: Product identifier (e.g., ASIN)
            marketplace: 'UK' or 'US' (optional, for matching by both ASIN & marketplace)
        
        Returns:
            Decimal: Our acquisition cost in marketplace currency
        
        Example:
            >>> repo.get_our_cost_c('143914995X', 'US')
            Decimal('17.90')
        
        Note:
            - This is 'C' in the ROI formulas
            - Should be in same currency as marketplace (GBP for UK, USD for US)
            - Our ROI = (Q - C) / C
            - SupabaseRepo uses public.products.our_price
        """
        ...

