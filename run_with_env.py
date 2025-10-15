"""
Load .env file and run Python script with environment variables
----------------------------------------------------------------
This helper loads your .env file and makes variables available to other scripts.
"""

import os
import sys
from pathlib import Path

# Load .env file
env_file = Path('.env')

if env_file.exists():
    print("📂 Loading environment variables from .env...")
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                os.environ[key] = value
                # Show loaded (but hide sensitive values)
                if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key or 'TOKEN' in key:
                    print(f"  ✓ {key}=***hidden***")
                else:
                    print(f"  ✓ {key}={value[:40]}...")
    print()
else:
    print("❌ .env file not found!")
    sys.exit(1)

# Check if SUPABASE vars are set
if 'SUPABASE_URL' not in os.environ or 'SUPABASE_KEY' not in os.environ:
    print("⚠️  WARNING: SUPABASE_URL or SUPABASE_KEY not found in .env")
    print()
    print("Your .env file needs these variables:")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_KEY=your-anon-or-service-role-key")
    print()
    print("To find these values:")
    print("  1. Go to your Supabase project dashboard")
    print("  2. Click 'Settings' → 'API'")
    print("  3. Copy 'Project URL' → SUPABASE_URL")
    print("  4. Copy 'anon public' or 'service_role' key → SUPABASE_KEY")
    print()
    sys.exit(1)

print("✅ Environment variables loaded successfully!")
print()

# Run the test script
print("=" * 80)
print("Running test_supabase_quote.py with loaded environment...")
print("=" * 80)
print()

# Import and run the test
import test_supabase_quote
test_supabase_quote.main()




