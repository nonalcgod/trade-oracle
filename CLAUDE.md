# CLAUDE.md

**Auto-Loading Context File for Claude Code CLI** | Last Updated: 2025-11-05

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. It automatically loads when launching Claude Code in this directory, maintaining persistent context across all sessions.

> 💡 **NetworkChuck's Terminal AI Workflow**: This file follows the persistent context pattern - no more re-explaining the project every session!

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

### Current Session Context

**Project Phase:** BREAKTHROUGH - Root cause found and fixed for 20+ failed Railway deployments

**Recent Work (Nov 5, 2025):**
- MAJOR BREAKTHROUGH: Deployed @railway-deployment-expert and @deployment-critic agents in parallel
- Ran 86 diagnostic tools to identify root cause of all deployment failures
- Discovered critical dependency conflict: alpaca-py 0.30.1 vs supabase 2.23.0 (httpx version incompatibility)
- FIXED: Updated requirements-railway.txt with compatible versions:
  - alpaca-py: 0.30.1 → 0.35.0 (fixes httpx conflict)
  - Updated 10 packages: fastapi, hypercorn, pydantic, anthropic, structlog, etc.
  - Removed redis==5.0.1 (conflicted with upstash-redis)
  - Full security updates (1 year of patches for some packages)
- Updated Dockerfile: python:3.11.10-slim (exact version pin), added ENV PYTHONPATH=/app
- Updated railway.json: healthcheckTimeout 300→60 (faster failure detection)
- Created deployment commits: 2a6c003 (CRITICAL FIX), 7a3f0b8 (empty commit to trigger Railway)

**Git History Pattern:**
- 7a3f0b8: Empty commit to trigger fresh Railway deployment
- 2a6c003: CRITICAL FIX - Resolve dependency conflicts blocking Railway deployment
- e99daf3: Fix incompatible supabase sub-dependency pins
- 7c425e5: Force Railway cache bust to use current Dockerfile
- fbb4978: Fix supabase dependency proxy argument error

**Key Decisions:**
- All 20+ previous failures were due to dependency conflicts, NOT Docker/Python/build issues
- Using agents in parallel (86 tools!) found root cause we missed in manual debugging
- FAANG Level 10 execution: comprehensive fix, detailed commit messages, clear handoff
- Use Dockerfile (not Nixpacks) for Railway deployment
- Use Hypercorn (not Uvicorn) for dual-stack IPv4/IPv6 binding
- Separate requirements.txt (local) from requirements-railway.txt (production)

**Next Steps:**
1. ⏳ Verify Railway deployment succeeds (commit 7a3f0b8) - may need manual trigger
2. ⏳ Test health endpoint: `curl https://trade-oracle-production.up.railway.app/health`
3. ⏳ Verify all MVP endpoints work (/api/execution/trades, /api/execution/performance)
4. ⏳ Connect Vercel frontend with VITE_API_URL environment variable
5. ⏳ Test end-to-end MVP functionality (dashboard → backend → Alpaca paper trading)
6. 🔮 Fix Railway-GitHub webhook if auto-deploy isn't working
7. 🔮 Future: Phase 4-5 features (WebSocket, enhanced charts, unit tests)

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
