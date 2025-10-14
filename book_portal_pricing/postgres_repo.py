"""
PostgreSQL Repository Implementation - Direct Database Connection
------------------------------------------------------------------
Purpose:
- Implement Repo protocol using direct PostgreSQL connection
- Use existing DATABASE_URL (no Supabase API needed)
- Pull all product data from database tables directly

This is an alternative to SupabaseRepo that uses PostgreSQL directly.
Perfect when you already have DATABASE_URL configured!

Schema Mapping:
- public.products: our_price, package_weight, asin, marketplace
- Backfill_test.dynamic_data: buy_box_price, date (30-day history)
"""

from decimal import Decimal
from typing import Sequence, Literal
from statistics import mean
import os

Marketplace = Literal["UK", "US"]


class PostgresRepo:
    """
    Repository implementation using direct PostgreSQL connection.
    
    Purpose:
    - Connect to PostgreSQL database directly
    - No Supabase API key needed
    - Uses DATABASE_URL from .env
    
    Data Sources:
    - public.products: Static product data (cost, weight, ASIN, marketplace)
    - Backfill_test.dynamic_data: Historical Buy Box prices
    
    Usage:
        import os
        from book_portal_pricing.postgres_repo import PostgresRepo
        
        database_url = os.getenv("DATABASE_URL")
        repo = PostgresRepo(database_url)
        
        # Get data for a product
        bb_avg = repo.get_avg_bb_price('143914995X', 'US')
        cost = repo.get_our_cost_c('143914995X', 'US')
        weight = repo.get_weight_kg('143914995X', 'US')
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize repository with PostgreSQL connection.
        
        Args:
            database_url: PostgreSQL connection string
                         If None, reads from DATABASE_URL env variable
        
        Example:
            # From environment variable
            repo = PostgresRepo()
            
            # Or explicit URL
            repo = PostgresRepo("postgresql://user:pass@host:5432/db")
        
        Raises:
            ImportError: If psycopg2 not installed
            ValueError: If database_url not provided and not in environment
        """
        # Import psycopg2
        try:
            import psycopg2
            import psycopg2.extras
            self.psycopg2 = psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 not installed. Install with: pip install psycopg2-binary"
            )
        
        # Get database URL
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            raise ValueError(
                "DATABASE_URL not provided. Set it in .env or pass to constructor."
            )
        
        self.database_url = database_url
        
        # Test connection
        try:
            conn = self._get_connection()
            conn.close()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
    
    def _get_connection(self):
        """Get database connection."""
        return self.psycopg2.connect(self.database_url)
    
    def get_our_cost_c(self, product_id: str, marketplace: str = None) -> Decimal:
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
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Query public.catalog_rows for our_price
            if marketplace:
                cursor.execute(
                    "SELECT our_price FROM public.catalog_rows WHERE asin = %s AND marketplace = %s LIMIT 1",
                    (product_id, marketplace)
                )
            else:
                cursor.execute(
                    "SELECT our_price FROM public.catalog_rows WHERE asin = %s LIMIT 1",
                    (product_id,)
                )
            
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(
                    f"Product not found: ASIN={product_id}" +
                    (f", Marketplace={marketplace}" if marketplace else "")
                )
            
            our_price = result[0]
            
            if our_price is None:
                raise ValueError(
                    f"our_price is NULL for ASIN={product_id}"
                )
            
            return Decimal(str(our_price))
            
        finally:
            conn.close()
    
    def get_weight_kg(self, product_id: str, marketplace: str = None) -> Decimal:
        """
        Get product weight from public.products.package_weight.
        
        Purpose:
        - Fetch weight used for fulfilment cost (FC) tier calculation
        - Weight determines which FC tier applies
        
        Args:
            product_id: Product ASIN identifier
            marketplace: 'UK' or 'US' (optional)
        
        Returns:
            Decimal: Weight in kilograms (must be > 0)
        
        Raises:
            ValueError: If product not found or weight is null/invalid
        
        Example:
            >>> repo.get_weight_kg('143914995X', 'US')
            Decimal('1.20')
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Query public.catalog_rows for package_weight
            if marketplace:
                cursor.execute(
                    "SELECT package_weight FROM public.catalog_rows WHERE asin = %s AND marketplace = %s LIMIT 1",
                    (product_id, marketplace)
                )
            else:
                cursor.execute(
                    "SELECT package_weight FROM public.catalog_rows WHERE asin = %s LIMIT 1",
                    (product_id,)
                )
            
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(
                    f"Product not found: ASIN={product_id}" +
                    (f", Marketplace={marketplace}" if marketplace else "")
                )
            
            package_weight = result[0]
            
            if package_weight is None:
                raise ValueError(
                    f"package_weight is NULL for ASIN={product_id}"
                )
            
            weight = Decimal(str(package_weight))
            
            if weight <= 0:
                raise ValueError(
                    f"Invalid weight ({weight} kg) for ASIN={product_id}. Must be > 0."
                )
            
            return weight
            
        finally:
            conn.close()
    
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
        
        Note:
            - Orders by date DESC to get most recent prices first
            - Filters out NULL buy_box_price values
            - May return fewer than 30 if insufficient data
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Query backfill_test.dynamic_data for current_buybox_price
            cursor.execute(
                """
                SELECT current_buybox_price 
                FROM backfill_test.dynamic_data 
                WHERE asin = %s 
                  AND marketplace = %s 
                  AND current_buybox_price IS NOT NULL
                ORDER BY fetch_date DESC 
                LIMIT 30
                """,
                (product_id, marketplace)
            )
            
            results = cursor.fetchall()
            
            if not results:
                raise ValueError(
                    f"No Buy Box data available for ASIN={product_id}, Marketplace={marketplace}"
                )
            
            # Convert to Decimal
            prices = [Decimal(str(row[0])) for row in results]
            
            return prices
            
        finally:
            conn.close()
    
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
        """
        prices = self.get_bb_prices_last_30_days(product_id, marketplace)
        avg = mean(prices)
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
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)
            
            cursor.execute("SELECT asin, marketplace FROM public.catalog_rows")
            
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        finally:
            conn.close()

