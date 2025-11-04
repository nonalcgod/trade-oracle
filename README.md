# Nuclear Options Trading Bot

A production-ready options trading system built on 100% free tiers (Nuclear Option strategy).

## Architecture

- **Backend**: FastAPI on Railway ($5 trial credit)
- **Frontend**: React + Vite on Vercel (free tier)
- **Database**: Supabase PostgreSQL (free 500MB)
- **Cache**: Upstash Redis (free 256MB)
- **Market Data**: Alpaca Markets (free paper trading)
- **AI Analysis**: Claude 3.5 Sonnet

## Strategy

**IV Mean Reversion** - Research-proven strategy with 75% win rate in backtests:
- Sell when IV > 70th percentile (overpriced options)
- Buy when IV < 30th percentile (underpriced options)
- Trade options with 30-45 days to expiration
- Hardcoded parameters based on historical research

## Risk Management

- Max 2% portfolio risk per trade
- -3% daily loss circuit breaker
- Stop after 3 consecutive losses
- Kelly position sizing (half-Kelly for safety)
- Limit orders only (no market orders)

## Project Structure

```
nuclear-trading-bot/
├── backend/              # FastAPI trading engine
│   ├── api/             # REST endpoints
│   │   ├── data.py      # Alpaca WebSocket + Greeks
│   │   ├── strategies.py # IV Mean Reversion signals
│   │   ├── risk.py      # Circuit breakers + sizing
│   │   └── execution.py # Alpaca order placement
│   ├── cron/            # Scheduled jobs
│   │   └── reflection.py # Weekly Claude analysis
│   ├── models/          # Pydantic models
│   │   └── trading.py   # OptionTick, Signal, Portfolio
│   ├── utils/           # Utilities
│   │   └── greeks.py    # Black-Scholes calculator
│   └── main.py          # FastAPI app entry
├── frontend/            # React dashboard
│   └── src/
│       ├── App.tsx      # Main dashboard UI
│       └── main.tsx     # React entry point
├── backtest/            # Backtesting framework
│   └── run_backtest.py  # Walk-forward validation
└── .env.example         # Environment template
```

## Setup

### 1. Install Dependencies

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

Frontend:
```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **Alpaca**: Sign up at https://alpaca.markets (use paper trading)
- **Supabase**: Create project at https://supabase.com
- **Upstash**: Create Redis at https://upstash.com
- **Anthropic**: Get Claude API key at https://anthropic.com

### 3. Setup Database

Run the Supabase schema:
```bash
psql $SUPABASE_URL -f backend/schema.sql
```

Or manually execute `backend/schema.sql` in Supabase SQL Editor.

### 4. Run Backtest

Before going live, validate the strategy:
```bash
cd backtest
python run_backtest.py
```

Success criteria:
- ✅ Sharpe ratio > 1.2
- ✅ Win rate > 55%
- ✅ 200+ trades
- ✅ Includes $0.65 commission + 1% slippage

### 5. Start Development

Backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm run dev
```

## Deployment

### Backend (Railway)

1. Connect GitHub repo to Railway
2. Set environment variables in Railway dashboard
3. Railway auto-deploys on push to main

### Frontend (Vercel)

```bash
cd frontend
npm run build
vercel deploy --prod
```

## Important Notes

⚠️ **Paper Trading Only**: This bot uses Alpaca paper trading. Never use real money without extensive testing.

⚠️ **Risk Limits**: Circuit breakers are hardcoded. Do not modify without understanding the implications.

⚠️ **Costs**: Free tiers cover ~3-4 weeks. Monitor usage to avoid charges.

## Success Metrics

Track these metrics on the dashboard:
- **Sharpe Ratio**: Should stay > 1.2
- **Win Rate**: Target 55%+ over 30+ trades
- **Max Drawdown**: Should not exceed -10%
- **Daily P&L**: Circuit breaker triggers at -3%

## License

MIT

