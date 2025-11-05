# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trade Oracle is a production-ready options trading system implementing IV (Implied Volatility) Mean Reversion strategy. Built entirely on free-tier services for paper trading.

**Core Strategy**: Sell options when IV > 70th percentile, buy when IV < 30th percentile. Target 30-45 DTE with hardcoded risk management parameters proven by research (75% win rate in backtests).

## Architecture

The system follows a microservices pattern with four core services:

### Backend (FastAPI on Railway)
- **Data Service** (`backend/api/data.py`): Alpaca integration for real-time option quotes + Black-Scholes Greeks calculator
- **Strategy Service** (`backend/api/strategies.py`): IV Mean Reversion signal generation using 90-day IV rank
- **Risk Service** (`backend/api/risk.py`): Circuit breakers (3% daily loss, 3 consecutive losses, 2% max risk per trade)
- **Execution Service** (`backend/api/execution.py`): Order placement via Alpaca with slippage tracking and P&L logging

### Frontend (React + Vite on Vercel)
- Dashboard showing portfolio metrics, P&L charts, trade history, and system status
- Polls backend every 5 seconds for updates (WebSocket not yet implemented)

### Database (Supabase PostgreSQL)
- `option_ticks`: Real-time market data with calculated Greeks
- `trades`: Complete execution history with P&L, commission, slippage
- `reflections`: Weekly Claude AI analysis of performance
- `portfolio_snapshots`: Daily equity curve tracking

### External Services
- **Alpaca Markets**: Paper trading API (never use real money without extensive validation)
- **Upstash Redis**: Optional caching layer (not critical)
- **Anthropic API**: Weekly performance reflection (skeleton implemented)

## Key Commands

### Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py  # Starts on port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Starts on port 5173
```

**Run both services:**
```bash
# Terminal 1
cd backend && python main.py

# Terminal 2
cd frontend && npm run dev
```

### Testing

**Backtest validation (critical before deployment):**
```bash
cd backtest
python run_backtest.py
```

Success criteria: Sharpe > 1.2, Win Rate > 55%, 200+ trades

**API health check:**
```bash
curl http://localhost:8000/health
```

**API documentation:**
Open http://localhost:8000/docs

### Database Setup

Execute schema in Supabase SQL Editor or via psql:
```bash
psql $SUPABASE_URL -f backend/schema.sql
```

## Critical Development Rules

### Risk Management (DO NOT MODIFY)
- Circuit breakers are hardcoded in `backend/api/risk.py` for safety
- Max 2% portfolio risk per trade (Kelly sizing with half-Kelly safety factor)
- -3% daily loss limit (stop all trading)
- Stop after 3 consecutive losses
- These limits prevent catastrophic losses and should never be relaxed without extensive backtesting

### Paper Trading Only
- The system is configured for Alpaca paper trading
- Never use real money without months of validated performance
- `ALPACA_BASE_URL` should always point to `https://paper-api.alpaca.markets`

### Environment Variables
Required keys in `.env`:
- `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`: Paper trading credentials
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`: Database access
- `ANTHROPIC_API_KEY`: Claude reflection (optional)
- `UPSTASH_REDIS_URL`: Caching (optional)

Copy from `.env.example` and fill in your keys.

## Code Architecture Details

### Greeks Calculator (`backend/utils/greeks.py`)
Black-Scholes implementation for delta, gamma, theta, vega, and implied volatility calculation. Uses Newton-Raphson method for IV solving. This is a fallback for when Alpaca doesn't provide Greeks; in production, prefer market-derived Greeks when available.

### Data Models (`backend/models/trading.py`)
All models use Pydantic v2 with `Decimal` for financial precision:
- `OptionTick`: Real-time market data snapshot with Greeks
- `Signal`: Trading signal with entry/exit levels and reasoning
- `RiskApproval`: Circuit breaker validation result
- `Portfolio`: Current account state with positions and P&L

### Signal Generation Flow
1. Data service fetches latest option quotes from Alpaca
2. Calculate Greeks using Black-Scholes (or use Alpaca's if available)
3. Strategy service computes 90-day IV rank from historical ticks in Supabase
4. Generate BUY/SELL signal if IV crosses percentile thresholds (30th/70th)
5. Risk service validates against circuit breakers
6. Execution service places limit order via Alpaca API
7. Log all ticks and trades to Supabase for analysis

### Route Structure
All API routes follow RESTful pattern:
- `GET /api/data/latest/{symbol}`: Latest option data with Greeks
- `POST /api/strategies/signal`: Generate trading signal from tick
- `POST /api/risk/approve`: Validate trade against risk limits
- `POST /api/execution/order`: Execute trade via Alpaca
- `GET /api/execution/portfolio`: Current portfolio state
- `GET /api/execution/trades`: Trade history with P&L

Each service has a `/health` endpoint for monitoring.

### CORS Configuration
Frontend allowed origins in `backend/main.py`:
- `http://localhost:3000` (Create React App)
- `http://localhost:5173` (Vite default)
- `https://*.vercel.app` (Production deployments)

Add additional origins as needed for staging environments.

## Deployment

### Backend to Railway
1. Connect GitHub repo to Railway
2. Set all environment variables in Railway dashboard
3. Railway auto-deploys on push to `main`
4. Configure cron job: `0 22 * * 0` (Sunday 10 PM UTC) → `python -m backend.cron.reflection`

### Frontend to Vercel
1. Connect GitHub repo to Vercel
2. Set `REACT_APP_API_URL=https://your-railway-url`
3. Build: `npm run build`, Output: `dist`, Framework: Vite
4. Vercel auto-deploys on push to `main`

### Cost
- Railway: $5 trial credit (~4 weeks), then $5-10/month
- Vercel: Free forever
- Supabase: Free tier (500MB DB, 2GB bandwidth/month)
- Alpaca: Free paper trading

## Common Issues

### "Backend: Disconnected" on frontend
- Verify `REACT_APP_API_URL` in Vercel environment variables
- Check CORS origins in `backend/main.py`
- Test backend health: `curl https://your-railway-url/health`

### API returns 500 errors
- Missing environment variables in Railway
- Database schema not executed in Supabase
- Check Railway logs for detailed error messages

### Backtest fails
- Run from `backtest/` directory: `cd backtest && python run_backtest.py`
- Ensure pandas, numpy, scipy installed
- Synthetic data generation can take 10-15 seconds

### Greeks calculator returns None
- Check option price > 0 and strike > 0
- Expiration must be in the future
- Underlying price must be positive
- IV solver may fail for deeply ITM/OTM options (this is expected)

## Project Status

**Completed (Phases 1-3):**
- ✅ Complete backend with all 4 microservices
- ✅ React dashboard with basic UI
- ✅ Backtesting framework with realistic costs
- ✅ Database schema and queries
- ✅ Deployment configurations for Railway and Vercel

**Not Yet Implemented (Phases 4-5):**
- ⚠️ WebSocket streaming (currently using REST polling)
- ⚠️ Enhanced dashboard charts (Recharts installed but basic implementation)
- ⚠️ Full Claude weekly reflection (skeleton exists in `backend/cron/reflection.py`)
- ⚠️ Real-time portfolio updates (dashboard polls every 5 seconds)

## Important Notes

- This bot is for paper trading only. Real money requires extensive validation.
- IV Mean Reversion works best in high IV environments (VIX > 20).
- The 75% win rate from backtests assumes synthetic data; real performance varies.
- Always run backtests before deploying new parameters or strategies.
- Monitor free tier limits: Supabase (500MB), Railway ($5/month after trial).
- Commission is $0.65 per contract, slippage assumed at 1% in backtests.
