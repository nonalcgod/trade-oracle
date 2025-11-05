# Trade Oracle - Next Session Prompt

**Copy and paste this into your next Claude Code session to continue from where we left off.**

---

## Session Context

We just completed implementation of the **0DTE Iron Condor strategy** and ran a comprehensive parallel audit of all services (Supabase, GitHub, Vercel, Documentation). The audit revealed **2 critical blockers** that must be fixed before applying the database migration.

### Current Status

**✅ Completed**:
- Iron condor backend implementation (commit 74f469b)
- Multi-leg position tracking code
- Iron condor exit monitoring logic
- Database migration prepared (`002_multi_leg_positions.sql`)
- Comprehensive system audit (4 parallel agents)
- CLAUDE.md updated with iron condor content (commit acd479d)
- Vercel fix guide created (`FIX_VERCEL_ENV_VARS.md`)

**🔴 Critical Blockers** (Must Fix Before Migration):
1. **Vercel Environment Variables** - Currently point to localhost instead of Railway production
2. **Database Migration** - Ready but not yet applied in Supabase

**📊 System Readiness**: 75% (2 blockers remaining)

---

## Task: Apply Final Fixes and Deploy Iron Condor

### Step 1: Fix Vercel Environment Variables (5 minutes)

Follow the guide in `FIX_VERCEL_ENV_VARS.md`:

1. Go to Vercel Dashboard → trade-oracle → Settings → Environment Variables
2. Update `VITE_API_URL` from `http://localhost:8000` to `https://trade-oracle-production.up.railway.app`
3. Remove `N8N_API_URL` and `NEXT_PUBLIC_*` variables
4. Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
5. Redeploy frontend

**Verification**:
```bash
# Check Railway backend is healthy
curl https://trade-oracle-production.up.railway.app/health

# After redeployment, visit frontend and check browser console
# Should see API calls to Railway, not localhost
```

---

### Step 2: Apply Database Migration (5 minutes)

The migration is ready in `backend/migrations/002_multi_leg_positions.sql`.

**Instructions**:
1. Open Supabase SQL Editor: https://app.supabase.com/project/fltkfgfyjjsijgmhrnqt/sql
2. Copy entire contents of `backend/migrations/002_multi_leg_positions.sql`
3. Paste into SQL Editor
4. Click "Run" (or press Cmd+Enter)
5. Look for success message: ✅ "Multi-leg position columns added successfully"

**Verification**:
```sql
-- Run in Supabase SQL Editor to verify columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'positions'
AND column_name IN ('legs', 'net_credit', 'max_loss', 'spread_width');

-- Should return 4 rows:
-- legs         | jsonb
-- net_credit   | numeric
-- max_loss     | numeric
-- spread_width | numeric
```

---

### Step 3: Test Iron Condor End-to-End (10 minutes)

**IMPORTANT**: Only run during market hours (9:31am-4:00pm ET) when options are trading.

#### Test 1: Build Iron Condor
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "quantity": 1}'
```

**Expected**: JSON response with 4-leg iron condor setup showing strikes and multi_leg_order.

#### Test 2: Execute Multi-Leg Order
```bash
# Use the multi_leg_order from previous response
curl -X POST https://trade-oracle-production.up.railway.app/api/execution/order/multi-leg \
  -H "Content-Type: application/json" \
  -d '{ ... paste multi_leg_order here ... }'
```

**Expected**: Success response with Alpaca order IDs and position created.

#### Test 3: Verify Position Created
```bash
curl "https://trade-oracle-production.up.railway.app/api/execution/positions?status=open"
```

**Expected**: Array with position showing `legs` array with 4 entries (JSONB data).

#### Test 4: Monitor Position Exit Logic
```bash
# Watch Railway logs for position monitor activity
railway logs --tail | grep "iron_condor"
```

**Expected**: Every 60 seconds, should see:
- "Iron condor P&L calculated" with current pnl and pnl_pct
- Position monitor checking exit conditions

---

### Step 4: Verify Full Lifecycle (During Market Hours)

Let one iron condor trade run through its full lifecycle:

1. **Entry** (9:31-9:45am ET): Build and execute iron condor
2. **Monitoring** (9:45am-3:50pm ET): Position monitor polls every 60 seconds
3. **Exit** (when conditions met): Automatic close at 50% profit, 2x stop, or 3:50pm
4. **Database Verification**: Check position status updated to "closed" with exit reason

---

## Success Criteria

After completing all steps, verify:

- [ ] ✅ Vercel frontend connects to Railway backend (not localhost)
- [ ] ✅ Database has `legs`, `net_credit`, `max_loss`, `spread_width` columns
- [ ] ✅ Iron condor can be built via `/api/iron-condor/build`
- [ ] ✅ Multi-leg order executes via `/api/execution/order/multi-leg`
- [ ] ✅ Position created in database with 4-leg JSONB data
- [ ] ✅ Railway logs show "Iron condor P&L calculated" every 60 seconds
- [ ] ✅ Position auto-closes at exit condition
- [ ] ✅ Frontend displays position data from backend

---

## Reference Documents

All documentation is in the repository:

**Implementation Guides**:
- `IRON_CONDOR_IMPLEMENTATION_PLAN.md` - Complete implementation guide (1,200 lines)
- `IRON_CONDOR_DEPLOYMENT_READY.md` - Deployment checklist (600 lines)
- `IMPLEMENTATION_SUMMARY.md` - Implementation summary (400 lines)

**Action Guides**:
- `FIX_VERCEL_ENV_VARS.md` - Vercel environment variable fix (Step 1)
- `APPLY_DATABASE_MIGRATION.md` - Database migration guide (Step 2)
- `COMPREHENSIVE_AUDIT_REPORT.md` - Full audit findings

**Research**:
- `0DTE_IRON_CONDOR_EXPERT_GUIDE.md` - 40,000-word research document

**Context**:
- `CLAUDE.md` - Auto-loads in Claude Code (updated with iron condor content)

---

## Important Notes

**Paper Trading Only**:
- System uses Alpaca paper trading API
- Never use real money without months of validated performance

**Time Sensitivity**:
- Iron condors MUST enter between 9:31-9:45am ET
- Iron condors MUST close by 3:50pm ET (extreme gamma risk after)
- Position monitor enforces automatic 3:50pm close

**Commission Impact**:
- $5.20 round trip ($2.60 entry + $2.60 exit)
- Factor into profitability calculations

**Railway Deployment**:
- Backend: https://trade-oracle-production.up.railway.app
- Auto-deploys on push to `main` branch
- Monitor logs: `railway logs --tail`

**Vercel Deployment**:
- Frontend: https://trade-oracle-lac.vercel.app
- Auto-deploys on push to `main` branch
- Deploy from `frontend/` subdirectory

---

## After Deployment

Once both blockers are fixed and iron condor is tested:

### Week 1: Validation Phase
1. Paper trade 5-10 iron condors during market hours
2. Monitor Railway logs for any errors
3. Verify P&L calculations match Alpaca dashboard
4. Document actual win rate vs theoretical 70-80%

### Week 2-3: Frontend UI (Optional)
1. Create `IronCondorCard.tsx` with 4-leg visualization
2. Add iron condor metrics to dashboard
3. Update README.md with iron condor strategy section

### Month 2: Additional Strategies
1. Earnings Straddle strategy
2. Strategy comparison dashboard
3. Backtesting with real 0DTE data

---

## Quick Commands

```bash
# Check Railway backend health
curl https://trade-oracle-production.up.railway.app/health

# Check iron condor strategy health
curl https://trade-oracle-production.up.railway.app/api/iron-condor/health

# Check if within entry window
curl https://trade-oracle-production.up.railway.app/api/iron-condor/should-enter

# View Railway logs
railway logs --tail

# View git status
git status

# View recent commits
git log --oneline -5
```

---

**Start Here**: Follow Step 1 (Fix Vercel env vars) and Step 2 (Apply migration) sequentially. Then test during market hours.

**Estimated Time**: ~20 minutes for fixes + 10 minutes for testing = 30 minutes total to production readiness.

---

**Last Updated**: November 5, 2025
**System Version**: 2.0.0 (IV Mean Reversion + 0DTE Iron Condor)
**Deployment Status**: 75% Ready (2 critical fixes remaining)

