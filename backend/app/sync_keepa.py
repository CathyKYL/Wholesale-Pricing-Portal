"""
Keepa Data Sync Script
----------------------
Purpose:
- Fetch product metadata from Keepa API for all catalog items
- Update database with ISBN, images, dimensions, weight
- Can filter by marketplace or sync everything

Usage:
    # Sync all items
    python sync_keepa.py
    
    # Sync only US items
    python sync_keepa.py --marketplace US
    
    # Sync only UK items
    python sync_keepa.py --marketplace UK
    
    # Sync first 10 items (for testing)
    python sync_keepa.py --limit 10
"""

import sys
import argparse
from keepa_integration import update_catalog_with_keepa

def main():
    """
    Main function to run Keepa sync
    Parses command line arguments and runs the update
    """
    
    # Set up command line argument parser
    parser = argparse.ArgumentParser(
        description='Sync catalog with Keepa API data'
    )
    
    # Add optional marketplace filter argument
    parser.add_argument(
        '--marketplace',
        type=str,
        choices=['US', 'UK'],
        help='Filter by marketplace (US or UK). If not specified, syncs all.'
    )
    
    # Add optional limit argument (useful for testing)
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of items to update (useful for testing)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the update
    print("\n🚀 Starting Keepa Sync...")
    print("=" * 70)
    
    if args.marketplace:
        print(f"📌 Marketplace filter: {args.marketplace}")
    else:
        print(f"📌 No marketplace filter (syncing all)")
    
    if args.limit:
        print(f"📌 Limit: {args.limit} items")
    
    print()
    
    try:
        # Call the update function from our integration module
        updated_count = update_catalog_with_keepa(
            marketplace=args.marketplace,
            limit=args.limit
        )
        
        if updated_count > 0:
            print(f"\n✅ Success! Updated {updated_count} catalog items with Keepa data")
            sys.exit(0)
        else:
            print(f"\n⚠️  No items were updated")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Sync interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

