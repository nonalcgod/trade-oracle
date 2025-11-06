#!/usr/bin/env python3
"""
Apply database migration 002_multi_leg_positions.sql to Supabase
"""
import os
from supabase import create_client

# Get Supabase credentials from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables not set")
    print("Run: railway run python backend/apply_migration.py")
    exit(1)

# Read migration SQL
migration_file = "backend/migrations/002_multi_leg_positions.sql"
with open(migration_file, "r") as f:
    migration_sql = f.read()

print(f"📄 Reading migration from {migration_file}")
print(f"🔗 Connecting to Supabase: {SUPABASE_URL}")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Execute migration using RPC call to raw SQL
print("⚙️  Applying migration...")

try:
    # Supabase Python client doesn't support raw SQL directly
    # We need to use the PostgREST API with the service key
    import requests

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Use the Supabase SQL endpoint (requires service key)
    # Note: This requires a direct PostgreSQL connection or Supabase SQL endpoint
    print("⚠️  Migration requires direct PostgreSQL connection")
    print("📋 Copy the migration SQL and run it in Supabase SQL Editor:")
    print("   https://app.supabase.com/project/zwuqmnzqjkybnbicwbhz/sql/new")
    print("\n" + "="*80)
    print(migration_sql)
    print("="*80)

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
