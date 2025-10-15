"""Check ASINs in public.catalog_rows vs keepa_ingestor configuration"""
from sqlalchemy import create_engine, text
from config import settings
from keepa_ingestor import ASINS_US, ASINS_UK

def main():
    engine = create_engine(settings.DATABASE_URL)
    conn = engine.connect()
    
    print("🔍 CHECKING ASIN CONFIGURATION ALIGNMENT")
    print("=" * 80)
    
    # Get ASINs from public.catalog_rows
    catalog_result = conn.execute(text("""
        SELECT asin, marketplace, title 
        FROM public.catalog_rows 
        ORDER BY asin
    """)).fetchall()
    
    print(f"\n📋 ASINs in public.catalog_rows ({len(catalog_result)} total):")
    print(f"{'ASIN':<15} {'Market':<8} {'Title':<50}")
    print("-" * 80)
    
    catalog_asins = set()
    for r in catalog_result:
        asin, marketplace, title = r
        catalog_asins.add((asin, marketplace))
        print(f"{asin:<15} {marketplace:<8} {str(title)[:47]:<50}")
    
    print(f"\n📋 ASINs in keepa_ingestor.py configuration:")
    print(f"US ASINs ({len(ASINS_US)}): {ASINS_US}")
    print(f"UK ASINs ({len(ASINS_UK)}): {ASINS_UK}")
    
    # Check alignment
    print(f"\n🔍 ALIGNMENT CHECK:")
    
    # Check if catalog ASINs are in configuration
    missing_from_config = []
    for asin, marketplace in catalog_asins:
        if marketplace == 'US' and asin not in ASINS_US:
            missing_from_config.append((asin, marketplace))
        elif marketplace == 'UK' and asin not in ASINS_UK:
            missing_from_config.append((asin, marketplace))
    
    if missing_from_config:
        print(f"❌ ASINs in catalog but NOT in configuration:")
        for asin, marketplace in missing_from_config:
            print(f"   {asin} ({marketplace})")
    else:
        print(f"✅ All catalog ASINs are in configuration")
    
    # Check if config ASINs are in catalog
    extra_in_config = []
    for asin in ASINS_US:
        if (asin, 'US') not in catalog_asins:
            extra_in_config.append((asin, 'US'))
    for asin in ASINS_UK:
        if (asin, 'UK') not in catalog_asins:
            extra_in_config.append((asin, 'UK'))
    
    if extra_in_config:
        print(f"⚠️  ASINs in configuration but NOT in catalog:")
        for asin, marketplace in extra_in_config:
            print(f"   {asin} ({marketplace})")
    else:
        print(f"✅ All configuration ASINs are in catalog")
    
    # Check the problematic ASINs specifically
    problematic_asins = [
        '1546103597', '1637995059', '2067955810', '163799673X', '163799897X', 
        'B0F38CZDDF', 'B0FCFLLM8L', '0114850003', '4027876040', '9124233684', 
        '070234236X', '912424788X'
    ]
    
    print(f"\n🎯 PROBLEMATIC ASINs CHECK:")
    for asin in problematic_asins:
        in_catalog = any(asin == cat_asin for cat_asin, _ in catalog_asins)
        in_config_us = asin in ASINS_US
        in_config_uk = asin in ASINS_UK
        
        print(f"   {asin}: Catalog={in_catalog}, Config_US={in_config_us}, Config_UK={in_config_uk}")
    
    conn.close()

if __name__ == "__main__":
    main()




