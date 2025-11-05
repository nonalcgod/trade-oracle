#!/bin/bash

# Trade Oracle - Automated Deployment Script
# This script automates the deployment of Trade Oracle to Railway and Vercel

set -e  # Exit on error

echo "=================================================="
echo "Trade Oracle - Automated Deployment"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env file with your credentials first"
    exit 1
fi

# Load environment variables
echo -e "${BLUE}📋 Loading environment variables...${NC}"
source .env

# Verify required variables
REQUIRED_VARS=(
    "ALPACA_API_KEY"
    "ALPACA_SECRET_KEY"
    "SUPABASE_URL"
    "SUPABASE_KEY"
    "SUPABASE_SERVICE_KEY"
    "ANTHROPIC_API_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required environment variables:${NC}"
    printf '%s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "Please fill in all values in .env file"
    exit 1
fi

echo -e "${GREEN}✅ All required environment variables present${NC}"
echo ""

# Function to check CLI authentication
check_auth() {
    echo -e "${BLUE}🔐 Checking CLI authentication...${NC}"

    # Check Railway auth
    if railway whoami &>/dev/null; then
        echo -e "${GREEN}✅ Railway CLI authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️  Railway CLI not authenticated${NC}"
        echo "Please run: railway login"
        exit 1
    fi

    # Check Vercel auth
    if vercel whoami &>/dev/null; then
        echo -e "${GREEN}✅ Vercel CLI authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️  Vercel CLI not authenticated${NC}"
        echo "Please run: vercel login"
        exit 1
    fi

    # Check GitHub auth
    if gh auth status &>/dev/null; then
        echo -e "${GREEN}✅ GitHub CLI authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI not authenticated${NC}"
        echo "Please run: gh auth login"
        exit 1
    fi

    echo ""
}

# Step 1: Check authentication
check_auth

# Step 2: Push to GitHub
echo -e "${BLUE}📤 Step 1/4: Pushing code to GitHub...${NC}"
if git remote | grep -q "origin"; then
    echo "GitHub remote exists, pushing..."
    git add .
    git commit -m "Deploy Trade Oracle to production" || echo "No changes to commit"
    git push origin main
    echo -e "${GREEN}✅ Code pushed to GitHub${NC}"
else
    echo -e "${YELLOW}⚠️  No GitHub remote configured${NC}"
    echo "Please create a GitHub repository and run:"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/trade-oracle.git"
    echo "  git push -u origin main"
    exit 1
fi
echo ""

# Step 3: Deploy Backend to Railway
echo -e "${BLUE}🚂 Step 2/4: Deploying backend to Railway...${NC}"
cd backend

# Initialize Railway project if not already done
if [ ! -f ".railway" ]; then
    echo "Initializing Railway project..."
    railway init
fi

# Set environment variables in Railway
echo "Setting environment variables in Railway..."
railway variables set \
    ENVIRONMENT=production \
    PORT=8000 \
    ALPACA_API_KEY="$ALPACA_API_KEY" \
    ALPACA_SECRET_KEY="$ALPACA_SECRET_KEY" \
    SUPABASE_URL="$SUPABASE_URL" \
    SUPABASE_KEY="$SUPABASE_KEY" \
    SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"

# Deploy to Railway
echo "Deploying to Railway..."
railway up

# Get Railway URL
RAILWAY_URL=$(railway status --json | grep -o '"url":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}✅ Backend deployed to Railway${NC}"
echo -e "   URL: ${BLUE}$RAILWAY_URL${NC}"
echo ""

cd ..

# Step 4: Deploy Frontend to Vercel
echo -e "${BLUE}▲ Step 3/4: Deploying frontend to Vercel...${NC}"
cd frontend

# Deploy to Vercel with environment variable
echo "Deploying to Vercel..."
vercel --prod --yes \
    -e REACT_APP_API_URL="$RAILWAY_URL" \
    -e VITE_API_URL="$RAILWAY_URL"

# Get Vercel URL
VERCEL_URL=$(vercel inspect --json | grep -o '"url":"[^"]*' | head -1 | cut -d'"' -f4)
echo -e "${GREEN}✅ Frontend deployed to Vercel${NC}"
echo -e "   URL: ${BLUE}https://$VERCEL_URL${NC}"
echo ""

cd ..

# Step 5: Test Deployment
echo -e "${BLUE}🧪 Step 4/4: Testing deployment...${NC}"

# Test backend health
echo "Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s "$RAILWAY_URL/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

# Test frontend
echo "Testing frontend..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$VERCEL_URL")
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend returned HTTP $FRONTEND_RESPONSE${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "Your Trade Oracle is now live:"
echo ""
echo -e "${BLUE}Backend API:${NC}    $RAILWAY_URL"
echo -e "${BLUE}API Docs:${NC}       $RAILWAY_URL/docs"
echo -e "${BLUE}Frontend:${NC}       https://$VERCEL_URL"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Visit the frontend dashboard: https://$VERCEL_URL"
echo "2. Verify API connection (should show 'Connected')"
echo "3. Check API docs: $RAILWAY_URL/docs"
echo "4. Monitor Railway logs for any issues"
echo "5. Setup Supabase database schema (if not done)"
echo ""
echo "=================================================="
