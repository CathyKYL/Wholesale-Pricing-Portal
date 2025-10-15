"""
Test Supabase Connection
-------------------------
Test different connection methods to Supabase.
"""

import sys
from sqlalchemy import create_engine, text

# Try both direct and pooled connections
urls_to_test = [
    # Direct connection (port 5432)
    "postgresql://postgres:2407portal2407@db.mofhylcyainzwbrcmrqg.supabase.co:5432/postgres",
    
    # Pooled connection (port 6543) - RECOMMENDED
    "postgresql://postgres:2407portal2407@aws-0-us-west-1.pooler.supabase.com:6543/postgres",
]

print("\n" + "=" * 100)
print("🔍 TESTING SUPABASE CONNECTIONS")
print("=" * 100)

for i, url in enumerate(urls_to_test, 1):
    connection_type = "Direct (5432)" if ":5432" in url else "Pooled (6543)"
    host = url.split("@")[1].split(":")[0] if "@" in url else "unknown"
    
    print(f"\n{i}. Testing {connection_type}")
    print(f"   Host: {host}")
    print(f"   Connecting...")
    
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 10})
        conn = engine.connect()
        
        # Test query
        result = conn.execute(text("SELECT version()")).fetchone()
        postgres_version = result[0].split(',')[0]
        
        print(f"   ✅ SUCCESS!")
        print(f"   PostgreSQL: {postgres_version}")
        
        conn.close()
        
        print(f"\n✅ Use this URL in your .env file:")
        print(f"   DATABASE_URL={url}")
        
        break  # Stop on first successful connection
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ FAILED: {error_msg[:150]}")

print("\n" + "=" * 100)
print("\n💡 TIP: If both fail, check:")
print("   1. Password is correct")
print("   2. Project is fully provisioned (wait 2-3 minutes)")
print("   3. Check Supabase dashboard for correct connection string")
print("   4. Try the 'Connection pooling' URI from Settings → Database")
print("\n" + "=" * 100 + "\n")





