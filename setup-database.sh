#!/bin/bash

# Trade Oracle - Supabase Database Setup
# Automatically creates database schema in Supabase

set -e

echo "=================================================="
echo "Trade Oracle - Database Setup"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please run ./setup-credentials.sh first"
    exit 1
fi

# Load environment variables
source .env

# Check Supabase credentials
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo -e "${RED}❌ Error: Supabase credentials not configured${NC}"
    echo "Please run ./setup-credentials.sh first"
    exit 1
fi

echo -e "${BLUE}🗄️  Setting up Supabase database...${NC}"
echo ""

# Extract project ID from Supabase URL
PROJECT_ID=$(echo $SUPABASE_URL | sed -E 's/https:\/\/([^.]+).*/\1/')

echo "Project ID: $PROJECT_ID"
echo "Supabase URL: $SUPABASE_URL"
echo ""

# Link to Supabase project
echo -e "${BLUE}📎 Linking to Supabase project...${NC}"
supabase link --project-ref "$PROJECT_ID" --password "$SUPABASE_SERVICE_KEY" || {
    echo -e "${YELLOW}⚠️  Could not link automatically${NC}"
    echo ""
    echo "Please run the schema manually:"
    echo "1. Go to: https://supabase.com/dashboard/project/$PROJECT_ID/sql/new"
    echo "2. Copy contents of: backend/schema.sql"
    echo "3. Paste and click 'Run'"
    exit 0
}

# Run migrations
echo -e "${BLUE}🚀 Running database schema...${NC}"
supabase db push

echo ""
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo ""
echo "Tables created:"
echo "  - option_ticks"
echo "  - trades"
echo "  - reflections"
echo "  - portfolio_snapshots"
echo ""
echo "You can view your tables at:"
echo "https://supabase.com/dashboard/project/$PROJECT_ID/editor"
echo ""
