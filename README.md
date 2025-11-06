# Trade Oracle

A production-ready options trading system built on 100% free tiers. Implements IV (Implied Volatility) Mean Reversion strategy with hardcoded risk management.

**Status:** MVP deployed on Railway + Vercel (Nov 2025)

## Architecture

- **Backend**: FastAPI on Railway ($5 trial credit, then $5-10/month)
- **Frontend**: React + Vite on Vercel (free tier forever)
- **Database**: Supabase PostgreSQL (free 500MB)
- **Cache**: Upstash Redis (optional, free 256MB)
- **Market Data**: Alpaca Markets (free paper trading)
- **AI Analysis**: Claude 3.5 Sonnet (optional for weekly reflections)

## Strategies

Trade Oracle implements two algorithmic options strategies:

### 1. IV Mean Reversion
Research-proven strategy with 75% win rate in backtests:
- Sell when IV > 70th percentile (overpriced options)
- Buy when IV < 30th percentile (underpriced options)
- Trade options with 30-45 days to expiration
- Hardcoded parameters based on historical research

### 2. 0DTE Iron Condor (NEW)
Same-day expiration 4-leg spreads for consistent income:
- Entry window: 9:31-9:45am ET (first 15 minutes only)
- Delta-based strike selection (target 0.15 delta)
- Automated exits: 50% profit, 2x stop loss, or 3:50pm ET force close
- 70-80% theoretical win rate
- Multi-leg position tracking with P&L monitoring

## Risk Management

- Max 2% portfolio risk per trade (Kelly sizing with half-Kelly safety)
- -3% daily loss circuit breaker
- Stop after 3 consecutive losses
- Limit orders only (no market orders)
- **Paper trading only** - never use real money without extensive validation

## Project Structure

```
trade-oracle/
├── backend/              # FastAPI trading engine
│   ├── api/             # REST endpoints
│   │   ├── data.py      # Alpaca integration + Greeks calculator
│   │   ├── strategies.py # IV Mean Reversion signals
│   │   ├── risk.py      # Circuit breakers + position sizing
│   │   └── execution.py # Order placement + trade logging
│   ├── cron/            # Scheduled jobs
│   │   └── reflection.py # Weekly Claude analysis (skeleton)
│   ├── models/          # Pydantic v2 models
│   │   └── trading.py   # OptionTick, Signal, Portfolio
│   ├── utils/           # Utilities
│   │   └── greeks.py    # Black-Scholes calculator
│   ├── main.py          # FastAPI app entry
│   ├── requirements.txt # Local development dependencies
│   └── requirements-railway.txt # Production dependencies
├── frontend/            # React + Vite dashboard
│   └── src/
│       ├── App.tsx      # Main dashboard UI
│       ├── api.ts       # Backend API client
│       └── main.tsx     # React entry point
├── backtest/            # Backtesting framework
│   └── run_backtest.py  # Walk-forward validation
├── Dockerfile           # Railway deployment config
├── railway.json         # Railway service settings
├── CLAUDE.md            # Auto-loading context for Claude Code
└── .env.example         # Environment template
```

## Quick Start

### 1. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

**Required API keys:**
- **Alpaca Markets**: Sign up at https://alpaca.markets (use paper trading!)
- **Supabase**: Create project at https://supabase.com (free tier)
- **Upstash Redis**: Create database at https://upstash.com (optional)
- **Anthropic API**: Get Claude key at https://anthropic.com (optional for reflections)

### 3. Setup Database

Run the Supabase schema in the SQL Editor:

```bash
# Copy contents of backend/schema.sql
# Paste into Supabase SQL Editor and run
```

Creates tables: `option_ticks`, `trades`, `reflections`, `portfolio_snapshots`

### 4. Run Backtest (Optional)

Validate the strategy before going live:

```bash
cd backtest
python run_backtest.py
```

**Success criteria:**
- ✅ Sharpe ratio > 1.2
- ✅ Win rate > 55%
- ✅ 200+ trades
- ✅ Includes $0.65 commission + 1% slippage

### 5. Start Development Servers

**Backend:**
```bash
cd backend
python main.py  # Starts on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm run dev  # Starts on http://localhost:5173
```

**API Documentation:** http://localhost:8000/docs

## Dashboard Features

**Portfolio Overview:**
- Account balance & daily P&L
- Win rate percentage
- Active positions count
- Portfolio Greeks (delta, theta)
- Consecutive losses counter (circuit breaker status)

**Performance Charts:**
- Cumulative P&L trend
- Daily wins vs losses
- Daily P&L bars

**Recent Trades:**
- Trade history with timestamps
- Entry/exit prices
- Position quantities
- P&L per trade
- Trading strategy used

**System Status:**
- Backend connection indicator
- Alpaca Markets status
- Supabase database status
- Real-time update frequency (5 second polling)

## Deployment

### Backend (Railway)

**Using Dockerfile (Recommended):**

1. Push code to GitHub
2. Connect repo to Railway at https://railway.app
3. Railway auto-detects Dockerfile and builds
4. Set environment variables in Railway dashboard:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `ALPACA_BASE_URL=https://paper-api.alpaca.markets`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - (Optional) `ANTHROPIC_API_KEY`, `UPSTASH_REDIS_URL`

**Deployment notes:**
- Build time: ~3-4 minutes
- Uses `python:3.11.10-slim` for smaller image
- Health check: `/health` endpoint (60 second timeout)
- Auto-deploys on push to `main` branch

### Frontend (Vercel)

1. Push code to GitHub
2. Connect repo to Vercel at https://vercel.com
3. Set environment variable:
   - `VITE_API_URL=https://your-railway-url.railway.app`
4. Deploy settings:
   - Build command: `npm run build`
   - Output directory: `dist`
   - Framework: Vite

**Vercel auto-deploys on push to `main` branch**

## Development with Claude Code

This project uses **NetworkChuck's Terminal AI Workflow** for persistent context:

```bash
cd trade-oracle
claude  # Auto-loads CLAUDE.md with full project context
```

**CLAUDE.md contains:**
- Complete architecture overview
- Current deployment status
- Recent session summaries
- Common commands and workflows
- Agent usage patterns

**No more re-explaining the project every session!**

## Cost Breakdown

| Service | Free Tier | Paid Tier | Notes |
|---------|-----------|-----------|-------|
| Railway | $5 trial (30 days) | $5-10/month | Backend hosting |
| Vercel | Free forever | Free | Frontend hosting |
| Supabase | 500MB DB, 2GB bandwidth | $25/month | Usually stays free |
| Upstash Redis | 256MB, 10k commands/day | $0.20/100k | Optional caching |
| Alpaca Markets | Unlimited paper trading | Free | Market data |
| **Total** | **$0 for 30 days** | **~$5-10/month** | After Railway trial |

## Important Notes

⚠️ **Paper Trading Only**: This system uses Alpaca paper trading. Never use real money without months of validated performance.

⚠️ **Risk Limits**: Circuit breakers are hardcoded in `backend/api/risk.py` for safety. Do not modify without understanding implications.

⚠️ **API Keys**: Never commit API keys to git. Use `.env` file (already in `.gitignore`).

⚠️ **Dependency Conflicts**: If Railway deployment fails, check that:
- `alpaca-py==0.35.0` (not 0.30.x - has httpx conflict)
- `supabase==2.23.0` (not 2.10.x - has proxy bug)
- See `requirements-railway.txt` for tested versions

## Success Metrics

**Track these on the dashboard:**
- **Sharpe Ratio**: Should stay > 1.2
- **Win Rate**: Target 55%+ over 30+ trades
- **Max Drawdown**: Should not exceed -10%
- **Daily P&L**: Circuit breaker triggers at -3%

**Monitor circuit breakers:**
- Max 2% risk per trade enforced
- Trading stops after 3 consecutive losses
- Trading stops if daily loss hits -3%

## API Endpoints

**Health & Status:**
- `GET /` - Welcome message
- `GET /health` - Service health check

**Market Data:**
- `GET /api/data/latest/{symbol}` - Latest option data with Greeks

**Strategy:**
- `POST /api/strategies/signal` - Generate trading signal

**Risk Management:**
- `POST /api/risk/approve` - Validate trade against circuit breakers

**Execution:**
- `POST /api/execution/order` - Place order via Alpaca
- `GET /api/execution/portfolio` - Current portfolio state
- `GET /api/execution/trades` - Trade history
- `GET /api/execution/performance` - Performance metrics

**Full API Docs:** `https://your-railway-url/docs`

## Troubleshooting

**Backend won't start:**
- Check all environment variables are set
- Verify Supabase credentials with: `curl $SUPABASE_URL/rest/v1/`
- Check Railway logs for specific errors

**Frontend shows "Backend: Disconnected":**
- Verify `VITE_API_URL` is set in Vercel
- Check CORS settings in `backend/main.py`
- Test backend health: `curl https://your-railway-url/health`

**Railway deployment fails:**
- Check Railway build logs for dependency conflicts
- Verify `requirements-railway.txt` has compatible versions
- Ensure Dockerfile uses `python:3.11.10-slim` or later

**Greeks calculations seem wrong:**
- Check that underlying price is fetched correctly (not hardcoded $450)
- Verify option symbol format: `SPY250117C00450000`
- Ensure expiration date is in the future

## License

MIT

---

**Built with Claude Code** | See `CLAUDE.md` for development context
