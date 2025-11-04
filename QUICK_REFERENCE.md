# Quick Reference Guide

## Local Development

### Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
Visit: http://localhost:8000/docs

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit: http://localhost:5173 (or 3000)

### Run Backtest
```bash
cd backtest
python run_backtest.py
```

### Run Weekly Reflection
```bash
cd backend
python -m cron.reflection
```

---

## API Endpoints

### Health & Status
- `GET /` → Root info
- `GET /health` → Service health
- `GET /docs` → API documentation

### Data Service
- `GET /api/data/option/{symbol}` → Get option Greeks

### Strategies
- `GET /api/strategies/info` → Strategy parameters
- `GET /api/strategies/signal/{symbol}` → Generate trading signal

### Risk Management
- `GET /api/risk/portfolio` → Current portfolio state
- `POST /api/risk/approve` → Risk approval for trade

### Execution
- `GET /api/execution/portfolio` → Portfolio snapshot
- `GET /api/execution/trades` → Recent trades (limit param)
- `GET /api/execution/performance` → Performance metrics
- `POST /api/execution/order` → Place order

---

## Environment Variables

### Backend (Railway)
```
ENVIRONMENT=production
PORT=8000
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
ANTHROPIC_API_KEY=your_key
```

### Frontend (Vercel)
```
REACT_APP_API_URL=https://your-railway-backend.railway.app
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app entry |
| `backend/api/strategies.py` | IV Mean Reversion strategy |
| `backend/api/risk.py` | Risk management & circuit breakers |
| `backend/api/execution.py` | Trade execution & logging |
| `backend/cron/reflection.py` | Weekly Claude analysis |
| `frontend/src/App.tsx` | Main React dashboard |
| `frontend/src/api.ts` | API client service |
| `backtest/run_backtest.py` | Backtesting framework |
| `backend/schema.sql` | Database schema (run in Supabase) |

---

## Strategy Parameters

**IV Mean Reversion**
- Buy when IV < 30th percentile (underpriced)
- Sell when IV > 70th percentile (overpriced)
- Trade 30-45 days to expiration (DTE)
- Historical lookback: 90 days

**Risk Limits** (Hardcoded)
- Max 2% risk per trade
- Max 5% position size
- -3% daily loss circuit breaker
- 3 consecutive losses = pause trading

**Expected Performance**
- Win Rate: 70-80%
- Sharpe Ratio: 1.2-1.8
- Monthly Return: 5-15%
- Max Drawdown: 8-12%

---

## Database Schema

### option_ticks
Real-time option prices & Greeks
```sql
id, timestamp, symbol, underlying_price, strike,
bid, ask, delta, gamma, theta, vega, iv
```

### trades
Executed trades
```sql
id, timestamp, symbol, strategy, signal_type,
entry_price, exit_price, quantity, pnl, commission, slippage
```

### reflections
Weekly Claude analysis
```sql
id, week_ending, analysis (JSONB), metrics (JSONB)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check Python 3.8+, install requirements.txt |
| Frontend API errors | Check REACT_APP_API_URL, ensure backend running |
| Alpaca connection fails | Verify API keys, check paper trading enabled |
| Database errors | Run schema.sql in Supabase, verify credentials |
| Weekly reflection fails | Check ANTHROPIC_API_KEY, verify Supabase |

---

## Useful Commands

```bash
# Test API endpoint
curl http://localhost:8000/health

# Check git status
git status

# Push to GitHub
git push origin main

# View logs (Railway)
railway logs

# Restart service (Railway)
railway deploy

# Tail logs (Vercel)
vercel logs
```

---

## Cost Summary

| Service | Monthly | Status |
|---------|---------|--------|
| Railway | $0-5 | Trial then $5/mo |
| Vercel | Free | ∞ |
| Supabase | Free | ∞ (500MB) |
| Alpaca | Free | ∞ |
| Anthropic | ~$0.50 | Per API call |
| **Total** | **~$5-6** | Sustainable |

---

## Success Metrics

Track these metrics:

```
Dashboard shows:
  ✓ Portfolio balance
  ✓ Daily P&L
  ✓ Win rate
  ✓ Active positions
  ✓ Portfolio Greeks (delta, theta)

Charts show:
  ✓ Cumulative P&L trend
  ✓ Daily wins vs losses
  ✓ Daily P&L bars

Recent Trades show:
  ✓ Trade history with details
  ✓ Entry/exit prices
  ✓ P&L per trade
  ✓ Timestamp
```

---

## Next Steps

1. ✅ **Backtest** → Run locally, verify Sharpe >1.2
2. ✅ **Test Locally** → Start backend & frontend, check health
3. 🚀 **Deploy Backend** → Push to Railway
4. 🚀 **Deploy Frontend** → Push to Vercel
5. 🧪 **E2E Test** → Check dashboard updates
6. 📊 **Monitor** → Watch daily for first week
7. 🔄 **Iterate** → Adjust parameters based on results

---

## Support Resources

- API Docs: http://localhost:8000/docs (local) or deployed URL
- Backtest Results: Terminal output from `run_backtest.py`
- Database: Supabase dashboard
- Logs: Railway dashboard for backend, Vercel for frontend
- Claude Reflections: Check `reflections` table in Supabase

---

**Ready to trade? Good luck! 🚀**
