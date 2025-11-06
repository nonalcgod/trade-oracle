# Next Session Prompt - Trade Oracle Production Hardening

**Session Context**: Railway Deployment Fixes + Frontend Error Handling + Production Readiness
**Previous Session**: Completed CRITICAL_BUGS_FIX_PLAN.md with 8 backend bug fixes
**Ready for Implementation**: All research complete, context loaded from Context7 MCP

---

## Overview

You are continuing work on the Trade Oracle project - a production-ready multi-strategy options trading system (0DTE Iron Condor + IV Mean Reversion) deployed on Railway (backend) and Vercel (frontend).

**Current Status**: 75% production ready with 2 critical blockers resolved (Vercel env vars, DB migration). Ready for final production hardening phase.

**Your Tasks** (from previous session's explicit user confirmation):
1. ✅ **COMPLETE**: Create detailed fix plan for 8 critical backend bugs → `CRITICAL_BUGS_FIX_PLAN.md` (8-hour implementation guide)
2. ⏳ **IN PROGRESS**: Generate Railway deployment fixes as PR
3. ⏳ **IN PROGRESS**: Write frontend error boundary + ESLint config
4. ⏳ **IN PROGRESS**: Create production readiness checklist

---

## Task 1: Railway Deployment Fixes as PR

### Context from Comprehensive Audit

The Railway deployment has 5 critical configuration issues (identified in parallel audit, commit history available):

**Critical Issue #1: Missing Keep-Alive Timeout**
- **Problem**: No `--timeout-keep-alive` flag in Dockerfile CMD
- **Impact**: Railway proxy closes connections after 60s, causing 502 errors for long-running iron condor builds
- **Fix Required**: Add `--timeout-keep-alive 65` to Uvicorn command

**Critical Issue #2: Healthcheck Timeout Too Short**
- **Problem**: `railway.json` sets `healthcheckTimeout: 60` seconds
- **Impact**: Iron condor strategy initialization (option chain fetch + delta calculations) takes 90-120 seconds during market volatility
- **Fix Required**: Increase to 300 seconds

**Critical Issue #3: Deprecated Lifecycle Events**
- **Problem**: Using deprecated FastAPI `@app.on_event("startup")` pattern
- **Impact**: Will break in FastAPI 0.116.0+ (scheduled June 2025)
- **Fix Required**: Migrate to `lifespan` context manager

**Critical Issue #4: Supabase Version Drift**
- **Problem**: Using `supabase==2.15.1` in Dockerfile, but `requirements.txt` has unpinned version
- **Impact**: Local development uses different version than production
- **Fix Required**: Pin to proven stable version across both files

**Critical Issue #5: Testing Risk Limits in Production**
- **Problem**: `backend/api/risk.py` lines 58-59 have testing limits (5% risk, 10% position size)
- **Impact**: Violates paper trading safety guarantees, enables oversized positions
- **Fix Required**: Revert to production values (2% risk, 5% position size)

### Research from Context7 MCP - Railway Best Practices

**Railway Healthcheck Configuration** (railway.json):
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Deployment Lifecycle Management**:
- `drainingSeconds`: Time between SIGTERM and SIGKILL (60s recommended)
- `overlapSeconds`: Zero-downtime deployment overlap (30-60s)

**Dockerfile Best Practices for FastAPI**:
- Use multi-stage builds for smaller image sizes
- Pin exact Python version (e.g., `python:3.11.10-slim`)
- Use `--no-cache-dir` with pip to reduce image size
- Bind to `::` (IPv6) or `0.0.0.0` for Railway networking

### Research from Web Search - FastAPI Uvicorn Production (2025)

**Critical Production Settings** (September 2025 article):

1. **Timeout Keep-Alive**: `--timeout-keep-alive 65`
   - Closes Keep-Alive connections if no new data within 65 seconds
   - **Railway requirement**: Must be > 60s to prevent proxy timeouts
   - Default is 5s (too aggressive for production)

2. **Graceful Shutdown**: `--timeout-graceful-shutdown 300`
   - Allows in-flight requests to complete before SIGKILL
   - Critical for multi-leg order execution (don't kill mid-trade!)

3. **Concurrency Limits**: `--limit-concurrency 1000`
   - Maximum concurrent connections before 503 responses
   - Railway free tier: 100-200 concurrent connections realistic

4. **Backlog**: `--backlog 2048`
   - Connection queue size for OS socket
   - Higher values prevent connection drops during traffic spikes

5. **Worker Recycling**: `--limit-max-requests 10000`
   - Restart worker after N requests to prevent memory leaks
   - Optional but recommended for long-running deployments

**Recommended Production CMD**:
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}", \
     "--timeout-keep-alive", "65", \
     "--timeout-graceful-shutdown", "300", \
     "--limit-concurrency", "1000", \
     "--backlog", "2048"]
```

**Multi-Worker Configuration** (for scaling):
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --timeout 300 \
  --keep-alive 65 \
  --graceful-timeout 300
```

### Your Implementation Instructions

**Step 1: Read Current Files**
```bash
# Files to analyze
- /Users/joshuajames/Projects/trade-oracle/Dockerfile
- /Users/joshuajames/Projects/trade-oracle/railway.json
- /Users/joshuajames/Projects/trade-oracle/backend/requirements.txt
- /Users/joshuajames/Projects/trade-oracle/backend/requirements-railway.txt
- /Users/joshuajames/Projects/trade-oracle/backend/api/risk.py
- /Users/joshuajames/Projects/trade-oracle/backend/main.py
```

**Step 2: Create Git Branch**
```bash
cd /Users/joshuajames/Projects/trade-oracle
git checkout -b fix/railway-production-hardening
```

**Step 3: Apply Fixes**

**Fix #1: Dockerfile CMD** (add keep-alive timeout)
```dockerfile
# BEFORE (line ~25):
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# AFTER:
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} \
     --timeout-keep-alive 65 \
     --timeout-graceful-shutdown 300 \
     --limit-concurrency 1000 \
     --backlog 2048"]
```

**Fix #2: railway.json** (healthcheck timeout)
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "drainingSeconds": 60,
    "overlapSeconds": 30
  }
}
```

**Fix #3: main.py** (lifespan context manager)
```python
# BEFORE (deprecated pattern):
@app.on_event("startup")
async def startup_event():
    # Start position monitor
    asyncio.create_task(monitor_positions())

# AFTER (lifespan context manager):
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    monitor_task = asyncio.create_task(monitor_positions())
    logger.info("Position monitor started")

    yield  # Application runs

    # Shutdown
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        logger.info("Position monitor stopped")

app = FastAPI(
    title="Trade Oracle API",
    version="1.0.0",
    lifespan=lifespan  # Add lifespan parameter
)
```

**Fix #4: Supabase Version Pinning**
```dockerfile
# In Dockerfile (line ~20):
# BEFORE:
supabase==2.15.1

# Verify requirements.txt also has:
supabase==2.15.1  # Add if missing
```

**Fix #5: Risk Limits Revert**
```python
# backend/api/risk.py lines 58-59
# BEFORE (TESTING MODE):
MAX_PORTFOLIO_RISK = Decimal('0.05')   # 5% max risk per trade
MAX_POSITION_SIZE = Decimal('0.10')    # 10% max position size

# AFTER (PRODUCTION MODE):
MAX_PORTFOLIO_RISK = Decimal('0.02')   # 2% max risk per trade
MAX_POSITION_SIZE = Decimal('0.05')    # 5% max position size
```

**Step 4: Create PR**
```bash
# Commit changes
git add Dockerfile railway.json backend/main.py backend/api/risk.py
git commit -m "CRITICAL: Railway production hardening fixes

- Add Uvicorn timeout-keep-alive (65s) to prevent 502 errors
- Increase healthcheck timeout (60s → 300s) for iron condor init
- Migrate to FastAPI lifespan context (deprecation warning fix)
- Pin Supabase version (2.15.1) across all requirement files
- Revert risk limits to production values (2%/5%)

Context:
- Railway proxy requires keep-alive > 60s
- Iron condor option chain fetch takes 90-120s during volatility
- FastAPI 0.116.0+ removes @app.on_event support
- Testing limits violated paper trading safety guarantees

References:
- CRITICAL_BUGS_FIX_PLAN.md (backend fixes)
- COMPREHENSIVE_AUDIT_REPORT.md (deployment issues)
- Railway docs: healthcheck best practices
- Uvicorn docs: production configuration (2025)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push branch
git push -u origin fix/railway-production-hardening

# Create PR (using GitHub CLI if available)
gh pr create \
  --title "CRITICAL: Railway Production Hardening Fixes" \
  --body "$(cat <<'EOF'
## Summary
5 critical Railway deployment fixes to prevent 502 errors, improve reliability, and ensure paper trading safety.

## Changes
- ✅ **Keep-Alive Timeout**: Added `--timeout-keep-alive 65` to Uvicorn (Railway proxy requirement)
- ✅ **Healthcheck Timeout**: Increased from 60s → 300s (iron condor initialization takes 90-120s)
- ✅ **Lifespan Migration**: Replaced deprecated `@app.on_event` with FastAPI lifespan context
- ✅ **Version Pinning**: Supabase 2.15.1 pinned across all requirement files
- ✅ **Risk Limits**: Reverted from testing (5%/10%) to production (2%/5%) values

## Impact
**Before**: 502 errors during iron condor builds, healthcheck failures, potential oversized positions
**After**: Stable connections, reliable deployments, enforced risk limits

## Testing
- [ ] Deploy to Railway staging
- [ ] Verify `/health` endpoint responds within 300s
- [ ] Test iron condor build during market hours (9:31-9:45am ET)
- [ ] Confirm no 502 errors in Railway logs
- [ ] Validate risk limits reject positions > 2% portfolio risk

## References
- CRITICAL_BUGS_FIX_PLAN.md
- COMPREHENSIVE_AUDIT_REPORT.md
- Railway docs: healthcheck configuration
- Uvicorn production guide (September 2025)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" \
  --base main \
  --head fix/railway-production-hardening
```

**Step 5: Verification**
```bash
# After merging PR and Railway deploys:

# 1. Check Railway logs for new flags
railway logs --tail | grep "timeout-keep-alive"
# Expected: "Uvicorn running on ... --timeout-keep-alive 65"

# 2. Test healthcheck
time curl https://trade-oracle-production.up.railway.app/health
# Expected: < 5 seconds response, no timeout

# 3. Test iron condor build (during market hours)
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "expiration": "2025-11-06", "quantity": 1}'
# Expected: Success response with real credits (not placeholders)

# 4. Verify risk limits
# Check risk.py in Railway deployment
railway run cat backend/api/risk.py | grep MAX_PORTFOLIO_RISK
# Expected: Decimal('0.02')  # NOT 0.05
```

---

## Task 2: Frontend Error Boundary + ESLint Config

### Context from Comprehensive Audit

The frontend has critical production gaps:

**Critical Issue #1: No Error Boundaries**
- React errors crash entire application (white screen of death)
- User loses all state and data
- No graceful recovery mechanism

**Critical Issue #2: ESLint Not Configured**
- Using default Vite template ESLint (minimal rules)
- No TypeScript type checking in lint
- No React hooks rules
- No accessibility checks

**Critical Issue #3: Zero Test Coverage**
- No `*.test.tsx` files found in project
- No error handling tests
- No integration tests for critical paths

### Research from Context7 MCP - React Error Boundary

**Package**: `react-error-boundary` (Trust Score: 9.7, 25 code snippets)

**Key Patterns**:

1. **Static Fallback** (Simple errors):
```tsx
import { ErrorBoundary } from "react-error-boundary";

<ErrorBoundary fallback={<div>Something went wrong</div>}>
  <App />
</ErrorBoundary>
```

2. **FallbackComponent** (Complex UI):
```tsx
function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div role="alert" style={{ padding: "20px", border: "1px solid red" }}>
      <h2>Application Error</h2>
      <details style={{ whiteSpace: "pre-wrap" }}>
        <summary>Error Details</summary>
        {error.message}
      </details>
      <button onClick={resetErrorBoundary}>Try Again</button>
    </div>
  );
}

<ErrorBoundary
  FallbackComponent={ErrorFallback}
  onError={(error, info) => {
    console.error("Error:", error);
    // Log to external service (e.g., Sentry)
  }}
  onReset={() => {
    window.location.href = "/";
  }}
>
  <App />
</ErrorBoundary>
```

3. **Nested Boundaries** (Granular recovery):
```tsx
function App() {
  return (
    <ErrorBoundary fallback={<div>App-level error</div>}>
      <Header />

      <ErrorBoundary fallback={<div>Dashboard unavailable</div>}>
        <Dashboard />
      </ErrorBoundary>

      <ErrorBoundary fallback={<div>Trades unavailable</div>}>
        <TradeHistory />
      </ErrorBoundary>

      <Footer />
    </ErrorBoundary>
  );
}
```

4. **useErrorBoundary Hook** (Async errors):
```tsx
import { useErrorBoundary } from "react-error-boundary";

function DataComponent() {
  const { showBoundary } = useErrorBoundary();

  useEffect(() => {
    fetch("/api/data")
      .then(res => res.json())
      .then(setData)
      .catch(error => {
        // Forward to error boundary
        showBoundary(error);
      });
  }, [showBoundary]);

  return <div>{data}</div>;
}
```

5. **TypeScript with Custom Error Types**:
```tsx
interface ApiError extends Error {
  statusCode: number;
  endpoint: string;
}

function ApiErrorFallback({ error }: FallbackProps) {
  const apiError = error as ApiError;

  return (
    <div>
      <h2>API Error ({apiError.statusCode})</h2>
      <p>Failed: {apiError.endpoint}</p>
    </div>
  );
}
```

### Research from Web Search - ESLint Config (2025)

**Key Changes in 2025**:
- ESLint v9 introduced flat config format (`eslint.config.js` replaces `.eslintrc`)
- Legacy format no longer enabled by default
- Vite React template includes pre-configured ESLint
- `eslint-plugin-prettier` is no longer needed (use `eslint-config-prettier` only)

**Production-Level Config** (TypeScript + React + Vite):
```javascript
// eslint.config.js
import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import react from 'eslint-plugin-react';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'build', 'coverage'] },
  {
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
      ...tseslint.configs.stylisticTypeChecked,
      react.configs.flat.recommended,
      react.configs.flat['jsx-runtime'],
      prettier
    ],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2024,
      globals: globals.browser,
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      'jsx-a11y': jsxA11y,
    },
    rules: {
      // React Hooks
      ...reactHooks.configs.recommended.rules,

      // React Refresh (Vite HMR)
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      // TypeScript
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_'
      }],
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/explicit-function-return-type': 'off',

      // React
      'react/prop-types': 'off', // Using TypeScript
      'react/react-in-jsx-scope': 'off', // Not needed in React 17+

      // Accessibility
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/aria-props': 'error',
      'jsx-a11y/aria-proptypes': 'error',
      'jsx-a11y/aria-unsupported-elements': 'error',
      'jsx-a11y/role-has-required-aria-props': 'error',
      'jsx-a11y/role-supports-aria-props': 'error',
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
);
```

### Your Implementation Instructions

**Step 1: Install Dependencies**
```bash
cd /Users/joshuajames/Projects/trade-oracle/frontend

# Install error boundary
npm install react-error-boundary

# Install ESLint plugins (if not already present)
npm install -D \
  @eslint/js \
  typescript-eslint \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  eslint-plugin-react-refresh \
  eslint-plugin-jsx-a11y \
  eslint-config-prettier
```

**Step 2: Create Error Boundary Component**

Create `frontend/src/components/ErrorBoundary.tsx` with Trade Oracle styling (cream background, teal/rose accents, rounded corners).

**Step 3: Update App.tsx with Nested Boundaries**

Wrap Dashboard, TradeHistory, and Positions with separate boundaries for granular error isolation.

**Step 4: Update main.tsx with Root Boundary**

Wrap entire app with top-level error boundary.

**Step 5: Create/Update ESLint Config**

Replace `frontend/eslint.config.js` with production-level configuration.

**Step 6: Add NPM Scripts**

Update `frontend/package.json`:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "type-check": "tsc --noEmit"
  }
}
```

**Step 7: Commit Changes**
```bash
cd /Users/joshuajames/Projects/trade-oracle

git add frontend/
git commit -m "FEATURE: Add error boundaries and production ESLint config

Frontend Error Handling:
- Install react-error-boundary (Trust Score 9.7)
- Create ErrorBoundaryWrapper component with Trade Oracle styling
- Add app-level and feature-level error boundaries
- Implement fallback UI with retry/home actions
- Add error logging hooks for future Sentry integration

ESLint Configuration (2025):
- Migrate to flat config format (eslint.config.js)
- Enable TypeScript type-checked rules
- Add React hooks linting
- Add accessibility checks (jsx-a11y)
- Configure Prettier integration (no conflicts)
- Add lint:fix and type-check scripts

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

**Step 8: Verification**
```bash
# 1. Run ESLint
cd frontend
npm run lint
# Expected: No errors (or only warnings)

# 2. Run type check
npm run type-check
# Expected: No TypeScript errors

# 3. Deploy to Vercel
vercel --prod
# Expected: Successful deployment, error boundaries active
```

---

## Task 3: Production Readiness Checklist

Create comprehensive checklist document covering:

1. **Security** (CRITICAL): Certificates, secrets, vulnerability scans
2. **Monitoring & Observability** (CRITICAL): Error tracking, alerting, log aggregation
3. **Infrastructure** (HIGH): Resources, database, networking, auto-scaling
4. **Reliability** (HIGH): Health checks, graceful degradation, DR planning
5. **Code Quality** (MEDIUM): Testing, linting, documentation
6. **Performance** (MEDIUM): Load testing, optimization, caching
7. **Compliance & Safety** (CRITICAL): Paper trading enforcement, audit logging
8. **Deployment Validation** (PRE-FLIGHT): Pre/post-deployment checklists
9. **Trade Oracle Specific**: Strategy validation, position monitoring, risk management
10. **Current Status**: Completion tracking with action items

Create `PRODUCTION_READINESS_CHECKLIST.md` with 2025 best practices from Port.io, GoReplay, and Spaceo.

---

## Summary

All three tasks are ready to implement with:
- ✅ Complete research from Context7 MCP and web sources
- ✅ Step-by-step implementation instructions
- ✅ Code examples and configuration snippets
- ✅ Verification steps for each task
- ✅ Git workflow (branch, commit, PR)

**Estimated Time**: 6-8 hours total
- Task 1 (Railway): 2-3 hours
- Task 2 (Frontend): 2-3 hours
- Task 3 (Checklist): 30 minutes

**Start with**: Task 1 (Railway fixes) as it's critical for production stability.

---

**Last Updated**: 2025-11-05
**Session ID**: Production Hardening Phase
**Previous Work**: CRITICAL_BUGS_FIX_PLAN.md (8 backend fixes documented)
