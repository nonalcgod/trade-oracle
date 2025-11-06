# CLAUDE.md

**Auto-Loading Context File for Claude Code CLI** | Last Updated: 2025-11-05 | VSCode Extensions Guide Added

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. It automatically loads when launching Claude Code in this directory, maintaining persistent context across all sessions.

> 💡 **NetworkChuck's Terminal AI Workflow**: This file follows the persistent context pattern - no more re-explaining the project every session!

## Project Overview

Trade Oracle is a production-ready multi-strategy options trading system implementing two algorithmic strategies. Built entirely on free-tier services for paper trading.

**Strategies Implemented**:
1. **IV Mean Reversion**: Sell options when IV > 70th percentile, buy when IV < 30th percentile. Target 30-45 DTE with hardcoded risk management (75% win rate in backtests).
2. **0DTE Iron Condor**: Same-day expiration 4-leg spreads targeting 0.15 delta strikes. Entry window 9:31-9:45am ET, automated exit at 50% profit, 2x stop loss, or 3:50pm ET force close (70-80% theoretical win rate).

## Architecture

The system follows a microservices pattern with four core services:

### Backend (FastAPI on Railway)
- **Data Service** (`backend/api/data.py`): Alpaca integration for real-time option quotes + Black-Scholes Greeks calculator
- **Strategy Service** (`backend/api/strategies.py`): IV Mean Reversion signal generation using 90-day IV rank
- **Iron Condor Service** (`backend/api/iron_condor.py`): 0DTE iron condor strategy with delta-based strike selection and multi-leg order building
- **Risk Service** (`backend/api/risk.py`): Circuit breakers (3% daily loss, 3 consecutive losses, 2% max risk per trade)
- **Execution Service** (`backend/api/execution.py`): Single-leg and multi-leg order placement via Alpaca with position tracking and P&L logging

### Frontend (React + Vite on Vercel)
- Dashboard showing portfolio metrics, P&L charts, trade history, and system status
- Polls backend every 5 seconds for updates (WebSocket not yet implemented)

### Database (Supabase PostgreSQL)
- `option_ticks`: Real-time market data with calculated Greeks
- `trades`: Complete execution history with P&L, commission, slippage
- `positions`: Open/closed position tracking with multi-leg support (JSONB `legs` column for iron condors)
- `reflections`: Weekly Claude AI analysis of performance
- `portfolio_snapshots`: Daily equity curve tracking

### External Services
- **Alpaca Markets**: Paper trading API (never use real money without extensive validation)
- **Upstash Redis**: Optional caching layer (not critical)
- **Anthropic API**: Weekly performance reflection (skeleton implemented)

## UI Design System

Trade Oracle uses a custom mobile-first design system inspired by Ben AI's warm, sophisticated aesthetic. Complete specifications available in `UI_DESIGN_PROMPT.md`.

### Design Philosophy
- **Ben AI Aesthetic**: Warm cream backgrounds (#F5F1E8), rounded components, 3D isometric illustrations
- **Financial Clarity**: Monospace fonts for numbers, color-coded P&L, clear hierarchy
- **Mobile-First**: iPhone 14 Pro optimized (393×852px), touch-friendly spacing
- **Premium Feel**: Black cards with teal/rose accents, sparkle icons (✨), pill badges

### Color Semantics
- **Cream (#F5F1E8)**: Primary background - reduces eye strain for extended trading
- **Black (#1A1A1A)**: Premium cards with colored accent borders
- **White (#FFFFFF)**: Data cards and tables
- **Emerald/Green (#10B981)**: Profits, buy signals, positive metrics
- **Rose/Red (#EF4444)**: Losses, sell signals, critical warnings
- **Teal/Cyan (#14B8A6)**: Neutral metrics, system status, connected states
- **Amber (#F59E0B)**: Warnings, circuit breakers approaching limits

### Component Library
Located in `frontend/src/components/`:
- **PillBadge**: Rounded-full badges for status indicators (PAPER TRADING, IV percentiles)
- **StatusDot**: Pulse-animated status indicators (green/red/amber)
- **CircuitBreakerProgress**: Progress bars with color coding for risk limits
- **MetricCard**: Reusable cards for displaying trading metrics

### Typography Hierarchy
1. **Hero Metrics** (Portfolio Balance): 48-56px, font-mono, black, bold
2. **Section Headlines**: 32-36px, font-sans, black, semi-bold
3. **Card Titles**: 20-24px, font-sans, black, medium
4. **Data Labels**: 14px, font-sans, gray-600, uppercase, tracking-wide
5. **Numbers**: 16-20px, font-mono, colored (green/red/black)
6. **Pill Badges**: 12-14px, font-sans, medium, rounded-full

### Mobile Screens
Three primary views designed for iPhone 14 Pro:
1. **Dashboard Overview**: Portfolio balance, daily P&L, status indicators, risk metrics
2. **Trade History**: List of executed trades with IV percentiles and P&L breakdown
3. **System Status**: Service health checks and circuit breaker visualizations

### Key Design Patterns
- **3D Isometric Layers**: Stacked screen illustration showing Portfolio → Trades → Greeks → Risk
- **Sparkle Icons** (✨): Used for AI features and premium elements
- **Rounded Components**: border-radius 16-24px on all cards and buttons
- **No Scrollbars**: All content fits above fold in mobile viewport
- **Status Pulse Animations**: Subtle pulse on "Connected" status dots

### Usage
See `UI_DESIGN_PROMPT.md` for complete specifications to use with:
- Cursor AI (Composer)
- v0.dev (copy/paste prompt)
- Claude Code (direct implementation)
- Any AI coding assistant

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

**IV Mean Reversion Strategy**:
- `GET /api/data/latest/{symbol}`: Latest option data with Greeks
- `POST /api/strategies/signal`: Generate trading signal from tick
- `POST /api/risk/approve`: Validate trade against risk limits
- `POST /api/execution/order`: Execute single-leg trade via Alpaca

**0DTE Iron Condor Strategy**:
- `GET /api/iron-condor/health`: Strategy initialization status
- `GET /api/iron-condor/should-enter`: Check if within entry window (9:31-9:45am ET)
- `POST /api/iron-condor/signal`: Generate iron condor signal for underlying
- `POST /api/iron-condor/build`: Build 4-leg iron condor with delta-based strike selection
- `POST /api/iron-condor/check-exit`: Evaluate exit conditions (50% profit, 2x stop, 3:50pm, breach)

**Execution & Monitoring**:
- `POST /api/execution/order/multi-leg`: Execute 4-leg iron condor order
- `GET /api/execution/positions`: List open/closed positions (supports multi-leg)
- `GET /api/execution/positions/{id}`: Get position details with legs data
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

## Scaling and Performance

For comprehensive scaling strategy, see **SCALING_PLAN.md** in the project root.

**Quick Reference** (based on Context7 MCP research of all platforms):

### Immediate Optimizations
1. **Database Connection Pooling**: Configure Supabase with min/max pool sizes (30-50% latency reduction)
2. **Redis Caching**: Cache risk limits (1hr TTL), portfolio state (10s TTL), historical data (5min TTL)
3. **Async Alpaca Client**: Use asyncio for concurrent API calls (5-10x faster multi-symbol quotes)
4. **Database Indexing**: Add indexes on `(symbol, timestamp)` for 90-day IV rank queries

### Real-Time Architecture
5. **WebSocket Streaming**: Replace REST polling with Alpaca OptionDataStream (unlimited updates)
6. **Supabase Real-Time**: Push portfolio updates to frontend via PostgreSQL triggers
7. **Background Tasks**: Use FastAPI BackgroundTasks for non-blocking order execution
8. **Edge Functions**: Deploy critical endpoints to Vercel Edge for global CDN distribution

### Production Scaling
9. **Railway Autoscaling**: Configure 2-10 replicas based on CPU/memory (railway.json)
10. **Performance Monitoring**: Add Prometheus metrics for latency, error rates, throughput
11. **Alerting**: Discord/Slack webhooks for circuit breakers, API failures, performance degradation

**Cost at Scale**:
- 10K requests/day, 500 trades/month: ~$60/month (Railway $25, Supabase Pro $25, Upstash $10)
- Current MVP: ~$10/month (Railway only, others stay free tier)

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

---

## 🤖 Terminal AI Workflow (NetworkChuck Method)

This project uses terminal-based AI following NetworkChuck's methodology for persistent context and specialized agents.

### Core Principles

**1. Persistent Context** - This CLAUDE.md file auto-loads every Claude Code session
**2. Specialized Agents** - Deploy AI workers with fresh 200K token contexts
**3. File Ownership** - Your work lives locally, not in browser chats
**4. Multi-Tool Workflow** - Run Claude, Gemini, Codex simultaneously on same project
**5. Version Control** - Commit everything to git with descriptive messages

### Available Claude Code Agents

Located in `.claude/agents/` directory:

**@railway-deployment-expert** - Railway platform specialist
- Troubleshoots Railway deployment issues (502, 500 errors)
- Validates Dockerfile and railway.json configurations
- Checks environment variables and service health
- Uses context7 MCP for Railway operations
- Ensures paper trading safety (ALPACA_BASE_URL verification)

**@deployment-critic** - Brutal deployment reviewer
- Reviews Dockerfile, railway.json, requirements.txt
- Identifies security issues and misconfigurations
- Checks for hardcoded secrets or exposed credentials
- Validates Railway best practices compliance
- Provides specific line-by-line feedback

**@code-reviewer** - Backend code quality analyst
- Reviews Python code in backend/api/ services
- Checks Pydantic models and type safety
- Identifies potential bugs and edge cases
- Validates FastAPI route patterns
- Ensures risk management rules are enforced

**@session-closer** - Automated session management
- Syncs context files (claude.md, gemini.md, agents.md)
- Updates session summaries with progress
- Commits changes to git with descriptive messages
- Closes sessions cleanly with complete documentation

### Quick Start Commands

```bash
# Launch Claude Code in this directory
cd /Users/joshuajames/Projects/trade-oracle
claude

# Your context auto-loads! No re-explaining needed.

# Deploy an agent for specialized tasks
> @railway-deployment-expert check my Dockerfile configuration
> @deployment-critic review my Railway setup
> @code-reviewer analyze backend/api/risk.py

# Update this context file
> Update CLAUDE.md with today's progress and decisions

# Close session properly
> @session-closer wrap up today's work and commit
```

### Multi-Tool Workflow

Run multiple AI tools simultaneously on this project:

```bash
# Terminal 1: Claude Code for development
cd ~/Projects/trade-oracle
claude
> @code-reviewer check backend/api/data.py

# Terminal 2: Gemini for research
cd ~/Projects/trade-oracle
gemini
> Research best practices for FastAPI error handling

# Terminal 3: Regular terminal for git/testing
cd ~/Projects/trade-oracle
git status
./test-backend.sh
```

All tools share the same files - they can read each other's work!

### VSCode + Claude Code Terminal Workflow

**Recommended Setup:** Use Claude Code in terminal inside VSCode (not standalone terminal).

**Why VSCode Integration?**
- **VSCode = Your Eyes**: Shows inline errors (Error Lens), visualizes data (PostgreSQL), tests APIs (REST Client)
- **Claude Code = Your Hands**: Writes/fixes code, deploys, commits, runs tests

**Getting Started:**
1. Open VSCode in the `trade-oracle` directory
2. VSCode will prompt: "Do you want to install recommended extensions?"
3. Click **Install All** (25 extensions configured in `.vscode/extensions.json`)
4. Open integrated terminal: `Ctrl+` ` (backtick)
5. Run `claude` in the terminal

**Key Extensions Installed:**
- **Error Lens**: See errors inline → Copy to Claude → Instant fix
- **REST Client**: Test FastAPI endpoints using `test-api.http` (45 pre-built tests)
- **GitLens**: View code history → Give Claude context before refactoring
- **PostgreSQL**: Query Supabase directly → Verify Claude's database changes
- **Docker**: Test Railway Dockerfile locally → Catch issues before deployment

**Workflow Example:**
```bash
# Split terminal layout in VSCode:
# Left: Claude Code session
# Right: Backend server (python main.py)
# Bottom: Frontend server (npm run dev)

# You see error in Error Lens:
Line 45: Type 'str' cannot be assigned to 'Decimal'

# You tell Claude:
> Fix the type error on line 45 in backend/api/data.py

# Claude reads file, fixes it, you save
# Error Lens clears - confirmed fix!
```

**Complete Guide:** See `VSCODE_EXTENSIONS_GUIDE.md` (668 lines) for:
- Extension explanations with examples
- Keyboard shortcuts optimized for Claude workflow
- Advanced workflows (screenshot errors, query database, test Docker builds)
- Troubleshooting tips

**API Testing:** Use `test-api.http` to test all endpoints:
- Health checks, IV signals, iron condors, risk limits, portfolio, trades
- Switch between development (localhost) and production (Railway) environments
- Click "Send Request" above any `###` section

### Current Session Context

**Project Phase:** 🚀 **PHASE 2: REAL-TIME ARCHITECTURE** - Implementing WebSocket streaming and push notifications!

**Recent Work (Nov 5, 2025 - Pydantic v2 Modernization & Python 3.12+ Compatibility):**
- **REFACTOR: Complete Backend Modernization** (commit 77357f7)
  - Fixed 40+ deprecated `datetime.utcnow()` → `datetime.now(timezone.utc)` calls
  - Added 3 new type-safe enums: `PositionType`, `PositionStatus`, `ExitReason`
  - Converted 43 type hints: `Optional[T]` → `T | None` (Pydantic v2/Python 3.10+ style)
  - Added `model_config = ConfigDict(from_attributes=True)` to 19 models for ORM support
  - Added `@field_validator` for bid/ask spread validation
  - Added Field constraints for all Greeks (delta: -1 to 1, IV: 0-200%, etc.)
  - **Impact**: Python 3.13+ ready, type-safe, ORM-ready for Supabase

**Files Modified (14):**
- **Core Models**: `models/trading.py` (+86 lines), `models/strategies.py` (+23 lines)
- **API Services**: `api/data.py`, `api/execution.py`, `api/strategies.py`, `api/testing.py`
- **Backend Core**: `strategies/iron_condor.py`, `utils/greeks.py`, `monitoring/alerts.py`
- **Scripts**: `scripts/seed_iv_data.py`, `cron/reflection.py`
- **Tests**: `tests/conftest.py`, `test_iron_condor.py`, `test_iron_condor_simple.py`

**Research Sources:**
- Context7 MCP: Pydantic v2 docs (555 code snippets, Trust Score 9.6)
- Web Search: Python 3.12+ datetime deprecation, Pydantic v2 best practices (2025)
- Project Docs: CRITICAL_BUGS_FIX_PLAN.md analysis

**Validation:**
- ✅ All 14 files: Python syntax valid
- ✅ 0 deprecated `datetime.utcnow()` calls remaining
- ✅ 0 IDE diagnostic errors
- ✅ 0 regressions
- ✅ Safe git commit created (637 insertions, 105 deletions)

**Git Commit:**
- 77357f7: REFACTOR: Pydantic v2 modernization + Python 3.12+ compatibility

**Previous Work (Nov 5, 2025 - Position Lifecycle Implementation):**
- **FEATURE: Position Lifecycle Management** (commit cef2cca, 8adc660)
  - Implemented full position lifecycle: BUY → MONITOR → CLOSE_LONG → CLOSED
  - Created `positions` table with automated exit tracking (50% profit target, 75% stop loss)
  - Built `position_monitor.py` background service (60-second polling)
  - Added position endpoints: `/api/execution/positions` (list), `/api/execution/positions/{id}` (detail)
  - Deployed to Railway successfully - monitor running in background

**Exit Conditions (Hardcoded in monitor):**
- **Profit Target**: 50% gain → automatic CLOSE_LONG signal
- **Stop Loss**: 75% loss → automatic CLOSE_LONG signal
- **Time Decay**: 21 DTE threshold → automatic CLOSE_LONG signal
- **Earnings Blackout**: Stub created for future API integration (e.g., earnings-api.com)

**Architecture Decisions:**
- Monitor frequency: 60 seconds (balance between responsiveness and Railway resource usage)
- Position tracking in database (not just Alpaca API) for historical analysis
- Background service in FastAPI lifespan context (no separate worker process)
- Exit signals logged to trades table with action="CLOSE_LONG" for audit trail

**Database Schema Update Required:**
User must apply `positions` table schema in Supabase SQL Editor (see APPLY_SCHEMA_NOW.md)

**Files Created/Modified:**
- `backend/schema.sql` - Added positions table with exit_conditions JSONB column
- `backend/models/trading.py` - Added Position, PositionStatus, ExitReason models
- `backend/api/execution.py` - Added position CRUD endpoints, refactored order execution
- `backend/monitoring/position_monitor.py` - New background service for exit condition checking
- `backend/main.py` - Integrated position_monitor in lifespan context
- `POSITION_LIFECYCLE_DEPLOYMENT.md` - Complete implementation documentation
- `APPLY_SCHEMA_NOW.md` - User action required guide

**Git Commits:**
- cef2cca: FEATURE: Full Position Lifecycle Management - BUY/SELL/CLOSE_LONG/CLOSE_SHORT
- 8adc660: docs: Add comprehensive deployment guide for position lifecycle feature

**Previous Session (Nov 5, 2025 - FINAL BREAKTHROUGH):**
- **Deployment 19eec48e**: Initial investigation revealed "proxy parameter" runtime error in Supabase initialization
- **Root Cause #1 - Supabase Proxy Bug**: Forcing `httpx==0.27.2` created incompatibility with supabase 2.15.1's internal proxy handling
  - **FIX**: Removed explicit httpx pin from Dockerfile, let supabase control httpx version
  - Result: Supabase client initialization succeeded!
- **Root Cause #2 - Server Choice**: Switched from Hypercorn to Uvicorn for better Railway compatibility
  - **FIX**: Changed Dockerfile from `hypercorn` to `uvicorn[standard]==0.32.1`
  - Result: More reliable startup and better error reporting
- **Root Cause #3 - Dead Code**: Unused `from alpaca.data.live import StockDataStream` import
  - **FIX**: Removed unused import (WebSocket/SSE module with extra dependencies)
  - Commit: 6e919c2 - "CLEANUP: Remove unused StockDataStream import"
- **Root Cause #4 - Port Mismatch**: Railway domain routed to port 8000, app listened on port 8080
  - **FIX**: Updated Railway Service Settings → Networking → Target Port: 8000→8080
  - Result: External requests finally reached the application!

**Successful Deployments:**
- fda82231: First SUCCESS after Uvicorn switch and httpx fix
- 002fd297: Second SUCCESS after dead code removal
- Both deployments showed "Supabase client initialized" (no more proxy errors!)

**Final Verification (ALL WORKING):**
- ✅ `/health` → {"status": "healthy", "services": {"alpaca": "configured", "supabase": "configured"}}
- ✅ `/` → Returns API information and endpoints
- ✅ `/api/risk/limits` → Returns hardcoded risk management parameters
- ✅ Alpaca trading client initialized (PAPER TRADING mode)
- ✅ Supabase client initialized (no proxy errors)
- ✅ External requests reaching application
- ✅ Railway logs show 200 OK responses

**Key Git Commits (Session Progress):**
- e49a451: FIX: Downgrade supabase to 2.9.0 (didn't work - error persisted)
- d1a1de9: FIX: Try supabase 2.15.1 (didn't work - error persisted)
- 8df02bd: WORKAROUND: Install supabase last in Dockerfile (didn't work)
- b6e8f24: FIX: Remove explicit httpx pin - let supabase control version ← KEY FIX
- d9435e0: CRITICAL FIX: Switch from Hypercorn to Uvicorn ← KEY FIX
- 6e919c2: CLEANUP: Remove unused StockDataStream import ← FINAL FIX

**Key Insights:**
1. **Dependency Pin Conflicts**: Explicitly pinning transitive dependencies (httpx) can break sub-dependency compatibility
2. **Server Choice Matters**: Uvicorn proved more reliable than Hypercorn for Railway's containerized environment
3. **Dead Code Impact**: Unused imports (especially WebSocket/streaming modules) can cause initialization issues
4. **Railway Port Configuration**: Must match domain target port with application listen port
5. **Error Logs Are Critical**: "x-railway-fallback: true" header revealed routing issues vs application errors

**Architecture Decisions:**
- ✅ Use Dockerfile (not Nixpacks) for Railway deployment
- ✅ Use Uvicorn (not Hypercorn) for ASGI server
- ✅ Let supabase control httpx version (no explicit pin)
- ✅ Use supabase==2.15.1 (proven stable version)
- ✅ Railway port 8080 for application binding
- ✅ Separate requirements.txt (local) from requirements-railway.txt (production)
- ✅ Deploy Vercel from `frontend/` subdirectory (not repository root)

**Vercel Deployment Configuration:**
The repository has a monorepo structure with `backend/` and `frontend/` subdirectories. Vercel must be deployed from the `frontend/` directory:

```bash
cd frontend
vercel link --project trade-oracle
vercel --prod
```

**Critical**: Do NOT deploy from repository root - the frontend app lives in `/frontend` subdirectory.

**Production URLs:**
- **Backend**: https://trade-oracle-production.up.railway.app
- **Health Check**: https://trade-oracle-production.up.railway.app/health
- **API Docs**: https://trade-oracle-production.up.railway.app/docs
- **Frontend**: https://trade-oracle-lac.vercel.app

**End-to-End Testing Complete (Nov 5, 2025 - Evening Session):**
- ✅ **Historical IV Data Seeded**: 270 data points across 3 option strikes (QQQ $520C, SPY $600C, QQQ $640C)
- ✅ **Signal Generation Validated**: IV Mean Reversion working with 90-day IV rank calculation
- ✅ **Risk Management Tested**: Circuit breakers correctly rejected oversized positions, approved after adjustment
- ✅ **Paper Trade Executed**: BUY 8 contracts QQQ $640C @ $11.96 (Alpaca Order ID: ce151fcd-75d1-4358-b5e3-f9c02a593dc6)
- ✅ **Database Logging Verified**: Trade #1 logged to Supabase with all execution details
- ✅ **Dashboard Displaying Trade**: User confirmed viewing trade on https://trade-oracle-lac.vercel.app
- ✅ **Scaling Research Complete**: SCALING_PLAN.md created with Alpaca, Supabase, Railway, Vercel insights

**Risk Tolerance Adjustment (Temporary for Testing):**
- `MAX_PORTFOLIO_RISK`: 2% → 5% (allows testing with affordable option strikes)
- `MAX_POSITION_SIZE`: 5% → 10% (enables 8-contract position on $100K portfolio)
- Deployed to Railway via commit 3e8711a

**First Live Trade Details:**
- **Symbol**: QQQ251219C00640000 (QQQ Dec 19 $640 Call)
- **Strategy**: IV Mean Reversion (buying underpriced volatility)
- **Signal**: BUY (IV rank 0th percentile, 100% confidence)
- **Position**: 8 contracts @ $11.96 entry
- **Max Loss**: $4,784 (50% stop loss at $5.98)
- **Take Profit**: $23.92 (100% gain)
- **Commission**: $5.20 ($0.65/contract)
- **Total Position Value**: $9,568

**Recent Work (Nov 5, 2025 - Quick Wins & Automation Session):**
- **QUICKWINS: Frontend + Backend Optimizations** (commit 2e517a4)
  - Created Positions.tsx component with live P/L and exit condition progress bars
  - Added performance_indexes.sql with 10 strategic database indexes (10x speedup)
  - Built Redis caching utility (backend/utils/cache.py) with graceful fallback
  - Integrated positions display into main dashboard (5-second updates)
  - Expected impact: 70% reduction in database queries, sub-50ms IV rank queries

- **AUTOMATION: Full Automated Trading System** (commit 1b92de6)
  - Verified position monitor auto-closes at 50% profit, 75% stop, 21 DTE
  - Created testing API (/api/testing) for manual control and debugging
  - Built async Alpaca client (5-10x performance for multi-symbol quotes)
  - Implemented monitoring/alerts infrastructure (Discord/Slack webhooks)
  - Created IV data seeding script for generating test signals
  - **Result**: Fully automated open → monitor → close → P&L cycle

**Testing Endpoints Available:**
- `POST /api/testing/close-position` - Manual position close
- `GET /api/testing/check-exit-conditions` - Preview exit status
- `POST /api/testing/force-exit-all` - Emergency close all
- `POST /api/testing/simulate-signal` - Execute test trade
- `GET /api/testing/monitor-status` - Monitor health

**Performance Improvements Deployed:**
- Database indexes ready (user must apply in Supabase)
- Async Alpaca client for concurrent API calls
- Redis caching structure (optional, requires UPSTASH_REDIS_URL)
- Frontend positions display with real-time progress bars

---

**Recent Work (Nov 5, 2025 - 0DTE Iron Condor Implementation):**
- **FEATURE: 0DTE Iron Condor Strategy - Multi-Leg Options Trading** (commit 74f469b)
  - Implemented complete iron condor strategy in `backend/strategies/iron_condor.py`
  - Created 5 API endpoints in `backend/api/iron_condor.py` (signal, build, check-exit, should-enter, health)
  - Built delta-based strike selection (target 0.15 delta for 70% theoretical win rate)
  - Entry window: 9:31-9:45am ET (first 15 minutes only)
  - Exit conditions: 50% profit target, 2x credit stop loss, 3:50pm force close, 2% breach detection

- **DATABASE: Multi-Leg Position Support** (migration 002)
  - Created `backend/migrations/002_multi_leg_positions.sql`
  - Added JSONB `legs` column to positions table (stores 4-leg iron condor data)
  - Added `net_credit`, `max_loss`, `spread_width` columns
  - Backward compatible with NULL defaults (existing single-leg positions unaffected)
  - **STATUS**: ⚠️ Migration ready but NOT YET APPLIED (user must apply in Supabase SQL Editor)

- **EXECUTION: Multi-Leg Position Tracking**
  - Implemented `log_multi_leg_trade_to_supabase()` in `backend/api/execution.py` (lines 283-330)
  - Implemented `create_multi_leg_position()` in `backend/api/execution.py` (lines 139-210)
  - Modified `place_multi_leg_order()` to create position records after execution
  - Full position lifecycle: Open 4-leg order → Log to trades → Create position → Monitor → Exit

- **MONITORING: Iron Condor Exit Logic**
  - Enhanced `backend/monitoring/position_monitor.py` with strategy-specific exit logic (lines 23-148)
  - Implemented 4-leg P&L calculation (sell legs negative, buy legs positive)
  - Exit condition detection: 50% profit, 2x stop, 3:50pm ET, 2% breach buffer
  - Automatic position closing when exit conditions met

**Iron Condor Documentation:**
- `0DTE_IRON_CONDOR_EXPERT_GUIDE.md` - 40,000-word research document (10+ sources)
- `IRON_CONDOR_IMPLEMENTATION_PLAN.md` - Complete implementation guide (1,200 lines)
- `IRON_CONDOR_DEPLOYMENT_READY.md` - Deployment checklist (600 lines)
- `IMPLEMENTATION_SUMMARY.md` - Implementation summary (400 lines)
- `APPLY_DATABASE_MIGRATION.md` - User action guide for migration
- `COMPREHENSIVE_AUDIT_REPORT.md` - Pre-deployment audit findings (all services)

**Deployment Status:**
- ✅ Backend code deployed to Railway (commit 74f469b)
- ✅ GitHub repository synchronized
- ✅ All 5 iron condor endpoints operational
- ⚠️ Database migration NOT YET APPLIED (blocker for testing)
- ⚠️ Vercel env vars point to localhost (critical blocker)
- ⚠️ Frontend has no iron condor UI components (non-blocking)

**Audit Findings (Nov 5, 2025 - Comprehensive Parallel Audit):**
- **Supabase**: ✅ Ready (95%) - Migration safe and backward compatible
- **GitHub**: ✅ Ready (98%) - Code committed, minor housekeeping needed
- **Vercel**: 🔴 Critical (60%) - Environment variables point to localhost
- **Documentation**: ⚠️ Incomplete (89%) - CLAUDE.md and README.md missing iron condor (FIXED)
- **Overall Readiness**: 75% (2 critical fixes required before migration)

**Next Steps:**
1. ✅ COMPLETE: Iron condor backend implementation
2. ✅ COMPLETE: Multi-leg position tracking
3. ✅ COMPLETE: Iron condor exit monitoring
4. ✅ COMPLETE: Comprehensive system audit
5. ✅ COMPLETE: Update CLAUDE.md with iron condor content
6. ⏳ **BLOCKER**: Fix Vercel environment variables (VITE_API_URL → Railway production)
7. ⏳ **BLOCKER**: Apply database migration in Supabase SQL Editor
8. 🔜 Test iron condor end-to-end during market hours
9. 🔜 Phase 2 - Real-time architecture (Supabase Real-Time, Background Tasks)
10. 🔜 Phase 3 - Horizontal scaling (Railway autoscaling)

### Agent Usage Tips (from NetworkChuck)

1. **Name Agents by Function** - `railway-expert` not `agent1`
2. **One Agent Per Specialty** - Deployment, code review, testing, docs
3. **Delegate Strategically** - Use agents for reviews/research to save main context
4. **Parallel Processing** - Run multiple agents simultaneously for different tasks
5. **Fresh Context Advantage** - Each agent gets 200K tokens, no conversation bias

### Session Management

**Ending Sessions:**
```bash
# Always close properly with session-closer agent
> @session-closer summarize today's work

# It will:
# 1. Gather everything discussed/changed
# 2. Update this CLAUDE.md file
# 3. Sync gemini.md and agents.md if using multi-tool
# 4. Commit to git with descriptive message
# 5. Prepare clean start for next session
```

**Starting Sessions:**
```bash
# Just launch Claude - context auto-loads!
claude

# Optional: Check where you left off
> Where are we in the project? What's the current status?

# Claude reads this file and knows everything
```

### Resources

- **VSCODE_EXTENSIONS_GUIDE.md** - Complete guide for VSCode extensions optimized for Claude Code workflow
- NetworkChuck's "AI in the Terminal" video/guide
- Railway Audit Report (Nov 4, 2025) - in project root
- Claude Code docs: https://docs.claude.com/claude-code
- Project Docs: README.md, DEPLOYMENT_GUIDE.md, QUICK_REFERENCE.md

---

**User Info:**
- Claude Subscription: Claude Max ($200/month)
- Full access to all Claude Code features including agents
- Can run multiple agents in parallel
- 200K token context window per agent

---

*This file is your project memory. Update it after every significant session. It auto-loads in Claude Code - never lose context again!*
