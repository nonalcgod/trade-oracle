#!/bin/bash
# Test script for Railway backend deployment
# Usage: ./test-backend.sh <railway-url>

RAILWAY_URL=${1:-"https://trade-oracle-production.up.railway.app"}

echo "🧪 Testing Railway Backend: $RAILWAY_URL"
echo "================================================"
echo ""

echo "1️⃣ Testing Health Endpoint..."
curl -s "$RAILWAY_URL/health" | jq '.' || echo "❌ Health check failed"
echo ""

echo "2️⃣ Testing Root Endpoint..."
curl -s "$RAILWAY_URL/" | jq '.' || echo "❌ Root endpoint failed"
echo ""

echo "3️⃣ Testing Strategy Info..."
curl -s "$RAILWAY_URL/api/strategies/info" | jq '.' || echo "❌ Strategy info failed"
echo ""

echo "4️⃣ Testing API Documentation..."
echo "Visit: $RAILWAY_URL/docs"
echo ""

echo "✅ Backend testing complete!"
echo ""
echo "Next step: Add this URL to Vercel:"
echo "vercel env add VITE_API_URL production"
echo "Enter value: $RAILWAY_URL"
