#!/bin/bash
# Apply positions table schema directly via psql
# Usage: ./apply_schema_psql.sh

set -e

# Load environment variables
source ../.env 2>/dev/null || source .env 2>/dev/null || true

# Extract DB credentials from SUPABASE_URL
# Format: https://zwuqmnzqjkybnbicwbhz.supabase.co
PROJECT_REF=$(echo $SUPABASE_URL | sed 's/https:\/\///' | sed 's/.supabase.co//')

# Supabase connection string format
# postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres

echo "========================================"
echo "Applying Positions Table Schema"
echo "========================================"
echo ""
echo "IMPORTANT: This script requires direct PostgreSQL access."
echo "Option 1: Use Supabase SQL Editor (recommended)"
echo "  1. Go to: https://supabase.com/dashboard/project/$PROJECT_REF/editor/sql"
echo "  2. Copy schema from backend/schema.sql (lines for positions table)"
echo "  3. Click 'Run'"
echo ""
echo "Option 2: Use psql with connection pooler"
echo "  Get connection string from: https://supabase.com/dashboard/project/$PROJECT_REF/settings/database"
echo "  Then run: psql 'YOUR_CONNECTION_STRING' -f ../schema.sql"
echo ""
echo "Option 3: Run the Python script (shows SQL to copy)"
echo "  python3 apply_positions_schema.py"
echo ""
