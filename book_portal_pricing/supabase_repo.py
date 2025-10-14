"""
Supabase Repository Implementation - Live Database Integration
---------------------------------------------------------------
Purpose:
- Implement Repo protocol using live Supabase data
- Pull all product data from actual database tables
- No random or hardcoded values

Schema Mapping:
- public.products: our_price, package_weight, asin, marketplace
- Backfill_test.dynamic_data: buy_box_price, date (30-day history)
"""

from decimal import Decimal
from typing import Sequence, Literal
from statistics import mean

Marketplace = Literal["UK", "US"]


class SupabaseRepo:
    """
    Repository implementation using live Supabase data.
    
    Purpose:
    - Connect to Supabase and fetch real product data
    - Implement Repo protocol for calculator integration
    - Pull Buy Box history from Backfill_test schema
    
    Data Sources:
    - public.products: Static product data (cost, weight, ASIN, marketplace)
    - Backfill_test.dynamic_data: Historical Buy Box prices
    
    Usage:
        from supabase import create_client
        from book_portal_pricing.supabase_repo import SupabaseRepo
        
        client = create_client(url, key)
        repo = SupabaseRepo(client)
        
        # Get data for a product
        bb_avg = repo.get_avg_bb_price('B0ABCD1234', 'UK')
        cost = repo.get_our_cost_c('B0ABCD1234', 'UK')
        weight = repo.get_weight_kg('B0ABCD1234', 'UK')
    """
    
    def __init__(self, client):
        """
        Initialize repository with Supabase client.
        
        Args:
            client: Authenticated Supabase client instance
        
        Example:
            from supabase import create_client
            import os
            
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            client = create_client(url, key)
            
            repo = SupabaseRepo(client)
        """
        self.client = client
    
    def get_our_cost_c(self, product_id: str, marketplace: str) -> Decimal:
        """
        Get our acquisition cost (C) from public.products.our_price.
        
        Purpose:
        - Fetch our wholesale acquisition cost for the book
        - This is 'C' in the ROI formulas
        
        Args:
            product_id: Product ASIN identifier
            marketplace: 'UK' or 'US'
        
        Returns:
            Decimal: Our acquisition cost in marketplace currency
        
        Raises:
            ValueError: If product not found or our_price is null
        
        Example:
            >>> repo.get_our_cost_c('143914995X', 'US')
            Decimal('17.90')
        
        Database Query:
            SELECT our_price FROM public.products
            WHERE asin = 'ASIN' AND marketplace = 'UK'
            LIMIT 1
        """
        try:
            # Query public.products table for our_price
            result = self.client.table("products") \
                .select("our_price") \
                .eq("asin", product_id) \
                .eq("marketplace", marketplace) \
                .limit(1) \
                .execute()
            
            # Check if product found
            if not result.data or len(result.data) == 0:
                raise ValueError(
                    f"Product not found: ASIN={product_id}, Marketplace={marketplace}"
                )
            
            # Extract our_price
            our_price = result.data[0]["our_price"]
            
            if our_price is None:
                raise ValueError(
                    f"our_price is NULL for ASIN={product_id}, Marketplace={marketplace}"
                )
            
            # Convert to Decimal for precise calculations
            return Decimal(str(our_price))
            
        except Exception as e:
            raise ValueError(
                f"Error fetching our_price for {product_id} ({marketplace}): {str(e)}"
            )
    
    def get_weight_kg(self, product_id: str, marketplace: str = None) -> Decimal:
        """
        Get product weight from public.products.package_weight.
        
        Purpose:
        - Fetch weight used for fulfilment cost (FC) tier calculation
        - Weight determines which FC tier applies
        
        Args:
            product_id: Product ASIN identifier
            marketplace: 'UK' or 'US' (optional, for matching)
        
        Returns:
            Decimal: Weight in kilograms (must be > 0)
        
        Raises:
            ValueError: If product not found or weight is null/invalid
        
        Example:
            >>> repo.get_weight_kg('143914995X', 'US')
            Decimal('1.20')
        
        Database Query:
            SELECT package_weight FROM public.products
            WHERE asin = 'ASIN' [AND marketplace = 'UK']
            LIMIT 1
        
        Note:
            Weight should be positive. Invalid weights will raise an error.
        """
        try:
            # Build query
            query = self.client.table("products").select("package_weight").eq("asin", product_id)
            
            # Add marketplace filter if provided
            if marketplace:
                query = query.eq("marketplace", marketplace)
            
            result = query.limit(1).execute()
            
            # Check if product found
            if not result.data or len(result.data) == 0:
                raise ValueError(
                    f"Product not found: ASIN={product_id}" + 
                    (f", Marketplace={marketplace}" if marketplace else "")
                )
            
            # Extract package_weight
            package_weight = result.data[0]["package_weight"]
            
            if package_weight is None:
                raise ValueError(
                    f"package_weight is NULL for ASIN={product_id}"
                )
            
            # Convert to Decimal
            weight = Decimal(str(package_weight))
            
            # Validate weight is positive
            if weight <= 0:
                raise ValueError(
                    f"Invalid weight ({weight} kg) for ASIN={product_id}. Must be > 0."
                )
            
            return weight
            
        except Exception as e:
            raise ValueError(
                f"Error fetching package_weight for {product_id}: {str(e)}"
            )
    
    def get_bb_prices_last_30_days(
        self, 
        product_id: str, 
        marketplace: Marketplace
    ) -> Sequence[Decimal]:
        """
        Get last 30 non-null daily Buy Box prices from Backfill_test.dynamic_data.
        
        Purpose:
        - Fetch historical Buy Box prices for calculating 30-day average
        - Filter out null values (missing data days)
        - Match by both ASIN and marketplace
        
        Args:
            product_id: Product ASIN identifier
            marketplace: 'UK' or 'US'
        
        Returns:
            Sequence[Decimal]: Up to 30 daily Buy Box prices (nulls filtered)
        
        Raises:
            ValueError: If no Buy Box data available
        
        Example:
            >>> prices = repo.get_bb_prices_last_30_days('143914995X', 'US')
            >>> len(prices)
            30
            >>> prices[0]
            Decimal('23.45')
        
        Database Query:
            SELECT buy_box_price FROM Backfill_test.dynamic_data
            WHERE asin = 'ASIN' AND marketplace = 'UK'
            ORDER BY date DESC
            LIMIT 30
        
        Note:
            - Orders by date DESC to get most recent prices first
            - Filters out NULL buy_box_price values
            - May return fewer than 30 if insufficient data
        """
        try:
            # Query Backfill_test.dynamic_data table
            # Note: Using .schema() to specify non-default schema
            result = self.client.schema("Backfill_test") \
                .table("dynamic_data") \
                .select("buy_box_price") \
                .eq("asin", product_id) \
                .eq("marketplace", marketplace) \
                .order("date", desc=True) \
                .limit(30) \
                .execute()
            
            # Filter out null values and convert to Decimal
            prices = [
                Decimal(str(row["buy_box_price"])) 
                for row in result.data 
                if row["buy_box_price"] is not None
            ]
            
            # Validate we have data
            if not prices or len(prices) == 0:
                raise ValueError(
                    f"No Buy Box data available for ASIN={product_id}, Marketplace={marketplace}"
                )
            
            return prices
            
        except Exception as e:
            raise ValueError(
                f"Error fetching Buy Box prices for {product_id} ({marketplace}): {str(e)}"
            )
    
    def get_avg_bb_price(self, product_id: str, marketplace: str) -> Decimal:
        """
        Calculate 30-day average Buy Box price (BB̄).
        
        Purpose:
        - Compute simple mean of last 30 daily Buy Box prices
        - This is 'BB̄' in the ROI formulas
        
        Args:
            product_id: Product ASIN identifier
            marketplace: 'UK' or 'US'
        
        Returns:
            Decimal: Average Buy Box price over last 30 days
        
        Raises:
            ValueError: If no Buy Box data available
        
        Example:
            >>> bb_avg = repo.get_avg_bb_price('143914995X', 'US')
            >>> bb_avg
            Decimal('23.45')
        
        Formula:
            BB̄ = mean(last 30 non-null daily Buy Box prices)
        
        Note:
            - Rounds to 2 decimal places (penny precision)
            - Uses simple arithmetic mean
        """
        # Fetch last 30 prices
        prices = self.get_bb_prices_last_30_days(product_id, marketplace)
        
        # Calculate mean
        avg = mean(prices)
        
        # Round to 2 decimal places and return as Decimal
        return Decimal(str(round(avg, 2)))
    
    def list_all_products(self) -> list:
        """
        List all products from public.products table.
        
        Purpose:
        - Get all ASIN + Marketplace combinations for batch processing
        - Used for generating reports with all products
        
        Returns:
            list: List of dicts with 'asin' and 'marketplace' keys
        
        Example:
            >>> products = repo.list_all_products()
            >>> len(products)
            38
            >>> products[0]
            {'asin': '143914995X', 'marketplace': 'US'}
        
        Database Query:
            SELECT asin, marketplace FROM public.products
        
        Note:
            Returns all products in database (no filtering).
        """
        try:
            result = self.client.table("products") \
                .select("asin, marketplace") \
                .execute()
            
            return result.data
            
        except Exception as e:
            raise ValueError(f"Error listing products: {str(e)}")



