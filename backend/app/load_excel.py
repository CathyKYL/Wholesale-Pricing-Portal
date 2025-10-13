"""
Excel Data Loader
-----------------
Purpose:
- Read Excel file specified in EXCEL_PATH environment variable
- Clean and validate data before inserting into database
- Convert currency strings (£44.95) to decimal numbers
- Handle missing/invalid data gracefully
- Insert data into catalog_rows table

Safe to run multiple times (checks for duplicates based on title+author).
"""

import os
import sys
import pandas as pd
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import SQLAlchemyError

# Import database session and models
from db import SessionLocal, init_db
from models import CatalogRow

# Import centralized configuration (works in both local and cloud)
from config import settings


def clean_currency(value):
    """
    Clean Currency String to Decimal
    ---------------------------------
    Converts currency strings to Decimal objects.
    
    Examples:
        "£44.95" → Decimal("44.95")
        "£1,234.56" → Decimal("1234.56")
        "N/A" → None
        NaN → None
        "" → None
    
    Args:
        value: The value to clean (string, float, int, or NaN)
    
    Returns:
        Decimal or None: Cleaned decimal value or None if invalid/empty
    """
    
    # If value is NaN or None, return None
    if pd.isna(value) or value is None:
        return None
    
    # Convert to string and strip whitespace
    value_str = str(value).strip()
    
    # Check for empty string or "N/A"
    if value_str == "" or value_str.upper() == "N/A":
        return None
    
    # Remove currency symbols and commas
    # Example: "£1,234.56" becomes "1234.56"
    cleaned = value_str.replace("£", "").replace("$", "").replace(",", "").strip()
    
    try:
        # Convert to Decimal (precise decimal representation)
        # Using Decimal instead of float avoids precision errors
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        # If conversion fails, return None
        print(f"⚠️  Warning: Could not convert '{value_str}' to decimal, using None")
        return None


def clean_integer(value):
    """
    Clean Integer Value
    -------------------
    Converts various inputs to integer or None.
    
    Examples:
        123 → 123
        "456" → 456
        12.0 → 12
        NaN → None
        "" → None
    
    Args:
        value: The value to clean
    
    Returns:
        int or None: Cleaned integer value or None if invalid/empty
    """
    
    # If value is NaN or None, return None
    if pd.isna(value) or value is None:
        return None
    
    # Convert to string and strip whitespace
    value_str = str(value).strip()
    
    # Check for empty string or "N/A"
    if value_str == "" or value_str.upper() == "N/A":
        return None
    
    try:
        # Convert to float first (handles "12.0"), then to int
        return int(float(value_str))
    except (ValueError, OverflowError):
        # If conversion fails, return None
        print(f"⚠️  Warning: Could not convert '{value_str}' to integer, using None")
        return None


def clean_string(value):
    """
    Clean String Value
    ------------------
    Cleans string values by stripping whitespace and converting NaN to None.
    
    Examples:
        "  Hello  " → "Hello"
        NaN → None
        "" → None
        123 → "123"
    
    Args:
        value: The value to clean
    
    Returns:
        str or None: Cleaned string or None if empty/NaN
    """
    
    # If value is NaN or None, return None
    if pd.isna(value) or value is None:
        return None
    
    # Convert to string and strip whitespace
    value_str = str(value).strip()
    
    # Return None if empty string
    if value_str == "":
        return None
    
    return value_str


def load_excel_to_db():
    """
    Load Excel Data into Database
    ------------------------------
    Main function that:
    1. Reads Excel file from EXCEL_PATH
    2. Cleans each row's data
    3. Creates CatalogRow objects
    4. Inserts into database
    
    Returns:
        int: Number of rows loaded, or -1 on error
    """
    
    # Get Excel file path from centralized config
    # This works seamlessly in both local (file path) and cloud (S3 URL, etc.)
    excel_path = settings.EXCEL_PATH
    
    if not excel_path:
        print("❌ ERROR: EXCEL_PATH not found in environment variables")
        print("→ Add to .env file: EXCEL_PATH=Data.xlsx")
        print("→ Or set EXCEL_PATH environment variable in cloud platform")
        return -1
    
    # Check if file exists
    if not os.path.exists(excel_path):
        abs_path = os.path.abspath(excel_path)
        print(f"❌ ERROR: Excel file not found at '{excel_path}'")
        print(f"   Expected at: {abs_path}")
        return -1
    
    print(f"📂 Reading Excel file: {excel_path}")
    
    try:
        # Read Excel file using pandas
        # This creates a DataFrame (like a table in memory)
        df = pd.read_excel(excel_path)
        
        print(f"📊 Found {len(df)} rows in Excel file")
        
    except Exception as e:
        print(f"❌ ERROR: Could not read Excel file: {e}")
        print("→ Make sure openpyxl is installed: pip install openpyxl")
        return -1
    
    # Normalize column names to lowercase for easier matching
    # "UK ASIN" → "uk asin"
    df.columns = df.columns.str.lower().str.strip()
    
    # Validate required columns exist
    required_cols = {"title"}  # Only title is required
    expected_cols = {"uk asin", "us asin", "title", "available stock", "author", "rrp", "our prices"}
    
    missing_cols = expected_cols - set(df.columns)
    if missing_cols:
        print(f"❌ ERROR: Missing columns in Excel: {missing_cols}")
        print(f"   Found columns: {list(df.columns)}")
        return -1
    
    # Create database session
    session = SessionLocal()
    
    try:
        # Counter for successfully loaded rows
        loaded_count = 0
        skipped_count = 0
        
        # Process each row in the Excel file
        # IMPORTANT: Each Excel row can create 1 or 2 database rows
        # - If only UK ASIN: 1 row with marketplace='UK'
        # - If only US ASIN: 1 row with marketplace='US'
        # - If both ASINs: 2 rows (one UK, one US)
        for idx, row in df.iterrows():
            
            # Clean each field according to its type
            title = clean_string(row.get("title"))
            
            # Skip rows without a title (title is required)
            if not title:
                print(f"⚠️  Skipping row {idx + 2} - no title")
                skipped_count += 1
                continue
            
            # Get both ASINs
            uk_asin = clean_string(row.get("uk asin"))
            us_asin = clean_string(row.get("us asin"))
            
            # Skip if no ASINs at all
            if not uk_asin and not us_asin:
                print(f"⚠️  Skipping row {idx + 2} - no ASIN (UK or US)")
                skipped_count += 1
                continue
            
            # Common fields for both marketplaces
            author = clean_string(row.get("author"))
            available_stock = clean_integer(row.get("available stock"))
            rrp = clean_currency(row.get("rrp"))
            our_price = clean_currency(row.get("our prices"))  # Note: column is "our prices" (plural)
            
            # ===== Process UK ASIN (if exists) =====
            if uk_asin:
                # Check if this ASIN already exists in UK marketplace
                existing_uk = session.query(CatalogRow).filter(
                    CatalogRow.asin == uk_asin,
                    CatalogRow.marketplace == 'UK'
                ).first()
                
                if existing_uk:
                    # Update existing UK marketplace entry
                    print(f"🔄 Updating UK: {uk_asin} - {title[:40]}...")
                    existing_uk.title = title
                    existing_uk.author = author
                    existing_uk.available_stock = available_stock
                    existing_uk.rrp = rrp
                    existing_uk.our_price = our_price
                else:
                    # Create new UK marketplace entry
                    print(f"✨ Creating UK: {uk_asin} - {title[:40]}...")
                    uk_row = CatalogRow(
                        asin=uk_asin,
                        marketplace='UK',
                        title=title,
                        author=author,
                        available_stock=available_stock,
                        rrp=rrp,
                        our_price=our_price
                    )
                    session.add(uk_row)
                
                loaded_count += 1
            
            # ===== Process US ASIN (if exists) =====
            if us_asin:
                # Check if this ASIN already exists in US marketplace
                existing_us = session.query(CatalogRow).filter(
                    CatalogRow.asin == us_asin,
                    CatalogRow.marketplace == 'US'
                ).first()
                
                if existing_us:
                    # Update existing US marketplace entry
                    print(f"🔄 Updating US: {us_asin} - {title[:40]}...")
                    existing_us.title = title
                    existing_us.author = author
                    existing_us.available_stock = available_stock
                    existing_us.rrp = rrp
                    existing_us.our_price = our_price
                else:
                    # Create new US marketplace entry
                    print(f"✨ Creating US: {us_asin} - {title[:40]}...")
                    us_row = CatalogRow(
                        asin=us_asin,
                        marketplace='US',
                        title=title,
                        author=author,
                        available_stock=available_stock,
                        rrp=rrp,
                        our_price=our_price
                    )
                    session.add(us_row)
                
                loaded_count += 1
        
        # Commit all changes to database (bulk insert)
        # This is faster than committing each row individually
        session.commit()
        
        print(f"✅ Loaded {loaded_count} rows into catalog_rows")
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} rows (missing title)")
        
        return loaded_count
        
    except SQLAlchemyError as e:
        # If there's a database error, rollback all changes
        session.rollback()
        print(f"❌ ERROR: Database error occurred: {e}")
        return -1
        
    except Exception as e:
        # If there's any other error, rollback all changes
        session.rollback()
        print(f"❌ ERROR: Unexpected error: {e}")
        return -1
        
    finally:
        # Always close the session (returns connection to pool)
        session.close()


# Allow this script to be run directly
if __name__ == "__main__":
    print("\n📥 Excel to Database Loader\n")
    
    # Initialize database tables
    init_db()
    
    # Load data
    result = load_excel_to_db()
    
    # Exit with appropriate code
    if result >= 0:
        print("\n✅ Load complete!")
        sys.exit(0)
    else:
        print("\n❌ Load failed!")
        sys.exit(1)

