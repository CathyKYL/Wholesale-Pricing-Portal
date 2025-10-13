"""
Smoke Test - End-to-End System Validation
------------------------------------------
Purpose:
- Validate entire system setup from .env to database to data loading
- Run a complete workflow: init DB → load Excel → query data
- Provide clear pass/fail feedback
- Safe to run multiple times

This script tests:
1. Environment variables are configured
2. Database connection works
3. Tables can be created
4. Excel data can be loaded
5. Data can be queried back

Usage:
    python smoke_test.py
"""

import os
import sys
from sqlalchemy import text

# Import our modules
from db import init_db, SessionLocal
from models import CatalogRow
from load_excel import load_excel_to_db

# Import centralized configuration (works in both local and cloud)
from config import settings


def mask_password(url):
    """
    Mask Password in Database URL
    ------------------------------
    Hides the password for security when printing.
    
    Example:
        "postgresql://user:secret123@host:5432/db"
        → "postgresql://user:****@host:5432/db"
    
    Args:
        url (str): The database URL
    
    Returns:
        str: URL with password masked
    """
    if not url:
        return "NOT SET"
    
    # Split by @ to separate credentials from host
    if '@' in url:
        # Split into: protocol://user:pass and host:port/db
        before_at = url.split('@')[0]
        after_at = url.split('@', 1)[1]
        
        # Check if there's a password (contains :)
        if ':' in before_at:
            # Split into: protocol://user and password
            protocol_user = before_at.rsplit(':', 1)[0]
            # Reconstruct with masked password
            return f"{protocol_user}:****@{after_at}"
    
    return url


def print_section(title):
    """
    Print Section Header
    --------------------
    Prints a formatted section title for better readability.
    
    Args:
        title (str): The section title to print
    """
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def main():
    """
    Main Smoke Test Function
    -------------------------
    Runs all validation steps and reports results.
    """
    
    print("\n🧪 SMOKE TEST - Wholesale Pricing Portal")
    print("=" * 70)
    
    # ========== STEP 1: Check Environment Variables ==========
    print_section("STEP 1: Environment Configuration")
    
    db_url = settings.DATABASE_URL
    excel_path = settings.EXCEL_PATH
    environment = settings.ENVIRONMENT
    is_cloud = settings.is_cloud()
    
    print(f"ENVIRONMENT: {environment}")
    print(f"DATABASE_URL: {mask_password(db_url)}")
    print(f"EXCEL_PATH: {excel_path}")
    print(f"RUNNING IN CLOUD: {'Yes' if is_cloud else 'No (Local)'}")
    
    if not db_url:
        print("❌ FAIL: DATABASE_URL not set in environment")
        sys.exit(1)
    
    if not excel_path:
        print("❌ FAIL: EXCEL_PATH not set in environment")
        sys.exit(1)
    
    print("✅ Environment variables configured correctly")
    
    # ========== STEP 2: Initialize Database ==========
    print_section("STEP 2: Database Initialization")
    
    try:
        print("→ Creating tables (idempotent)...")
        init_db()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ FAIL: Could not initialize database: {e}")
        sys.exit(1)
    
    # ========== STEP 3: Load Excel Data ==========
    print_section("STEP 3: Excel Data Loading")
    
    try:
        print("→ Loading Excel data...")
        rows_loaded = load_excel_to_db()
        
        if rows_loaded < 0:
            print("❌ FAIL: Excel loading failed")
            sys.exit(1)
        
        print(f"✅ Loaded {rows_loaded} rows into catalog_rows")
    except Exception as e:
        print(f"❌ FAIL: Error during Excel loading: {e}")
        sys.exit(1)
    
    # ========== STEP 4: Query Sample Data ==========
    print_section("STEP 4: Data Verification")
    
    try:
        # Create a database session
        session = SessionLocal()
        
        # Count total rows
        total_count = session.query(CatalogRow).count()
        print(f"📊 Total rows in database: {total_count}")
        
        if total_count == 0:
            print("⚠️  WARNING: No data in database (this might be expected)")
        
        # Query first 5 rows
        print("\n→ Fetching sample data (first 5 rows)...")
        sample_rows = session.query(CatalogRow).limit(5).all()
        
        if sample_rows:
            print(f"✅ Query returned {len(sample_rows)} rows")
            print("\n📋 Sample Data:")
            print("-" * 70)
            
            for row in sample_rows:
                # Format title (truncate if too long)
                title_display = row.title[:45] + "..." if len(row.title) > 45 else row.title
                
                # Format prices (handle None values)
                rrp_display = f"£{row.rrp:.2f}" if row.rrp else "N/A"
                our_price_display = f"£{row.our_price:.2f}" if row.our_price else "N/A"
                
                print(f"  ID: {row.id}")
                print(f"  ASIN: {row.asin}")
                print(f"  Marketplace: {row.marketplace}")
                print(f"  Title: {title_display}")
                print(f"  Author: {row.author or 'N/A'}")
                print(f"  Stock: {row.available_stock or 'N/A'}")
                print(f"  RRP: {rrp_display} | Our Price: {our_price_display}")
                print("-" * 70)
        else:
            print("⚠️  No data returned (database might be empty)")
        
        # Test a simple aggregation query
        print("\n→ Testing aggregation query...")
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total_items,
                COUNT(CASE WHEN marketplace = 'UK' THEN 1 END) as uk_marketplace_items,
                COUNT(CASE WHEN marketplace = 'US' THEN 1 END) as us_marketplace_items,
                AVG(rrp) as avg_rrp,
                AVG(our_price) as avg_our_price
            FROM catalog_rows
        """)).fetchone()
        
        if result:
            print(f"📊 Database Statistics:")
            print(f"   Total Items: {result.total_items}")
            print(f"   UK Marketplace Items: {result.uk_marketplace_items}")
            print(f"   US Marketplace Items: {result.us_marketplace_items}")
            print(f"   Average RRP: £{float(result.avg_rrp):.2f}" if result.avg_rrp else "N/A")
            print(f"   Average Our Price: £{float(result.avg_our_price):.2f}" if result.avg_our_price else "N/A")
        
        # Close session
        session.close()
        
        print("\n✅ Data verification complete")
        
    except Exception as e:
        print(f"❌ FAIL: Error querying database: {e}")
        sys.exit(1)
    
    # ========== FINAL SUMMARY ==========
    print_section("SMOKE TEST SUMMARY")
    
    print("✅ Environment Configuration: PASS")
    print("✅ Database Initialization: PASS")
    print("✅ Excel Data Loading: PASS")
    print("✅ Data Query & Verification: PASS")
    
    print("\n" + "=" * 70)
    print("🎉 ALL TESTS PASSED - System is healthy and operational!")
    print("=" * 70)
    print("\n📌 Next Steps:")
    print("   • Review the data in pgAdmin to verify accuracy")
    print("   • Ready to build API endpoints (Phase 3)")
    print("   • Ready to integrate Keepa API (Phase 4)")
    print("\n")


# Run the smoke test when script is executed
if __name__ == "__main__":
    try:
        main()
        sys.exit(0)  # Exit with success code
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

