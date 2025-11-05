#!/bin/bash

# Trade Oracle - Interactive Credential Setup
# This script helps you set up all credentials interactively

set -e

echo "=================================================="
echo "Trade Oracle - Credential Setup"
echo "=================================================="
echo ""
echo "This script will help you configure all required"
echo "API keys and authenticate CLI tools."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
        exit 0
    fi
fi

echo ""
echo "=================================================="
echo "Step 1: Alpaca Markets (Paper Trading)"
echo "=================================================="
echo ""
echo "1. Go to: https://app.alpaca.markets/paper/dashboard/overview"
echo "2. Click your name → API Keys"
echo "3. Click 'Create New Key' (Paper Trading)"
echo "4. Copy both keys"
echo ""

read -p "Enter ALPACA_API_KEY (starts with PK): " ALPACA_API_KEY
read -p "Enter ALPACA_SECRET_KEY: " ALPACA_SECRET_KEY

echo ""
echo "=================================================="
echo "Step 2: Supabase (Database)"
echo "=================================================="
echo ""
echo "1. Go to: https://supabase.com/dashboard"
echo "2. Create new project (name: trade-oracle)"
echo "3. Wait for project creation (~2 minutes)"
echo "4. Go to: Project Settings → API"
echo "5. Copy the URL and keys"
echo ""

read -p "Enter SUPABASE_URL (https://xxx.supabase.co): " SUPABASE_URL
read -p "Enter SUPABASE_KEY (anon/public key): " SUPABASE_KEY
read -p "Enter SUPABASE_SERVICE_KEY (service_role key): " SUPABASE_SERVICE_KEY

echo ""
echo "=================================================="
echo "Step 3: Anthropic (Claude AI)"
echo "=================================================="
echo ""
echo "1. Go to: https://console.anthropic.com/settings/keys"
echo "2. Click 'Create Key'"
echo "3. Copy the API key"
echo ""

read -p "Enter ANTHROPIC_API_KEY (sk-ant-...): " ANTHROPIC_API_KEY

# Write to .env file
echo ""
echo -e "${BLUE}📝 Writing credentials to .env file...${NC}"

cat > .env << EOF
# Trade Oracle - Production Environment Variables
# Generated: $(date)

# Deployment
ENVIRONMENT=production
PORT=8000

# Alpaca Markets (Paper Trading)
ALPACA_API_KEY=$ALPACA_API_KEY
ALPACA_SECRET_KEY=$ALPACA_SECRET_KEY
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Supabase (Database)
SUPABASE_URL=$SUPABASE_URL
SUPABASE_KEY=$SUPABASE_KEY
SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY

# Anthropic (Claude AI)
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
EOF

echo -e "${GREEN}✅ Credentials saved to .env${NC}"
echo ""

# Authenticate CLI tools
echo "=================================================="
echo "Step 4: Authenticate CLI Tools"
echo "=================================================="
echo ""

# Railway
echo -e "${BLUE}🚂 Authenticating Railway CLI...${NC}"
echo "A browser window will open for Railway login"
read -p "Press Enter to continue..."
railway login
echo -e "${GREEN}✅ Railway authenticated${NC}"
echo ""

# Vercel
echo -e "${BLUE}▲ Authenticating Vercel CLI...${NC}"
echo "A browser window will open for Vercel login"
read -p "Press Enter to continue..."
vercel login
echo -e "${GREEN}✅ Vercel authenticated${NC}"
echo ""

# GitHub
echo -e "${BLUE}🐙 Authenticating GitHub CLI...${NC}"
if gh auth status &>/dev/null; then
    echo -e "${GREEN}✅ GitHub already authenticated${NC}"
else
    gh auth login
    echo -e "${GREEN}✅ GitHub authenticated${NC}"
fi
echo ""

echo "=================================================="
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "All credentials configured and CLIs authenticated!"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Create GitHub repository:"
echo "   gh repo create trade-oracle --private --source=. --push"
echo ""
echo "2. Setup Supabase database:"
echo "   - Go to Supabase SQL Editor"
echo "   - Copy/paste contents of backend/schema.sql"
echo "   - Click 'Run'"
echo ""
echo "3. Run deployment:"
echo "   ./deploy.sh"
echo ""
echo "=================================================="
