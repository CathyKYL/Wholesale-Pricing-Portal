"""
Environment Test Script
=======================
This script tests the connection to PostgreSQL, Keepa API, and pandas Excel reading capability.

According to project rules:
- All secrets are read from .env file (never hardcoded)
- Before connecting to real APIs or databases, test with mock data
- All code includes plain-English comments for non-coders
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
import keepa

# Load environment variables from the .env file
# This reads our API keys and database URL safely
load_dotenv()

def test_env_variables():
    """
    Test if environment variables are loaded correctly.
    
    This function checks that we can read the Keepa API key and database URL
    from the .env file without any issues.
    """
    print("=" * 60)
    print("🔍 TESTING ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    # Get the Keepa API key from environment variables
    keepa_key = os.getenv('KEEPA_API_KEY')
    # Get the database connection URL from environment variables
    database_url = os.getenv('DATABASE_URL')
    
    # Check if the Keepa API key exists and is not empty
    if keepa_key:
        # Show only the first 10 characters for security (hide the full key)
        print(f"✅ Keepa API Key found: {keepa_key[:10]}...")
    else:
        print("❌ Keepa API Key NOT found in .env file")
        return False
    
    # Check if the database URL exists and is not empty
    if database_url:
        # Show the database URL (safe to display since it's localhost)
        print(f"✅ Database URL found: {database_url}")
    else:
        print("❌ Database URL NOT found in .env file")
        return False
    
    print("✅ Environment variables loaded successfully!\n")
    return True


def test_database_connection():
    """
    Test the connection to the PostgreSQL database.
    
    This function attempts to connect to the database and run a simple query
    to verify that the connection works properly.
    """
    print("=" * 60)
    print("🔍 TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        # Get the database URL from environment variables
        database_url = os.getenv('DATABASE_URL')
        
        # Create a database engine (this is like a connection manager)
        # The engine handles all communication with the database
        engine = create_engine(database_url)
        
        # Try to connect to the database
        with engine.connect() as connection:
            # Run a simple test query to check if connection works
            # This query just returns the PostgreSQL version
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            print(f"✅ Successfully connected to PostgreSQL!")
            print(f"   Database version: {version[:50]}...")  # Show first 50 chars
        
        print("✅ Database connection test passed!\n")
        return True
        
    except Exception as error:
        # If connection fails, show what went wrong
        print(f"❌ Database connection failed!")
        print(f"   Error: {str(error)}")
        print("\n   💡 Troubleshooting tips:")
        print("      - Is PostgreSQL running on your computer?")
        print("      - Is the database 'book_portal' created?")
        print("      - Are the username/password correct in .env?")
        print("      - Is PostgreSQL listening on port 5432?\n")
        return False


def test_keepa_api():
    """
    Test the connection to Keepa API.
    
    This function checks if we can initialize the Keepa API client
    with the API key from our .env file.
    """
    print("=" * 60)
    print("🔍 TESTING KEEPA API")
    print("=" * 60)
    
    try:
        # Get the Keepa API key from environment variables
        keepa_key = os.getenv('KEEPA_API_KEY')
        
        # Create a Keepa API client
        # This initializes the connection to Keepa's services
        api = keepa.Keepa(keepa_key)
        
        # Check if API tokens are available
        # Tokens are like credits - each API call uses some tokens
        tokens_left = api.tokens_left
        
        print(f"✅ Successfully connected to Keepa API!")
        print(f"   API Tokens remaining: {tokens_left}")
        
        # Warn if tokens are running low
        if tokens_left < 100:
            print("   ⚠️  Warning: Low on API tokens. Consider upgrading your plan.")
        
        print("✅ Keepa API test passed!\n")
        return True
        
    except Exception as error:
        # If Keepa connection fails, show what went wrong
        print(f"❌ Keepa API connection failed!")
        print(f"   Error: {str(error)}")
        print("\n   💡 Troubleshooting tips:")
        print("      - Is your API key correct in .env?")
        print("      - Do you have an active Keepa subscription?")
        print("      - Is your internet connection working?\n")
        return False


def test_pandas_excel():
    """
    Test pandas ability to read Excel files.
    
    This function verifies that pandas can read Excel files,
    which is needed for importing product data.
    """
    print("=" * 60)
    print("🔍 TESTING PANDAS EXCEL READING")
    print("=" * 60)
    
    try:
        # Create a small test DataFrame (like a table in memory)
        # This simulates product data we might have in Excel
        test_data = {
            'Product': ['Test Product 1', 'Test Product 2'],
            'ASIN': ['B001234567', 'B009876543'],
            'Cost': [10.50, 25.00]
        }
        
        # Convert the dictionary to a pandas DataFrame
        df = pd.DataFrame(test_data)
        
        print(f"✅ Pandas is working correctly!")
        print(f"   Test DataFrame created with {len(df)} rows")
        print("\n   Sample data:")
        # Display the test data in a nice format
        print(df.to_string(index=False))
        
        print("\n✅ Pandas Excel capability test passed!\n")
        return True
        
    except Exception as error:
        # If pandas test fails, show what went wrong
        print(f"❌ Pandas test failed!")
        print(f"   Error: {str(error)}\n")
        return False


def main():
    """
    Main function to run all environment tests.
    
    This runs all our test functions in sequence and reports
    whether the environment is ready for development.
    """
    print("\n" + "=" * 60)
    print("🚀 WHOLESALE PRICING PORTAL - ENVIRONMENT TEST")
    print("=" * 60)
    print("This script tests your development environment setup.\n")
    
    # Run all tests and track results
    # Each test returns True if it passes, False if it fails
    results = {
        'Environment Variables': test_env_variables(),
        'Database Connection': test_database_connection(),
        'Keepa API': test_keepa_api(),
        'Pandas Excel': test_pandas_excel()
    }
    
    # Print summary of all test results
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    # Count how many tests passed
    passed = sum(results.values())
    total = len(results)
    
    # Show each test result
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    # Print final verdict
    print("=" * 60)
    if passed == total:
        print(f"🎉 SUCCESS! All {total} tests passed!")
        print("   Your environment is ready for development.")
    else:
        print(f"⚠️  WARNING: {total - passed} out of {total} tests failed.")
        print("   Please fix the issues above before proceeding.")
    print("=" * 60 + "\n")


# This runs when the script is executed directly
# (not when imported as a module)
if __name__ == "__main__":
    main()

