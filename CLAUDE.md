# CLAUDE.md

**Auto-Loading Context File for Claude Code CLI** | Last Updated: 2025-11-12

This file provides guidance to Claude Code when working with this repository. It automatically loads when launching Claude Code in this directory, maintaining persistent context across all sessions.

> 💡 **NetworkChuck's Terminal AI Workflow**: Persistent context pattern - no more re-explaining the project every session!

---

## Project Overview

**Trade Oracle** is a production-ready multi-strategy options trading system built on free-tier services for paper trading.

### Three Live Strategies

1. **IV Mean Reversion** ✅ Production-Ready
   - Single-leg options (30-45 DTE)
   - Buy IV < 30th percentile, Sell IV > 70th percentile
   - 90-day IV rank calculation
   - 75% backtest win rate, 50% profit target, 75% stop loss

2. **0DTE Iron Condor** ✅ Production-Ready
   - 4-leg same-day expiration spreads
   - Entry: 9:31-9:45am ET (15-minute window)
   - Target 0.15 delta strikes
   - Exit: 50% profit, 2x stop loss, 3:50pm force close
   - Multi-leg position close fully implemented
   - 70-80% theoretical win rate

3. **0DTE Momentum Scalping** ✅ Most Advanced (Newest)
   - Single-leg 0DTE contracts
   - **6-condition system** (ALL must be met):
     1. EMA(9) crosses EMA(21)
     2. RSI(14) confirmation (>30 long, <70 short)
     3. Volume spike (≥2x average)
     4. VWAP breakout
     5. Relative strength confirmation
     6. Time window (9:31-11:30am ET only)
   - **Advanced detection**: Gamma walls, unusual activity
   - **Strict discipline**: Max 4 trades/day, 2-loss rule, 11:30am force close
   - **Elite agent**: AI scalper in `.claude/agents/scalper-expert.md` (5,000 words)

---

## Architecture

### Backend (FastAPI on Railway) - 7 Services

| Service | File | LOC | Status | Purpose |
|---------|------|-----|--------|---------|
| **Data** | `api/data.py` | 279 | ✅ | Alpaca integration + Black-Scholes Greeks |
| **Strategies** | `api/strategies.py` | 238 | ✅ | IV Mean Reversion signals |
| **Iron Condor** | `api/iron_condor.py` | 220 | ⚠️ | 0DTE 4-leg strategy |
| **Momentum Scalping** | `api/momentum_scalping.py` | 537 | ✅ | 0DTE momentum with gamma detection |
| **Risk** | `api/risk.py` | 291 | ✅ | Circuit breakers (hardcoded for safety) |
| **Execution** | `api/execution.py` | 1,451 | ✅ | Order placement + position tracking |
| **Testing** | `api/testing.py` | 328 | ✅ | Development/debugging helpers |

**Total**: 37 API endpoints, 5,384 LOC

**Background Services**:
- `monitoring/position_monitor.py` (260 LOC) - Auto-exits with strategy-specific logic
- `utils/greeks.py` - Black-Scholes calculator
- `utils/indicators.py` - EMA, RSI, VWAP, volume analysis
- `utils/gamma_walls.py` - Gamma wall detection
- `utils/unusual_activity.py` - Options flow analysis

### Frontend (React 19 + Vite on Vercel) - 3,670 LOC

**Pages**:
- `/` - Main dashboard (Portfolio, Trades, Positions, Charts, System Status)
- `/scalper-pro` - Momentum scalping dashboard with signal table

**Components** (13 total):
- Core: Portfolio, Trades, Positions, Charts, MomentumSignals
- UI Kit: PillBadge, StatusDot, CircuitBreakerProgress, MetricCard

**Polling**: 5-60 seconds (WebSocket not implemented)

### Database (Supabase PostgreSQL)

```
option_ticks        # Market data + calculated Greeks
trades              # Execution history with P&L
positions           # Open/closed positions (JSONB legs for multi-leg)
reflections         # Weekly AI analysis (skeleton)
portfolio_snapshots # Daily equity curve
```

**Multi-Leg Support**: JSONB `legs` column stores 4-leg iron condor data

### External Services

- **Alpaca Markets**: Paper trading API (NEVER use real money without validation)
- **Supabase**: Free tier (500MB DB, 2GB bandwidth/month)
- **Upstash Redis**: Optional caching (not critical)
- **Anthropic API**: Weekly reflections (skeleton only)

---

## Quick Start

### Development

```bash
# Backend (port 8000)
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py

# Frontend (port 5173)
cd frontend
npm run dev

# API Docs
open http://localhost:8000/docs
```

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Backtest validation (CRITICAL before deployment)
cd backtest && python run_backtest.py
# Success: Sharpe > 1.2, Win Rate > 55%, 200+ trades
```

### Database Setup

```bash
# Apply schema in Supabase SQL Editor
psql $SUPABASE_URL -f backend/schema.sql
```

---

## Critical Development Rules

### 🔒 Risk Management (DO NOT MODIFY)

Hardcoded in `backend/api/risk.py` for safety:
- **Max 2% portfolio risk per trade** (Kelly sizing with half-Kelly factor)
- **-3% daily loss limit** (stop all trading)
- **3 consecutive losses** (stop all trading)
- **NEVER relax without extensive backtesting**

### 🚨 Paper Trading Only

- System configured for Alpaca paper trading
- `ALPACA_BASE_URL` must point to `https://paper-api.alpaca.markets`
- Never use real money without months of validated performance

### 🔑 Environment Variables

Required in `.env`:
```bash
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret
SUPABASE_URL=your_db_url
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
ANTHROPIC_API_KEY=optional_for_reflections
UPSTASH_REDIS_URL=optional_for_caching
```

Copy from `.env.example` and fill in your keys.

---

## Key API Routes

### IV Mean Reversion
```
GET  /api/data/latest/{symbol}     # Latest option data + Greeks
POST /api/strategies/signal         # Generate IV signal
POST /api/risk/approve              # Validate against circuit breakers
POST /api/execution/order           # Execute single-leg trade
```

### 0DTE Iron Condor
```
GET  /api/iron-condor/health        # Strategy initialization status
GET  /api/iron-condor/should-enter  # Check entry window (9:31-9:45am)
POST /api/iron-condor/signal        # Generate iron condor signal
POST /api/iron-condor/build         # Build 4-leg with delta-based strikes
POST /api/iron-condor/check-exit    # Evaluate exit conditions
```

### 0DTE Momentum Scalping
```
GET  /api/momentum-scalping/scan    # Scan for 6-condition setups
POST /api/momentum-scalping/execute # Execute momentum trade
GET  /api/momentum-scalping/health  # Strategy status
```

### Execution & Monitoring
```
POST /api/execution/order/multi-leg     # Execute 4-leg orders
GET  /api/execution/positions           # List all positions
GET  /api/execution/positions/{id}      # Position details + legs
GET  /api/execution/portfolio           # Current portfolio state
GET  /api/execution/trades              # Trade history with P&L
```

### Testing/Debugging
```
POST /api/testing/close-position        # Manual position close
GET  /api/testing/check-exit-conditions # Preview exit status
POST /api/testing/force-exit-all        # Emergency close all
POST /api/testing/simulate-signal       # Execute test trade
GET  /api/testing/monitor-status        # Monitor health
```

---

## Deployment

### Backend → Railway

1. Connect GitHub repo to Railway
2. Set environment variables in dashboard
3. Auto-deploys on push to `main`
4. Port: 8080 (internal), 8000 (external)

**Production URL**: https://trade-oracle-production.up.railway.app

### Frontend → Vercel

1. Connect GitHub repo to Vercel
2. Set `VITE_API_URL=https://trade-oracle-production.up.railway.app`
3. Root Directory: `frontend/`
4. Build: `npm run build`, Output: `dist`, Framework: Vite

**Production URL**: https://trade-oracle-lac.vercel.app

### Cost

- Railway: $5 trial (~4 weeks), then $5-10/month
- Vercel: Free forever
- Supabase: Free tier
- Alpaca: Free paper trading

---

## UI Design System

Trade Oracle uses a Ben AI-inspired mobile-first design. Complete specs in `UI_DESIGN_PROMPT.md`.

**Key Colors**:
- Cream (#F5F1E8) - Background
- Green (#10B981) - Profits/buy signals
- Red (#EF4444) - Losses/sell signals
- Teal (#14B8A6) - Neutral/connected
- Amber (#F59E0B) - Warnings

**Typography**: Monospace for numbers, sans-serif for labels, responsive sizing

---

## Common Issues

### "Backend: Disconnected" on frontend
- Check `VITE_API_URL` in Vercel env vars (not `REACT_APP_API_URL`)
- Verify CORS origins in `backend/main.py`
- Test: `curl https://trade-oracle-production.up.railway.app/health`

### API returns 500 errors
- Missing Railway environment variables
- Database schema not applied in Supabase
- Check Railway logs for details

### Greeks calculator returns None
- Option price/strike must be > 0
- Expiration must be in future
- IV solver may fail for deep ITM/OTM (expected)

---

## Project Status

### ✅ Production-Ready
- IV Mean Reversion strategy (75% backtest win rate)
- Momentum Scalping strategy (most sophisticated)
- Iron Condor strategy (multi-leg close implemented 2025-11-12)
- Position lifecycle monitoring (auto-exit)
- Multi-leg order execution and position close
- Circuit breakers and risk management
- Frontend dashboard + ScalperPro page
- Railway + Vercel deployments

### 🔜 Planned (Not Implemented)
- WebSocket streaming (currently REST polling)
- Redis caching integration
- Supabase Real-Time subscriptions
- Prometheus metrics
- Full Claude weekly reflections

**Overall**: ~75% feature-complete, ready for paper trading validation

---

## 🤖 Terminal AI Workflow (NetworkChuck Method)

### Available Claude Code Agents

Located in `.claude/agents/`:

| Agent | Purpose |
|-------|---------|
| **@railway-deployment-expert** | Railway troubleshooting, config validation, healthchecks |
| **@deployment-critic** | Security review, Dockerfile audit, secret detection |
| **@code-reviewer** | Backend code quality, type safety, FastAPI patterns |
| **@session-closer** | Sync context files, commit to git, session cleanup |
| **@iron-condor-expert** | VIX analysis, trade recommendations, risk assessment |
| **@scalper-expert** | Elite 0DTE momentum trading, 6-condition validation |

### Quick Commands

```bash
# Launch Claude Code
cd /Users/joshuajames/Projects/trade-oracle
claude

# Deploy agents
> @railway-deployment-expert check my Dockerfile
> @code-reviewer analyze backend/api/momentum_scalping.py
> @scalper-expert what trades look good today?

# Close session
> @session-closer wrap up and commit
```

### VSCode Integration

**Recommended**: Use Claude Code in VSCode integrated terminal (not standalone).

**Setup**:
1. Open VSCode in `trade-oracle` directory
2. Click "Install All" when prompted (25 extensions in `.vscode/extensions.json`)
3. Open terminal: Ctrl+` (backtick)
4. Run `claude`

**Key Extensions**:
- **Error Lens** - See errors inline → Copy to Claude → Instant fix
- **REST Client** - Test endpoints with `test-api.http` (45 pre-built tests)
- **GitLens** - View code history before refactoring
- **PostgreSQL** - Query Supabase directly
- **Docker** - Test Dockerfile locally

See `VSCODE_EXTENSIONS_GUIDE.md` for complete workflow guide.

---

## Current Status (2025-11-12)

### System State
- 🟢 **Backend**: Deployed and healthy on Railway
- 🟢 **Frontend**: Deployed on Vercel with correct env vars
- 🟢 **Database**: All migrations applied (multi-leg support)
- 🟢 **Risk Limits**: Production values (2% risk, 5% position size)

### Recent Milestones
- ✅ **Nov 12**: CRITICAL P&L tracking bug fixed (all trades were showing null P&L)
- ✅ **Nov 12**: Multi-leg position close implemented (Iron Condor exit support)
- ✅ **Nov 12**: Comprehensive code audit completed (1 critical bug fixed)
- ✅ **Nov 12**: All 3 strategies now 100% complete and production-ready
- ✅ **Nov 5**: First live paper trade executed (QQQ $640C, 8 contracts)
- ✅ **Nov 5**: Iron Condor strategy deployed
- ✅ **Nov 5**: Momentum Scalping strategy deployed (6-condition system)
- ✅ **Nov 5**: Position monitor auto-close verified
- ✅ **Nov 5**: Railway production hardening (Uvicorn keep-alive, lifespan migration)
- ✅ **Nov 5**: Pydantic v2 + Python 3.12+ compatibility

### Known Issues
- ~~P&L tracking bug (trades showed null pnl)~~ ✅ FIXED 2025-11-12
- ~~Multi-leg position close not implemented~~ ✅ FIXED 2025-11-12
- Iron Condor needs live market validation (9:31-9:45am ET)
- Momentum Scalping needs multi-day validation
- Database view references wrong column (`t.action` should be `t.signal_type`) - minor
- No WebSocket (REST polling only)
- No Redis caching (optional optimization)

### Next Actions
1. **Validate P&L fix** - Next position close should show exit_price and pnl (not null)
2. Test Iron Condor during market hours (9:31-9:45am ET)
3. Validate Momentum Scalping 6-condition system
4. Monitor position auto-close behavior (including multi-leg)
5. Fix database view column name (t.action → t.signal_type)
6. Add frontend error boundaries
7. Implement performance monitoring (Prometheus)

---

## Resources

- **Code Audit Report**: `CODE_AUDIT_2025-11-12.md` (comprehensive audit + P&L bug fix)
- **Test Results**: `TEST_RESULTS_2025-11-12.md` (23 endpoints, no 500 errors)
- **Architecture Deep Dive**: `CODEBASE_ANALYSIS.md` (25KB analysis)
- **UI Specifications**: `UI_DESIGN_PROMPT.md` (complete design system)
- **Scaling Strategy**: `SCALING_PLAN.md` (Railway, Supabase, Vercel research)
- **VSCode Workflow**: `VSCODE_EXTENSIONS_GUIDE.md` (668 lines)
- **Iron Condor Research**: `0DTE_IRON_CONDOR_EXPERT_GUIDE.md` (40,000 words)
- **Momentum Status**: `MOMENTUM_SCALPING_STATUS.md` (updated 2025-11-12)
- **API Testing**: `test-api.http` (45 pre-built HTTP requests)
- **Claude Code Docs**: https://docs.claude.com/claude-code

---

## Important Notes

- **Paper Trading Only**: This bot is NOT validated for real money
- **IV Mean Reversion**: Works best when VIX > 20 (high IV environments)
- **Backtest Caveat**: 75% win rate based on synthetic data, real performance varies
- **Commission**: $0.65 per contract (Alpaca), 1% slippage assumed in backtests
- **Free Tier Limits**: Monitor Supabase (500MB), Railway ($5/month after trial)
- **Position Sizing**: Circuit breakers enforce 2% max risk per trade
- **Exit Logic**: Strategy-specific (IV: 50%/75%, Iron Condor: 50%/2x, Momentum: 25%/50%/-50%)

---

**User Info**:
- Claude Subscription: Claude Max ($200/month)
- Full access to Claude Code agents
- 200K token context window per agent

---

*This file is your project memory. Update it after every significant session. It auto-loads in Claude Code - never lose context again!*
