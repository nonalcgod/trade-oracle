# Nuclear Trading Bot - Setup Guide

## Quick Start (Phases 1-3 Complete!)

You now have a fully functional options trading bot with:
- ✅ Complete project structure
- ✅ All backend services (data, strategies, risk, execution)
- ✅ Backtesting framework with realistic costs
- ✅ React frontend dashboard (basic)

## Next Steps

### 1. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required keys:
- **ALPACA_API_KEY** & **ALPACA_SECRET_KEY**: Get from https://alpaca.markets (paper trading)
- **SUPABASE_URL** & **SUPABASE_KEY**: Get from https://supabase.com
- **UPSTASH_REDIS_URL**: Get from https://upstash.com (optional for caching)
- **ANTHROPIC_API_KEY**: For weekly reflections (Phase 4 feature)

### 3. Setup Database

Run the Supabase schema in your Supabase SQL Editor:

```bash
# Option 1: Copy/paste backend/schema.sql into Supabase SQL Editor
# Option 2: Use psql (if you have it)
psql $SUPABASE_URL -f backend/schema.sql
```

### 4. Run Backtest (Validate Strategy)

Before going live, validate the strategy:

```bash
cd backtest
python run_backtest.py
```

**Success Criteria:**
- ✅ Sharpe Ratio > 1.2
- ✅ Win Rate > 55%
- ✅ 200+ trades

Note: The backtest uses synthetic data for demonstration. In production, you'd fetch real historical data from Alpaca.

### 5. Start the Backend

```bash
cd backend
python main.py
```

The API will be available at http://localhost:8000

**Test the API:**
```bash
curl http://localhost:8000/health
```

**View API Docs:**
Open http://localhost:8000/docs in your browser

### 6. Start the Frontend

```bash
cd frontend
npm run dev
```

The dashboard will be available at http://localhost:3000

## Project Status

### ✅ Completed (Phases 1-3)

**Phase 1: Foundation**
- Project structure
- Pydantic models (OptionTick, Signal, Portfolio, etc.)
- Database schema (Supabase)
- Dependencies configured

**Phase 2: Core Services**
- Greeks calculator (Black-Scholes)
- Data service (Alpaca integration)
- Strategy service (IV Mean Reversion)
- Risk management (circuit breakers, Kelly sizing)
- Execution service (order placement, P&L tracking)
- FastAPI application with all routes

**Phase 3: Backtesting**
- Walk-forward backtest framework
- Realistic cost model ($0.65 commission + 1% slippage)
- Historical data fetching (synthetic for demo)
- Performance validation

### 🚧 Not Yet Implemented (Phases 4-5)

**Phase 4: Enhancement**
- Weekly Claude reflection (skeleton created)
- Enhanced React dashboard with charts
- Real-time portfolio updates

**Phase 5: Deployment**
- Railway backend deployment
- Vercel frontend deployment
- Environment variable configuration
- Production testing

## API Endpoints

### Data Service (`/api/data`)
- `GET /api/data/latest/{symbol}` - Get latest option data with Greeks
- `POST /api/data/stream` - Start streaming (not yet implemented)
- `GET /api/data/health` - Health check

### Strategy Service (`/api/strategies`)
- `POST /api/strategies/signal` - Generate trading signal
- `GET /api/strategies/info` - Strategy information
- `GET /api/strategies/health` - Health check

### Risk Management (`/api/risk`)
- `POST /api/risk/approve` - Approve/reject trade
- `GET /api/risk/limits` - Get risk limits
- `GET /api/risk/health` - Health check

### Execution Service (`/api/execution`)
- `POST /api/execution/order` - Execute trade
- `GET /api/execution/portfolio` - Get portfolio state
- `GET /api/execution/health` - Health check

## Testing the System

### 1. Test Greeks Calculator

```bash
cd backend
python -c "
from utils.greeks import calculate_all_greeks
from decimal import Decimal
from datetime import datetime, timedelta

greeks = calculate_all_greeks(
    underlying_price=Decimal('450.00'),
    strike=Decimal('455.00'),
    expiration=datetime.now() + timedelta(days=35),
    option_price=Decimal('5.50'),
    is_call=True
)

print(f'Delta: {greeks[\"delta\"]}')
print(f'Gamma: {greeks[\"gamma\"]}')
print(f'Theta: {greeks[\"theta\"]}')
print(f'Vega: {greeks[\"vega\"]}')
print(f'IV: {greeks[\"iv\"]}')
"
```

### 2. Test Strategy Signal Generation

```bash
# Start the backend first
cd backend
python main.py

# In another terminal, test the signal endpoint
curl -X POST http://localhost:8000/api/strategies/signal \
  -H "Content-Type: application/json" \
  -d '{
    "tick": {
      "symbol": "SPY250117C00450000",
      "underlying_price": 450.00,
      "strike": 450.00,
      "expiration": "2025-01-17T16:00:00Z",
      "bid": 5.20,
      "ask": 5.40,
      "delta": 0.5,
      "gamma": 0.01,
      "theta": -0.05,
      "vega": 0.1,
      "iv": 0.35,
      "timestamp": "2024-11-04T12:00:00Z"
    }
  }'
```

### 3. Run Backtest

```bash
cd backtest
python run_backtest.py
```

## Important Notes

⚠️ **Paper Trading Only**: This bot is configured for paper trading only. Never use real money without extensive testing.

⚠️ **Risk Limits**: Circuit breakers are hardcoded for safety:
- Max 2% risk per trade
- -3% daily loss limit
- Stop after 3 consecutive losses

⚠️ **Free Tier Limits**:
- Supabase: 500MB database, 2GB bandwidth/month
- Upstash: 256MB Redis, 10k commands/day
- Railway: $5 trial credit (~3-4 weeks)
- Alpaca: Paper trading unlimited

## Architecture Overview

```
┌─────────────┐
│   Frontend  │  React Dashboard (Vercel)
│   (React)   │  - Portfolio view
└──────┬──────┘  - Trade history
       │         - System status
       │ HTTP
┌──────▼──────┐
│   Backend   │  FastAPI (Railway)
│  (FastAPI)  │  - Data service (Alpaca + Greeks)
└──────┬──────┘  - Strategy (IV Mean Reversion)
       │         - Risk (Circuit breakers)
       │         - Execution (Order placement)
       │
   ┌───┴───┬───────────┬──────────┐
   │       │           │          │
┌──▼───┐ ┌─▼─────┐ ┌──▼──────┐ ┌─▼────────┐
│Alpaca│ │Supabase│ │Upstash  │ │Claude API│
│Markets│ │ (DB)  │ │(Cache)  │ │ (Reflect)│
└──────┘ └────────┘ └─────────┘ └──────────┘
```

## Troubleshooting

### Backend won't start
- Check that all environment variables are set in `.env`
- Verify Python version >= 3.11
- Make sure virtual environment is activated

### Frontend won't start
- Run `npm install` first
- Check Node.js version >= 18

### Backtest fails
- Check that pandas and numpy are installed
- Verify backend path is accessible
- Run from `backtest/` directory

### API returns errors
- Check that services are configured (health endpoints)
- Verify API keys are valid
- Check logs for detailed error messages

## Next Steps After Setup

1. **Run Backtest**: Validate strategy performance
2. **Test API**: Use `/docs` to test all endpoints
3. **Deploy Backend**: Push to Railway
4. **Deploy Frontend**: Push to Vercel
5. **Monitor Performance**: Check dashboard and logs
6. **Paper Trade**: Test with real market data
7. **Implement Phase 4**: Weekly reflections, enhanced UI

## Support

For issues or questions:
1. Check the `/docs` endpoint for API documentation
2. Review logs in `backend/` directory
3. Test individual components (Greeks, strategy, risk)
4. Verify environment variables are set correctly

---

**Remember**: This is a paper trading bot. Never risk real money without extensive testing and validation!

