# Phase 5: Production Deployment Guide

## Overview

This guide walks through deploying the Nuclear Trading Bot to production using free tier services:
- **Backend**: FastAPI on Railway.app
- **Frontend**: React on Vercel
- **Database**: Supabase PostgreSQL
- **Caching**: Upstash Redis (optional)
- **Trading**: Alpaca Markets Paper Trading

**Total Cost**: $0/month for 4 weeks (Railway trial), then ~$5/month

---

## Prerequisites

Before deploying, ensure you have:

1. ✅ Accounts created:
   - Railway.app (free)
   - Vercel (free)
   - Supabase (free)
   - Alpaca Markets (free paper trading)
   - Anthropic API (for Claude reflection)

2. ✅ Environment variables gathered:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`
   - `ANTHROPIC_API_KEY`

3. ✅ Code tested locally:
   ```bash
   # Test backend
   cd backend
   python main.py
   # Should start on http://localhost:8000

   # Test frontend
   cd frontend
   npm install && npm run dev
   # Should start on http://localhost:5173
   ```

4. ✅ GitHub repository set up:
   ```bash
   cd /Users/joshuajames/Projects/nuclear-trading-bot
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

---

## Phase 5A: Deploy Backend to Railway

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "Create new project"
4. Select "Deploy from GitHub repo"
5. Search and select your nuclear-trading-bot repository
6. Railway will auto-detect the Python project

### Step 2: Configure Environment Variables

In Railway dashboard:

1. Go to Variables tab
2. Add all required variables:
   ```
   ENVIRONMENT=production
   PORT=8000
   ALPACA_API_KEY=<your_key>
   ALPACA_SECRET_KEY=<your_secret>
   SUPABASE_URL=<your_url>
   SUPABASE_KEY=<your_anon_key>
   SUPABASE_SERVICE_KEY=<your_service_key>
   ANTHROPIC_API_KEY=<your_key>
   ```

3. Save and Railway will redeploy automatically

### Step 3: Verify Backend Deployment

1. Get the deployed URL from Railway dashboard
2. Test health endpoint:
   ```bash
   curl https://your-railway-url/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "services": {
       "alpaca": "configured",
       "supabase": "configured"
     },
     "paper_trading": true
   }
   ```

3. Visit `/docs` for API documentation:
   ```
   https://your-railway-url/docs
   ```

### Step 4: Setup Cron Job for Weekly Reflection

In Railway dashboard:

1. Go to Services → Select backend
2. Create a cron job:
   - Name: `weekly-reflection`
   - Schedule: `0 22 * * 0` (Sunday 10 PM UTC)
   - Command: `python -m backend.cron.reflection`

This runs Claude analysis every Sunday.

---

## Phase 5B: Deploy Frontend to Vercel

### Step 1: Connect GitHub to Vercel

1. Go to https://vercel.com
2. Click "Import Project"
3. Select "Import Git Repository"
4. Authenticate with GitHub
5. Select your nuclear-trading-bot repository

### Step 2: Configure Build Settings

Vercel auto-detects React/Vite, but verify:

1. **Build Command**: `npm run build`
2. **Output Directory**: `dist`
3. **Install Command**: `npm install`
4. **Framework Preset**: Vite (should auto-detect)

### Step 3: Add Environment Variables

In Vercel project settings → Environment Variables:

```
REACT_APP_API_URL=https://your-railway-url
```

⚠️ Important: This URL must point to your Railway backend from Step 5A.

### Step 4: Deploy

1. Click "Deploy"
2. Vercel builds and deploys to `https://your-project.vercel.app`
3. Check deployment status in Vercel dashboard

---

## Phase 5C: End-to-End Testing

### Test 1: Backend Health

```bash
curl https://your-railway-url/health
```

Expected response: `{"status": "healthy", ...}`

### Test 2: Frontend Loading

1. Visit `https://your-project.vercel.app`
2. Should load dashboard without errors
3. Check browser console for any API errors
4. All cards should show "Disconnected" or "Not configured" initially

### Test 3: API Documentation

1. Visit `https://your-railway-url/docs`
2. Try test endpoints:
   - `GET /health` → should return healthy
   - `GET /api/strategies/info` → should return strategy info
   - `GET /api/execution/trades` → should return empty array initially

### Test 4: Database Connection

Verify Supabase schema is created:

1. Go to Supabase dashboard
2. SQL Editor
3. Run query:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema='public';
   ```
4. Should list: `option_ticks`, `trades`, `reflections`

### Test 5: Manual Paper Trade (Optional)

To verify full integration:

1. Create test trade in Alpaca paper account
2. Monitor dashboard updates
3. Verify trade appears in `/api/execution/trades`
4. Check Supabase `trades` table for entry

---

## Troubleshooting

### Frontend shows "Backend: Disconnected"

**Cause**: CORS issue or wrong API URL

**Solution**:
1. Check `REACT_APP_API_URL` in Vercel environment
2. Verify Railway backend is running: `curl https://your-railway-url/health`
3. Check browser console for detailed error
4. Redeploy frontend after fixing

### Backend returns 500 errors

**Cause**: Missing environment variables or Supabase schema not created

**Solution**:
1. Verify all env vars set in Railway dashboard
2. Copy SQL from `backend/schema.sql` to Supabase SQL Editor
3. Check Railway logs for detailed error
4. Restart deployment

### Weekly reflection cron not running

**Cause**: Cron job misconfigured or API key missing

**Solution**:
1. Verify `ANTHROPIC_API_KEY` is set in Railway
2. Check Railway cron job schedule: `0 22 * * 0` (UTC time)
3. Test manually:
   ```bash
   curl -X POST https://your-railway-url/api/cron/reflect
   ```

---

## Performance Monitoring

### Dashboard

Monitor these metrics:

1. **Backend Health**
   - Response time: < 200ms
   - Uptime: > 99.5%
   - Logs: Check Railway dashboard

2. **Frontend Performance**
   - Load time: < 3s
   - API latency: < 5s
   - Check Vercel Analytics

3. **Trading Metrics**
   - Win rate: 70-80% (from backtest)
   - Daily P&L: Visible on dashboard
   - Trade count: > 1/week (IV mean reversion)

### Alerts

Set up monitoring:

1. Railway: Configure log alerts
2. Vercel: Enable error tracking
3. Supabase: Monitor database usage

---

## Cost Breakdown

| Service | Free Tier | Cost | Duration |
|---------|-----------|------|----------|
| Railway | $5 credit | $0 | 3-4 weeks |
| Vercel | Unlimited | $0 | ∞ |
| Supabase | 500MB DB | $0 | ∞ |
| Upstash | 256MB Redis | $0 | ∞ |
| Alpaca | Paper trading | $0 | ∞ |
| Anthropic | Claude API | Pay per use | ∞ |

**Total Monthly**: $0 for first month, then $5-10/month (Railway only)

---

## Important Notes

### ⚠️ Safety First
- Always paper trade first
- Monitor all trades manually
- Review risk management settings
- Test circuit breakers before live trading

### 📊 Backtesting Results
Before deploying, verify:
- ✅ Backtest Sharpe > 1.2
- ✅ Backtest Win Rate > 55%
- ✅ 200+ trades for statistical significance
- ✅ Realistic costs ($0.65 commission + 1% slippage)

### 🔄 Continuous Deployment

Changes auto-deploy:
1. Push to GitHub `main` branch
2. Railway redeploys backend automatically
3. Vercel redeploys frontend automatically
4. No manual steps needed

### 📝 Logging

All trading data logged to Supabase:
- `option_ticks`: Real-time market data
- `trades`: All executed trades
- `reflections`: Weekly Claude analysis

Access anytime via Supabase dashboard or API.

---

## Success Criteria

Your deployment is successful when:

�� **Backend**
- Health endpoint returns 200
- All services configured
- API docs accessible at `/docs`

✅ **Frontend**
- Dashboard loads without errors
- API connection established
- Charts render without errors
- Real-time updates working (5-second polling)

✅ **Integration**
- Portfolio metrics display correctly
- Recent trades table populated
- System status shows connected
- No console errors

✅ **Database**
- Schema tables created
- Trades logged on execution
- Reflections saved weekly

---

## Next Steps

1. **Monitor**: Watch dashboard daily for first week
2. **Adjust**: Fine-tune parameters based on live results
3. **Document**: Keep notes on trade performance
4. **Analyze**: Review weekly Claude reflections
5. **Scale**: Increase position sizes if confidence builds

---

## Support & Debugging

### Common Issues

**Q: Dashboard shows "Disconnected"**
A: Check `REACT_APP_API_URL` environment variable in Vercel

**Q: API returns 401 Unauthorized**
A: Verify `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in Railway

**Q: Database shows no data**
A: Run SQL schema from `backend/schema.sql` in Supabase

**Q: Claude reflection not running**
A: Check cron schedule and `ANTHROPIC_API_KEY` in Railway

### Logs

Check these for errors:

1. **Railway**: Dashboard → Services → Logs
2. **Vercel**: Dashboard → Deployments → Logs
3. **Supabase**: Dashboard → Logs
4. **Browser**: Developer Tools → Console

---

## Congratulations! 🎉

Your Nuclear Trading Bot is now live and ready to trade!

**Remember**: Always start with paper trading, monitor closely, and gradually increase risk as confidence builds.

For questions or issues, check the [README.md](./README.md) and [SETUP.md](./SETUP.md).
