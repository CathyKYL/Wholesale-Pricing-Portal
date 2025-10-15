"""Verify DATABASE_URL format for GitHub Actions"""
import os
from urllib.parse import urlparse

# Load .env
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

print("=" * 80)
print("🔍 VERIFYING DATABASE_URL FORMAT FOR GITHUB ACTIONS")
print("=" * 80)
print()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    print()
    print("   You need to add it to .env file:")
    print("   DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres")
    print()
else:
    print("✅ DATABASE_URL found in .env")
    print()
    
    # Parse the URL
    try:
        parsed = urlparse(DATABASE_URL)
        
        print("📋 DATABASE_URL Details:")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'NOT SET'}")
        print()
        
        # Validate format
        errors = []
        
        if parsed.scheme not in ['postgresql', 'postgres']:
            errors.append(f"❌ Scheme should be 'postgresql' or 'postgres', found '{parsed.scheme}'")
        
        if not parsed.hostname:
            errors.append("❌ Hostname is missing")
        
        if not parsed.port:
            errors.append("❌ Port is missing (should be 5432 for Supabase)")
        elif parsed.port != 5432:
            errors.append(f"⚠️  Port is {parsed.port}, Supabase typically uses 5432")
        
        if not parsed.username:
            errors.append("❌ Username is missing")
        
        if not parsed.password:
            errors.append("❌ Password is missing")
        
        if errors:
            print("🚨 ISSUES FOUND:")
            for error in errors:
                print(f"   {error}")
            print()
        else:
            print("✅ DATABASE_URL format looks correct!")
            print()
            
        # Show what to add to GitHub Secrets
        print("=" * 80)
        print("📝 ADD THIS TO GITHUB SECRETS:")
        print("=" * 80)
        print()
        print("1. Go to: https://github.com/CathyKYL/Wholesale-Pricing-Portal/settings/secrets/actions")
        print()
        print("2. Click 'New repository secret'")
        print()
        print("3. Name: DATABASE_URL")
        print("   Value: (copy your DATABASE_URL from .env file)")
        print()
        print("4. Name: KEEPA_API_KEY")
        print(f"   Value: {os.getenv('KEEPA_API_KEY', 'NOT FOUND IN .ENV')}")
        print()
        
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")

print("=" * 80)

