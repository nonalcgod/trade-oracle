#!/usr/bin/env python3
"""
Check if database migration has been applied
"""
import os
import sys
from supabase import create_client

# Get credentials from environment
SUPABASE_URL = "https://zwuqmnzqjkybnbicwbhz.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_KEY:
    print("Error: SUPABASE_SERVICE_KEY not found")
    print("Run: railway run python check_migration.py")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try to query a position with legs column
# This will fail if the column doesn't exist
try:
    result = supabase.table('positions').select('id, legs, net_credit, max_loss, spread_width').limit(1).execute()
    print("✅ Migration applied successfully!")
    print(f"   Found {len(result.data)} positions")
    print("   Columns exist: legs, net_credit, max_loss, spread_width")
    sys.exit(0)
except Exception as e:
    error_msg = str(e)
    if 'column' in error_msg.lower() and ('does not exist' in error_msg.lower() or 'not found' in error_msg.lower()):
        print("⚠️  Migration NOT yet applied")
        print("   Please run the SQL in Supabase SQL Editor")
        sys.exit(1)
    else:
        print(f"❌ Error checking migration: {e}")
        sys.exit(1)
