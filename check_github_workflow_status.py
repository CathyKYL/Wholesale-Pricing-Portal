"""Check GitHub Actions workflow status"""
import requests
import os

# You'll need to set GITHUB_TOKEN in your .env file
# Get it from: https://github.com/settings/tokens

# Load .env
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'CathyKYL'
REPO_NAME = 'Wholesale-Pricing-Portal'

print("=" * 80)
print("🔍 CHECKING GITHUB ACTIONS WORKFLOW STATUS")
print("=" * 80)
print()

if not GITHUB_TOKEN:
    print("⚠️  GITHUB_TOKEN not found in .env")
    print("   To check workflow status programmatically, you need a GitHub token.")
    print("   Get one from: https://github.com/settings/tokens")
    print()
    print("   For now, please check manually:")
    print(f"   👉 https://github.com/{REPO_OWNER}/{REPO_NAME}/actions")
    print()
else:
    # Get recent workflow runs
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            runs = data.get('workflow_runs', [])
            
            print(f"📊 Recent workflow runs:")
            print()
            
            for run in runs[:5]:  # Show last 5 runs
                print(f"   Name: {run['name']}")
                print(f"   Status: {run['status']}")
                print(f"   Conclusion: {run.get('conclusion', 'N/A')}")
                print(f"   Created: {run['created_at']}")
                print(f"   URL: {run['html_url']}")
                print()
        else:
            print(f"❌ GitHub API Error: {response.status_code}")
            print(f"   {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("=" * 80)

