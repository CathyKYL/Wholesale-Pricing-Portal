"""
Add SUPABASE_URL and SUPABASE_KEY to .env file
-----------------------------------------------
This script helps you add the missing Supabase variables to your .env
"""

import os
import re

# Read current .env
with open('.env', 'r') as f:
    env_content = f.read()

# Check if already has SUPABASE vars
if 'SUPABASE_URL' in env_content and 'SUPABASE_KEY' in env_content:
    print("✅ SUPABASE_URL and SUPABASE_KEY already in .env!")
    exit(0)

# Try to extract project ID from DATABASE_URL
project_id = None
database_url_match = re.search(r'postgres\.(\w+)\.supabase\.com', env_content)
if not database_url_match:
    # Try pooler format
    database_url_match = re.search(r'postgres\.(\w+):', env_content)

if database_url_match:
    project_id = database_url_match.group(1)
    print(f"📊 Detected Supabase project ID: {project_id}")
    print()

# Prepare new variables
new_lines = []

if project_id:
    supabase_url = f"https://{project_id}.supabase.co"
    new_lines.append(f"\n# Supabase API Configuration (for quote calculator)")
    new_lines.append(f"SUPABASE_URL={supabase_url}")
    print(f"✓ Generated SUPABASE_URL: {supabase_url}")
else:
    new_lines.append(f"\n# Supabase API Configuration (for quote calculator)")
    new_lines.append(f"SUPABASE_URL=https://your-project-id.supabase.co  # TODO: Replace with your actual URL")
    print("⚠️  Could not auto-detect URL. Please update manually.")

print()
print("⚠️  IMPORTANT: You need to add your SUPABASE_KEY manually!")
print()
print("To get your Supabase API key:")
print("  1. Go to https://supabase.com/dashboard/project/{your-project}")
print("  2. Click 'Settings' (⚙️) in sidebar")
print("  3. Click 'API' section")
print("  4. Copy either:")
print("     - 'anon' 'public' key (for frontend/safe operations)")
print("     - 'service_role' 'secret' key (for backend/admin operations)")
print()
print("Then add to your .env file:")
print("  SUPABASE_KEY=your-copied-key-here")
print()

# Ask for confirmation
response = input("Add SUPABASE_URL to .env now? (y/n): ")

if response.lower() == 'y':
    with open('.env', 'a', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
        f.write('\nSUPABASE_KEY=your-key-here  # TODO: Get from Supabase Dashboard > Settings > API\n')
    
    print()
    print("✅ Added to .env!")
    print()
    print("📝 Next steps:")
    print("  1. Open .env file")
    print("  2. Replace 'your-key-here' with your actual Supabase API key")
    print("  3. Save the file")
    print("  4. Run: python run_with_env.py")
    print()
else:
    print()
    print("Cancelled. Add these lines to your .env manually:")
    print()
    for line in new_lines:
        print(line)
    print("SUPABASE_KEY=your-key-here")
    print()

