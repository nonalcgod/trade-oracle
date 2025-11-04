# Testing Checklist

Complete all tests before deploying to production.

---

## Phase 1: Local Development Testing

### Backend Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment created: `python -m venv venv`
- [ ] Dependencies installed: `pip install -r backend/requirements.txt`
- [ ] Environment variables configured in `.env`

### Backend API Testing
- [ ] Backend starts without errors: `python backend/main.py`
- [ ] Health endpoint returns 200: `curl http://localhost:8000/health`
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Root endpoint works: `curl http://localhost:8000/`
- [ ] All 4 service endpoints registered in docs

#### Data Service
- [ ] `GET /api/data/option/{symbol}` returns valid data
- [ ] Response includes: symbol, bid, ask, delta, gamma, theta, vega, iv

#### Strategies Service
- [ ] `GET /api/strategies/info` returns strategy parameters
- [ ] Returns: IV_HIGH=0.70, IV_LOW=0.30, DTE_MIN=30, DTE_MAX=45
- [ ] `GET /api/strategies/signal/{symbol}` works (may return null)

#### Risk Service
- [ ] `GET /api/risk/portfolio` returns portfolio state
- [ ] Response includes: balance, daily_pnl, win_rate, consecutive_losses
- [ ] `POST /api/risk/approve` accepts signal and returns approval

#### Execution Service
- [ ] `GET /api/execution/portfolio` returns current portfolio
- [ ] `GET /api/execution/trades` returns empty list initially
- [ ] `GET /api/execution/performance` returns metrics
- [ ] `POST /api/execution/order` accepts order (paper trading)

### Frontend Setup
- [ ] Node.js 16+ installed
- [ ] Dependencies installed: `npm install` (in frontend/)
- [ ] Environment variables configured: `REACT_APP_API_URL=http://localhost:8000`

### Frontend Testing
- [ ] Frontend starts: `npm run dev`
- [ ] Dashboard loads without errors
- [ ] API client initialized correctly
- [ ] No console errors

#### Dashboard Components
- [ ] Portfolio card renders (balance, P&L, win rate, etc.)
- [ ] Trades table renders (empty initially)
- [ ] Charts render without data
- [ ] System info section shows correctly
- [ ] Error banner works (test with bad API URL)

#### API Integration
- [ ] Portfolio data fetches from backend
- [ ] Trades data fetches from backend
- [ ] Health status shows connection status
- [ ] Real-time polling works (5-second updates)

### Database Setup
- [ ] Supabase account created
- [ ] PostgreSQL database initialized
- [ ] Schema imported: Run `backend/schema.sql` in Supabase SQL Editor
- [ ] Verify tables created:
  ```sql
  SELECT table_name FROM information_schema.tables WHERE table_schema='public';
  ```
- [ ] Should list: option_ticks, trades, reflections

---

## Phase 2: Backtest Validation

### Backtest Execution
- [ ] Backtest runs without errors: `python backtest/run_backtest.py`
- [ ] Backtest completes in < 5 minutes
- [ ] Output shows summary statistics

### Backtest Metrics
- [ ] **Sharpe Ratio > 1.2**: Verify in output
  - Expected: 1.2-1.8
  - Actual: ___
  - ✅ / ❌

- [ ] **Win Rate > 55%**: Verify in output
  - Expected: 70-80%
  - Actual: ___
  - ✅ / ❌

- [ ] **Total Trades >= 200**: Verify in output
  - Expected: 200+
  - Actual: ___
  - ✅ / ❌

- [ ] **Realistic Costs Applied**:
  - Commission per trade: $0.65
  - Slippage: 1%
  - Both visible in code and P&L calculation

### Backtest Validation
- [ ] Initial balance: $10,000
- [ ] Final balance: > $10,000
- [ ] Total return: Shown in output
- [ ] No negative Sharpe ratio
- [ ] Win rate reasonable (not 100%)

---

## Phase 3: Integration Testing

### API Integration
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Frontend can reach backend (no CORS errors)
- [ ] All 4 services respond correctly

### Data Flow
- [ ] Portfolio data flows from backend to frontend
- [ ] Dashboard updates from API responses
- [ ] Charts render when trades exist
- [ ] Real-time polling working (check Network tab)

### Database Integration
- [ ] Supabase connected from backend
- [ ] Trades can be inserted to database
- [ ] Queries work from Supabase dashboard

### Error Handling
- [ ] Stop backend → frontend shows error message
- [ ] Bad API URL → proper error displayed
- [ ] Invalid parameters → API returns 400
- [ ] Missing env vars → appropriate warnings logged

---

## Phase 4: Risk Management Testing

### Circuit Breakers
- [ ] Daily loss limit (-3%): Test with mock trade
- [ ] 3 consecutive losses: Verify trading pauses
- [ ] Max position size (5%): Verify sizing correct
- [ ] Risk approval logic: Works as expected

### Kelly Position Sizing
- [ ] Calculates correct position size
- [ ] Never exceeds max limits
- [ ] Responds to win rate changes

### Greeks Calculation
- [ ] Delta calculated correctly
- [ ] Gamma calculated correctly
- [ ] Theta calculated correctly
- [ ] Vega calculated correctly
- [ ] IV rank calculated correctly

---

## Phase 5: Deployment Preparation

### Code Quality
- [ ] No console errors (frontend)
- [ ] No Python errors (backend)
- [ ] No TypeScript compilation errors
- [ ] All imports working correctly
- [ ] No hardcoded URLs or secrets

### Git Repository
- [ ] All changes committed: `git status` shows clean
- [ ] Git history clean
- [ ] README.md updated
- [ ] No sensitive files in repo

### Environment Configuration
- [ ] `.env.example` up to date
- [ ] All required variables documented
- [ ] No secrets in code
- [ ] Environment-specific configs working

### Build Verification
- [ ] Backend builds: `pip install -r requirements.txt`
- [ ] Frontend builds: `npm run build`
- [ ] Build artifacts created successfully
- [ ] No build warnings or errors

---

## Phase 6: Pre-Deployment Checklist

### Backend (Railway)
- [ ] Railway account created
- [ ] GitHub connected to Railway
- [ ] Railway.json configuration correct
- [ ] Build command correct
- [ ] Start command correct

### Frontend (Vercel)
- [ ] Vercel account created
- [ ] GitHub connected to Vercel
- [ ] Build settings configured
- [ ] Environment variables ready

### Infrastructure
- [ ] Supabase database ready
- [ ] Database schema created
- [ ] API credentials obtained:
  - [ ] Alpaca API key
  - [ ] Alpaca secret key
  - [ ] Supabase URL
  - [ ] Supabase anon key
  - [ ] Supabase service key
  - [ ] Anthropic API key

---

## Phase 7: Deployment Testing

### Backend Deployment
- [ ] Code pushed to GitHub: `git push origin main`
- [ ] Railway auto-deploys
- [ ] Deployment succeeds (check Railway logs)
- [ ] Health endpoint returns 200
- [ ] Environment variables loaded correctly
- [ ] All services configured

### Frontend Deployment
- [ ] Code pushed to GitHub
- [ ] Vercel auto-deploys
- [ ] Deployment succeeds
- [ ] Dashboard loads
- [ ] No build errors
- [ ] Environment variable loaded

### Integration Testing (Production)
- [ ] Frontend connects to deployed backend
- [ ] API calls work with deployed URL
- [ ] Portfolio data displays correctly
- [ ] No CORS errors
- [ ] Charts render correctly

### Database Testing (Production)
- [ ] Supabase connected from deployed backend
- [ ] Trades can be logged
- [ ] Data persists in database
- [ ] Queries work from dashboard

---

## Phase 8: Production Validation

### System Status
- [ ] Backend: Healthy & Running
- [ ] Frontend: Deployed & Loading
- [ ] Database: Connected & Data stored
- [ ] Trading: Paper trading mode enabled

### Feature Testing
- [ ] **Portfolio Display**
  - [ ] Balance shows correct amount
  - [ ] Daily P&L calculates correctly
  - [ ] Win rate accurate
  - [ ] Greeks calculated and displayed

- [ ] **Trading**
  - [ ] Signals generated correctly
  - [ ] Risk approval working
  - [ ] Orders placed to Alpaca paper
  - [ ] Trades logged to database

- [ ] **Analytics**
  - [ ] Charts display with sample data
  - [ ] Cumulative P&L chart works
  - [ ] Daily metrics chart works
  - [ ] Trades table displays correctly

- [ ] **Automation**
  - [ ] Cron job configured
  - [ ] Weekly reflection scheduled
  - [ ] Claude analysis runs successfully

### Performance
- [ ] Dashboard load time < 3 seconds
- [ ] API response time < 500ms
- [ ] No memory leaks
- [ ] Database queries efficient

---

## Phase 9: Monitoring Setup

### Logs
- [ ] Railway logs accessible
- [ ] Vercel logs accessible
- [ ] Supabase logs accessible
- [ ] Error tracking enabled

### Alerts
- [ ] Backend down alerts configured
- [ ] Frontend deployment alerts ready
- [ ] Database connection alerts set
- [ ] Trading error alerts ready

### Metrics
- [ ] Dashboard shows real-time updates
- [ ] Performance metrics tracked
- [ ] Win rate monitored
- [ ] P&L tracked correctly

---

## Phase 10: Final Sign-Off

### Safety
- [ ] Paper trading only (not real money)
- [ ] Circuit breakers active
- [ ] Risk limits enforced
- [ ] Trade reviews required before execution

### Documentation
- [ ] README complete and accurate
- [ ] Setup guide complete
- [ ] API documentation generated
- [ ] Deployment guide complete

### Ready for Production?

- [ ] ✅ All backtest criteria passed
- [ ] ✅ All local tests passed
- [ ] ✅ All integration tests passed
- [ ] ✅ All deployment tests passed
- [ ] ✅ Monitoring configured
- [ ] ✅ Safety verified
- [ ] ✅ Documentation complete

**Status**: [ ] Ready for Production | [ ] Needs More Testing

---

## Sign-Off

**Tested By**: _________________________

**Date**: _________________________

**Notes**:
```
[Add any observations or concerns]
```

---

## Test Results Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | | |
| Frontend UI | | |
| Database | | |
| Strategy | | |
| Risk Management | | |
| Integration | | |
| Deployment | | |
| Performance | | |

---

**Remember**: Never skip tests. A bug caught in testing saves money in production.
