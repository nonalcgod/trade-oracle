# Tonight's Action Plan - Fix Critical Issues

**Time Required**: ~1 hour
**Deadline**: Before tomorrow 9:30am ET market open

---

## 🔴 CRITICAL ISSUE FOUND

Your optimized CLAUDE.md says momentum scalping is "✅ Production-Ready" but it's actually **NOT deployed to Railway**!

**Evidence**:
- Railway API returns 404 for `/api/momentum-scalping/health`
- Production `/` endpoint lists only 2 strategies (missing Momentum Scalping)
- Files `gamma_walls.py` and `unusual_activity.py` are untracked in git

**Impact**: Frontend ScalperPro page will fail, can't test momentum strategy tomorrow

---

## ⚡ Quick Fix (Copy/Paste These Commands)

### Step 1: Verify What's Missing (2 minutes)

```bash
cd /Users/joshuajames/Projects/trade-oracle

# Check untracked files
git status

# Expected output should show:
# backend/utils/gamma_walls.py
# backend/utils/unusual_activity.py
```

### Step 2: Add Files to Git (5 minutes)

```bash
# Add momentum scalping utilities
git add backend/utils/gamma_walls.py
git add backend/utils/unusual_activity.py

# Add optimized CLAUDE.md
git add CLAUDE.md

# Add the checklists we just created
git add PRE_LAUNCH_CHECKLIST.md
git add CLAUDE_MD_OPTIMIZATION_SUMMARY.md
git add CODEBASE_ANALYSIS.md
git add TONIGHT_ACTION_PLAN.md

# Verify files staged
git status
# Should show 7 files ready to commit
```

### Step 3: Commit with Descriptive Message (2 minutes)

```bash
git commit -m "DEPLOYMENT: Add momentum scalping + optimize CLAUDE.md

CRITICAL FIX: Deploy momentum scalping to production
- backend/utils/gamma_walls.py: Gamma wall detection
- backend/utils/unusual_activity.py: Options flow analysis
- Enables /api/momentum-scalping/* endpoints

OPTIMIZATION: CLAUDE.md streamlined
- 867 lines → 420 lines (-51% reduction)
- Fixed inaccuracy: Listed 3 strategies, only 2 deployed
- Added service table showing 7 services with LOC
- Added momentum scalping details (6-condition system)
- Removed 288 lines of historical debugging logs
- Improved scanability with tables and emoji indicators

DOCUMENTATION: Pre-launch validation
- PRE_LAUNCH_CHECKLIST.md: Comprehensive audit of Railway, GitHub, DB
- TONIGHT_ACTION_PLAN.md: Quick-fix guide
- CLAUDE_MD_OPTIMIZATION_SUMMARY.md: Optimization report
- CODEBASE_ANALYSIS.md: 25KB deep dive (9,054 LOC analysis)

Momentum Scalping Features:
- 6-condition entry validation (EMA, RSI, volume, VWAP, RS, time)
- Entry window: 9:31-11:30am ET (lunch cutoff)
- Exit: 25%/50% profit, -50% stop, 11:30am force close
- Discipline: Max 4 trades/day, 2-loss rule
- Advanced: Gamma walls + unusual activity detection

Status: Backend deployed, needs 1 week validation before live use

Testing Plan: Start with IV Mean Reversion tomorrow (proven strategy),
add momentum scalping after 1 week of monitoring

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 4: Push to GitHub (Triggers Railway Deploy) (2 minutes)

```bash
git push origin main

# Expected output:
# Enumerating objects: X, done.
# Counting objects: 100% (X/X), done.
# ...
# To https://github.com/yourusername/trade-oracle.git
#    107ee46..XXXXXXX  main -> main
```

### Step 5: Wait for Railway Build (10 minutes)

Railway will automatically detect the push and start building:

1. Open https://railway.app/ in browser
2. Click on "trade-oracle-production" project
3. Watch build logs (should see "Building..." then "Deployed")
4. Wait for status to show green checkmark

**Or check via terminal**:
```bash
# Check every minute until health returns 200
while true; do
  echo "Checking Railway..."
  curl -s https://trade-oracle-production.up.railway.app/health | python -m json.tool
  echo "\n---\n"
  sleep 60
done
```

### Step 6: Verify Momentum Scalping Deployed (5 minutes)

```bash
# Should return 200 OK (not 404)
curl https://trade-oracle-production.up.railway.app/api/momentum-scalping/health

# Should list 3 strategies now (not 2)
curl https://trade-oracle-production.up.railway.app/ | python -m json.tool

# Check docs page (should see momentum-scalping endpoints)
open https://trade-oracle-production.up.railway.app/docs
```

### Step 7: Verify Frontend (2 minutes)

```bash
# Open frontend
open https://trade-oracle-lac.vercel.app/scalper-pro

# Should load without errors now
# Check browser console (F12) - no 404 errors expected
```

---

## ✅ Success Criteria

After completing these steps, you should see:

1. **Git Status**: Clean working directory (no untracked files for momentum)
2. **Railway Production**:
   - `/` lists "0DTE Momentum Scalping" in strategies
   - `/api/momentum-scalping/health` returns 200 OK
   - Docs show momentum-scalping endpoints
3. **Frontend**: ScalperPro page loads without 404 errors
4. **CLAUDE.md**: Accurate (shows momentum as deployed)

---

## 🚨 If Something Goes Wrong

### Railway Build Fails

**Check logs**:
```bash
# Look for error in Railway dashboard
# Common issues:
# - Missing dependencies in requirements
# - Syntax errors in Python files
# - Import errors
```

**Fix**:
```bash
# If build fails, check Railway logs for specific error
# Fix the issue locally
# Commit and push again
git add .
git commit -m "FIX: [describe the fix]"
git push origin main
```

### Health Check Still Returns 404

**Debug**:
```bash
# Check if router is registered in main.py
grep "momentum_scalping" backend/main.py

# Should see:
# from api import ... momentum_scalping
# app.include_router(momentum_scalping.router)
```

**Fix**:
If missing, add to `backend/main.py`:
```python
from api import data, strategies, risk, execution, testing, iron_condor, momentum_scalping

app.include_router(momentum_scalping.router)
```

### Frontend Still Shows Errors

**Clear cache**:
```bash
# Hard refresh browser
# Chrome/Firefox: Ctrl+Shift+R (Cmd+Shift+R on Mac)
# Or clear browser cache
```

---

## 📊 Post-Fix Validation

Once deployed, run this validation suite:

```bash
# Save this as validate_deployment.sh
#!/bin/bash

echo "🔍 Validating Trade Oracle Deployment\n"

echo "1. Health Check:"
curl -s https://trade-oracle-production.up.railway.app/health | python -m json.tool
echo "\n"

echo "2. Strategy List (should show 3):"
curl -s https://trade-oracle-production.up.railway.app/ | python -m json.tool | grep -A 5 "strategies"
echo "\n"

echo "3. Risk Limits:"
curl -s https://trade-oracle-production.up.railway.app/api/risk/limits | python -m json.tool
echo "\n"

echo "4. Momentum Scalping Health:"
curl -s https://trade-oracle-production.up.railway.app/api/momentum-scalping/health | python -m json.tool
echo "\n"

echo "5. Iron Condor Health:"
curl -s https://trade-oracle-production.up.railway.app/api/iron-condor/health | python -m json.tool
echo "\n"

echo "✅ Validation complete!"
```

**Run it**:
```bash
chmod +x validate_deployment.sh
./validate_deployment.sh
```

---

## 🎯 Tomorrow Morning Prep (After Deploy Succeeds)

Once momentum scalping is deployed, you have 3 strategy options:

### Option 1: Conservative (✅ RECOMMENDED)
**Test IV Mean Reversion ONLY**
- Proven strategy (Nov 5 paper trade successful)
- Single-leg execution (lowest complexity)
- Exit logic validated
- Start time: 9:30am-11:00am ET

### Option 2: Moderate (⚠️ RISKY)
**Test IV Mean Reversion + Iron Condor**
- Add iron condor testing (untested multi-leg)
- Entry window: 9:31-9:45am ET only
- Monitor closely for exit issues
- Higher complexity, higher risk

### Option 3: Aggressive (🔴 NOT RECOMMENDED)
**Test All 3 Strategies**
- Add momentum scalping (just deployed, 6 conditions)
- Entry window: 9:31-11:30am ET
- Most complex strategy, highest bug risk
- Needs 1 week validation minimum

**My Recommendation**: **Option 1 - Conservative**

Test IV Mean Reversion for 2 weeks, then add iron condor, then momentum scalping. This validates the core system before adding complexity.

---

## 📋 Pre-Market Checklist (Tomorrow 8:00am ET)

Before market opens at 9:30am ET:

```bash
# 1. Verify Railway health
curl https://trade-oracle-production.up.railway.app/health

# 2. Check Alpaca paper account
# Login to https://alpaca.markets/
# Verify balance and paper mode enabled

# 3. Check open positions (should be empty)
# Query Supabase: SELECT * FROM positions WHERE status='OPEN'

# 4. Check VIX
# If VIX < 15, consider skipping IV Mean Reversion today
# (low volatility environment = poor IV signals)

# 5. Review economic calendar
# Avoid trading on FOMC, CPI, NFP announcement days
# High volatility = unpredictable option pricing

# 6. Position monitor logs
# Check Railway logs for "Position monitor started"
# Verify no errors in startup
```

---

## 🤝 Need Help?

If you run into issues:

1. **Check Railway Logs**: Railway dashboard → Deployments → Latest → Logs
2. **Check GitHub Actions**: If you have CI/CD set up
3. **Verify Environment Variables**: Railway dashboard → Variables (all set?)
4. **Test Locally**: `cd backend && python main.py` (does it start?)

---

**Time to Complete**: ~30 minutes (excluding 10-minute Railway build wait)

**Status**: Ready to execute

**Next Step**: Run Step 1 (verify untracked files)
