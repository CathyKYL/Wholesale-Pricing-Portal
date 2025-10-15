"""
Extract Supabase URL from DATABASE_URL and guide user to add API key
"""

import re
import os

# Read .env file
with open('.env', 'r', encoding='utf-8') as f:
    env_content = f.read()

# Extract project ID from DATABASE_URL
# Format: postgres.mofhylcyainzwbrcmrqg.supabase.com or pooler.supabase.com
match = re.search(r'postgres\.(\w+)\.supabase\.com|postgres\.(\w+):', env_content)

if match:
    project_id = match.group(1) or match.group(2)
    supabase_url = f"https://{project_id}.supabase.co"
    
    print("=" * 80)
    print("📊 SUPABASE CONFIGURATION DETECTED")
    print("=" * 80)
    print()
    print(f"✅ Project ID: {project_id}")
    print(f"✅ Supabase URL: {supabase_url}")
    print()
    
    # Check if SUPABASE vars already exist
    if 'SUPABASE_URL=' in env_content and 'SUPABASE_KEY=' in env_content:
        # Check if they're not just placeholders
        if 'your-key-here' not in env_content and 'your-project-id' not in env_content:
            print("✅ SUPABASE_URL and SUPABASE_KEY already configured in .env!")
            print()
            print("You can now run:")
            print("  python run_with_env.py")
            exit(0)
    
    print("⚠️  NEXT STEP: Add your Supabase API Key to .env")
    print()
    print("📝 Instructions:")
    print()
    print(f"1. Go to: https://supabase.com/dashboard/project/{project_id}/settings/api")
    print()
    print("2. Copy your API key:")
    print("   • For quote calculator: Copy 'anon' 'public' key")
    print("   • OR for admin operations: Copy 'service_role' key")
    print()
    print("3. Add these TWO lines to your .env file:")
    print()
    print(f"   SUPABASE_URL={supabase_url}")
    print("   SUPABASE_KEY=paste-your-key-here")
    print()
    print("=" * 80)
    print()
    
    # Offer to add SUPABASE_URL automatically
    if 'SUPABASE_URL=' not in env_content:
        response = input("Add SUPABASE_URL to .env automatically? (y/n): ")
        if response.lower() == 'y':
            with open('.env', 'a', encoding='utf-8') as f:
                f.write(f'\n# Supabase API Configuration\n')
                f.write(f'SUPABASE_URL={supabase_url}\n')
                f.write('SUPABASE_KEY=  # TODO: Get from dashboard\n')
            print()
            print("✅ Added SUPABASE_URL to .env!")
            print()
            print("📝 Now manually edit .env and add your SUPABASE_KEY")
            print()
else:
    print("❌ Could not find Supabase connection in DATABASE_URL")
    print()
    print("Please add manually to .env:")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_KEY=your-api-key")




