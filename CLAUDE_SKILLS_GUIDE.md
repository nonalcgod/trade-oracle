# Claude Skills for Trade Oracle

**Research Date**: November 6, 2025
**Source**: YouTube transcript analysis + Trade Oracle codebase deep dive

## What Are Claude Skills?

Claude Skills are **modular, task-specific instructions** that Claude triggers only when needed. Think of them as mini-programs that teach Claude how to execute your workflows with precision.

**Key Differences from Other Tools:**
- **vs. Custom Instructions**: Skills are task-specific, not global
- **vs. Projects**: Skills can be used across projects and chained together
- **vs. MCPs**: Skills provide instructions for actions, MCPs provide data access
- **File Format**: Markdown files with step-by-step instructions and reference materials

## Executive Summary: Top 3 Opportunities for Trade Oracle

### 1. End-to-End Trade Tester (HIGH IMPACT)
**Time Savings**: 10-15 minutes → 30 seconds per test cycle
**Accuracy**: 90% reduction in manual errors

**What it does**: Orchestrates complete trade lifecycle testing (signal → risk → execute → verify) for both IV Mean Reversion and 0DTE Iron Condor strategies with intelligent error diagnosis.

**Why it matters**: Currently testing requires running bash scripts, manually parsing JSON, checking multiple endpoints, and verifying database state. A skill automates all of this with intelligent error handling.

### 2. Performance Analyzer & Optimizer (HIGH IMPACT)
**Time Savings**: 2-3 hours → 5 minutes
**Cost Impact**: Keeps you in free tier by identifying optimizations

**What it does**: Analyzes backend performance metrics, identifies bottlenecks (missing indexes, inefficient queries, synchronous API calls), and generates specific code fixes with before/after examples.

**Why it matters**: You have extensive performance infrastructure (Redis caching, database indexes, async clients) but no unified way to analyze what's slow and prioritize optimizations.

### 3. Weekly Strategy Reflection Generator (MEDIUM-HIGH IMPACT)
**Time Savings**: 30-60 minutes → 2 minutes
**Decision Quality**: Data-driven insights vs. gut feeling

**What it does**: Automates the weekly reflection process (backend/cron/reflection.py) by fetching trades, calculating advanced metrics (Sharpe ratio, max drawdown, Kelly criterion), and using Claude AI to generate actionable recommendations.

**Why it matters**: The skeleton exists but needs enhancement. A skill would provide systematic performance analysis to improve trading decisions.

---

## Complete Skills Breakdown

### SKILL 1: End-to-End Trade Tester

**File**: `.claude/skills/end-to-end-trade-tester.md`

**What it does:**
Orchestrates complete trade lifecycle testing for both IV Mean Reversion and 0DTE Iron Condor strategies with intelligent error handling and verification.

**Steps:**
1. **Pre-flight checks**: Backend health, strategy initialization, entry window validation, risk limits
2. **Generate signal**: Create realistic OptionTick (IV) or iron condor signal (0DTE)
3. **Risk validation**: Fetch portfolio, submit to risk manager, diagnose rejections
4. **Execute trade**: POST to single-leg or multi-leg execution endpoint
5. **Verify database**: Check positions and trades tables for new records
6. **Monitor exit** (optional): Poll exit conditions, display P&L progress
7. **Cleanup** (optional): Force close position after test

**Parameters:**
- `strategy`: "iv_mean_reversion" or "iron_condor"
- `symbol`: Option symbol or underlying
- `quantity`: Number of contracts (1-10)
- `monitor`: Watch position until exit
- `cleanup`: Force close after test
- `mock_entry_window`: Bypass 9:31-9:45am check

**Reference Materials:**
- `scripts/test_iv_trade.sh`
- `scripts/test_iron_condor.sh`
- `backend/api/risk.py` (risk limits)
- `backend/monitoring/position_monitor.py` (exit conditions)

**Integration Points:**
- Bash tool for API calls
- Read tool for JSON parsing
- context7 MCP for Alpaca docs if errors occur
- Chain to "performance-analyzer" if API slow

**Expected Output:**
```
✓ Backend healthy
✓ Strategy initialized
✓ Signal generated: BUY SPY $600C (IV rank 0.25)
✓ Risk approved: 3 contracts
✓ Trade executed: Order ID abc123
✓ Position verified: ID 42 in database
✓ Exit conditions: 50% profit target, 75% stop loss

Test complete: 1m 15s
```

**Impact**: HIGH - 10-15 min → 30 sec, 90% error reduction

---

### SKILL 2: Performance Analyzer & Optimizer

**File**: `.claude/skills/performance-analyzer.md`

**What it does:**
Analyzes backend performance metrics, identifies bottlenecks, and generates specific optimization recommendations with code examples.

**Steps:**
1. **Baseline audit**: Measure /health, /portfolio, /signal, /iron-condor/build response times
2. **Database analysis**: Find queries without indexes, check if performance_indexes.sql applied
3. **Caching scan**: Identify endpoints that don't change frequently, check if cache.py used
4. **Async optimization**: Find synchronous Alpaca calls, blocking I/O, sequential operations
5. **Frontend polling**: Count polling endpoints, check if Supabase Real-Time enabled
6. **Generate report**: Rank bottlenecks by impact, provide code fixes, estimate speedup

**Parameters:**
- `focus_area`: "database" | "caching" | "async" | "frontend" | "all"
- `include_code_examples`: Generate full code snippets
- `deployment_env`: "local" | "production"

**Reference Materials:**
- `SCALING_PLAN.md` (Phase 1, 2, 3 optimizations)
- `backend/performance_indexes.sql`
- `backend/utils/cache.py`
- `backend/realtime_triggers.sql`

**Integration Points:**
- Bash tool to measure latency
- Grep to scan for anti-patterns
- Read to check if optimization files exist
- context7 MCP for FastAPI/Supabase best practices
- Chain to "database-migration-applier" if indexes missing

**Expected Output:**
```
CRITICAL: IV rank calculation (500ms)
├─ Missing index on option_ticks(symbol, timestamp)
├─ Fix: Apply backend/performance_indexes.sql
├─ Impact: 500ms → 50ms (10x faster)
└─ Effort: 2 minutes

HIGH: Portfolio polling (150 requests/min)
├─ Frontend polls every 5 seconds
├─ Fix: Implement Supabase Real-Time subscriptions
├─ Impact: 90% reduction in API calls
└─ Effort: 30 minutes
```

**Impact**: HIGH - 2-3 hours → 5 min, identifies free tier optimizations

---

### SKILL 3: Weekly Strategy Reflection Generator

**File**: `.claude/skills/weekly-strategy-reflection.md`

**What it does:**
Automates weekly trading performance analysis with advanced metrics and Claude AI insights.

**Steps:**
1. **Fetch trade data**: Query /api/execution/trades for past 7 days, separate by strategy
2. **Calculate metrics**: Win rate, Profit Factor, Sharpe Ratio, Max Drawdown, streaks
3. **Identify patterns**: Group by day/time/IV/DTE, find best/worst conditions
4. **Risk audit**: Check if trades violated limits, count circuit breaker triggers
5. **Claude analysis**: Use Anthropic API to analyze metrics and generate recommendations
6. **Save reflection**: Insert into Supabase reflections table
7. **Action items**: Extract specific TODOs for next week

**Parameters:**
- `lookback_days`: Number of days to analyze (default: 7)
- `include_comparison`: Compare to previous week
- `strategies`: Array of strategies to analyze
- `min_trades`: Minimum trades required

**Reference Materials:**
- `backend/cron/reflection.py` (skeleton)
- Backtest targets: 75% win rate, Sharpe >1.2
- `backend/api/risk.py` (circuit breakers)
- `0DTE_IRON_CONDOR_EXPERT_GUIDE.md` (70-80% theoretical win rate)

**Integration Points:**
- Bash tool to query API
- Anthropic API for analysis
- context7 MCP for options trading best practices
- Write to Supabase reflections table

**Expected Output:**
```markdown
# Weekly Trading Reflection - Week of Nov 4-10, 2025

## Performance Summary
- Total Trades: 12
- Win Rate: 66.7% (8W / 4L)
- Net P&L: $1,245.00
- Sharpe Ratio: 1.05
- Max Drawdown: -$380.00 (3.8%)

## Strategy Breakdown
### IV Mean Reversion (8 trades)
- Win Rate: 75.0% ✓ (meets target)
- Avg Win: $180, Avg Loss: $95

### Iron Condor (4 trades)
- Win Rate: 50.0% ⚠️ (below 70% target)
- Issue: 2 losses from breach (underlying moved >2%)
- Recommendation: Widen strikes to 0.20 delta

## Claude Analysis
[AI-generated insights on patterns and improvements]

## Action Items for Next Week
1. [ ] Widen iron condor strikes (0.15 → 0.20 delta)
2. [ ] Avoid IV trades when VIX < 15
3. [ ] Review exit timing (avg hold: 18 days vs. 21 DTE)
```

**Impact**: MEDIUM-HIGH - 30-60 min → 2 min, data-driven decisions

---

### SKILL 4: Database Migration Applier

**File**: `.claude/skills/database-migration-applier.md`

**What it does:**
Safely applies database migrations (indexes, triggers, schema changes) with validation and rollback.

**Steps:**
1. **Pre-flight**: Check Supabase connection, verify SUPABASE_SERVICE_KEY
2. **Migration analysis**: Read .sql file, identify type, estimate impact, generate rollback
3. **Safety checks**: Check if migration already applied, validate syntax
4. **Apply**: Execute SQL via Supabase API or psql
5. **Validation**: Verify migration succeeded, measure performance improvement
6. **Record**: Insert into migrations table, update docs

**Parameters:**
- `migration_file`: Path to .sql file
- `dry_run`: Preview without executing
- `validate_only`: Check if already applied
- `environment`: "development" | "production"

**Reference Materials:**
- `backend/migrations/`
- `backend/performance_indexes.sql`
- `backend/realtime_triggers.sql`
- `APPLY_DATABASE_MIGRATION.md`

**Expected Output:**
```
MIGRATION: backend/performance_indexes.sql

✓ Supabase connection OK
✓ No conflicting indexes

Applying:
✓ CREATE INDEX idx_option_ticks_symbol_timestamp (127ms)
✓ CREATE INDEX idx_positions_status_opened (43ms)
...

Validation:
✓ All 10 indexes created
✓ Query speedup: 487ms → 52ms (9.4x faster)
```

**Impact**: MEDIUM-HIGH - 15 min → 2 min, prevents duplicate migrations

---

### SKILL 5: Deployment Diagnostics

**File**: `.claude/skills/deployment-diagnostics.md`

**What it does:**
Diagnoses Railway/Vercel deployment issues with intelligent troubleshooting and fix suggestions.

**Steps:**
1. **Status check**: Curl Railway and Vercel, parse response codes
2. **Railway diagnostics**: Check Uvicorn config, fetch logs, parse errors
3. **Vercel diagnostics**: Check VITE_API_URL, test API calls, check build logs
4. **Env var audit**: Compare .env.example with deployed vars
5. **Dependency conflicts**: Check requirements.txt, Python version, package.json
6. **Fix recommendations**: Rank by priority, provide code changes, estimate time

**Parameters:**
- `service`: "backend" | "frontend" | "both"
- `include_logs`: Fetch and analyze logs
- `auto_fix`: Apply safe fixes automatically

**Reference Materials:**
- `.claude/agents/railway-deployment-expert.md`
- `Dockerfile`, `railway.json`, `vercel.json`
- `SESSION_COMPLETION_SUMMARY.md` (recent fixes)

**Expected Output:**
```
BACKEND: 502 Bad Gateway

ROOT CAUSE: Uvicorn timeout-keep-alive too low
File: Dockerfile line 24
Fix: Set --timeout-keep-alive 65

Impact: CRITICAL (site unreachable)
Time: 2 min + 3 min redeploy

FRONTEND: 200 OK
Issue: API calls failing (VITE_API_URL = localhost)
Fix: Set env var to Railway URL

Impact: HIGH (dashboard not loading)
Time: 1 min + instant redeploy
```

**Impact**: HIGH - 30-60 min → 5 min, faster root cause identification

---

### SKILL 6: Signal Generator & Validator

**File**: `.claude/skills/signal-generator-validator.md`

**What it does:**
Generates realistic market data to trigger trading signals for testing, with validation against backtest parameters.

**Steps:**
1. **Understand target**: IV rank < 30% (BUY), > 70% (SELL), or 0DTE iron condor
2. **Generate tick**: Create realistic option data with Greeks using Black-Scholes
3. **Validate signal**: POST to /api/strategies/signal, verify type matches
4. **Risk simulation**: Create portfolio state, get approval, adjust if rejected
5. **Historical check**: Compare to backtest expectations (75% win rate for IV)
6. **Batch generation** (optional): Generate N signals for stress testing

**Parameters:**
- `strategy`: "iv_buy" | "iv_sell" | "iron_condor" | "random"
- `symbol`: Option symbol or underlying
- `target_iv_rank`: Float 0-1 for IV strategy
- `dte`: Days to expiration (30-45 for IV, 0 for iron condor)
- `batch_count`: Number of signals
- `output_file`: Save to JSON

**Reference Materials:**
- `backend/api/strategies.py` (IV_HIGH=0.70, IV_LOW=0.30)
- `backend/utils/greeks.py` (Black-Scholes)
- `backend/strategies/iron_condor.py` (delta selection)

**Expected Output:**
```
GENERATED SIGNAL: IV Mean Reversion BUY

Option: SPY251219C00600000
- Underlying: $597.50, Strike: $600
- DTE: 43, IV: 18.5% (rank 0.25)
- Delta: 0.48, Mid: $12.00

Signal:
- Type: BUY
- Entry: $12.00, Stop: $6.00, Target: $24.00
- Reasoning: "IV rank 0.25 < 0.30"

Risk: ✓ Approved (3 contracts, $1,800 max loss)

Ready for execution
```

**Impact**: MEDIUM - 10 min → 30 sec, enables systematic testing

---

### SKILL 7: Production Readiness Checker

**File**: `.claude/skills/production-readiness-checker.md`

**What it does:**
Comprehensive pre-deployment checklist validator ensuring all systems are production-ready.

**Steps:**
1. **Security audit**: No secrets committed, testing endpoints protected, paper trading mode
2. **Risk validation**: Limits at production values, circuit breakers functional
3. **Database integrity**: Migrations applied, schema matches models, backups enabled
4. **Monitoring**: Position monitor running, exit conditions tested, logging structured
5. **Performance**: Measure critical endpoints, check query times, test under load
6. **Deployment**: Railway/Vercel health, env vars set, free tier limits monitored
7. **Backtest alignment**: Compare parameters, verify Kelly sizing, check exit conditions
8. **Documentation**: README up to date, API docs accessible, runbook exists

**Parameters:**
- `strict_mode`: Fail on warnings
- `skip_load_test`: Skip performance benchmarks
- `output_format`: "checklist" | "report" | "json"

**Reference Materials:**
- `backend/api/risk.py` (production values)
- `IRON_CONDOR_DEPLOYMENT_READY.md`
- `CRITICAL_BUGS_FIX_PLAN.md`

**Expected Output:**
```
TRADE ORACLE - Production Readiness Check

SECURITY: ✓ PASS
RISK MANAGEMENT: ✓ PASS
DATABASE: ⚠️ WARNING (connection pooling recommended)
MONITORING: ✓ PASS
PERFORMANCE: ✓ PASS
DEPLOYMENT: ✓ PASS
BACKTEST ALIGNMENT: ✓ PASS

OVERALL: ✓ READY FOR PRODUCTION
(1 warning, 0 critical issues)

Recommendation: Apply connection pooling before high volume.
See SCALING_PLAN.md Phase 1.1
```

**Impact**: MEDIUM-HIGH - 60 min → 5 min, catches critical issues

---

## Skill Chaining Examples

### Example 1: Full Development Cycle
```
User: "Test iron condor and optimize any slow parts"

Execution:
1. signal-generator-validator
   → Generates realistic 0DTE data

2. end-to-end-trade-tester
   → Executes trade, detects 800ms bottleneck

3. performance-analyzer
   → Identifies missing database index

4. database-migration-applier
   → Applies index, reduces to 85ms

5. end-to-end-trade-tester
   → Validates fix (230ms total)

Total: 2 minutes (vs. 45 minutes manual)
```

### Example 2: Weekly Trading Review
```
User: "Analyze this week's performance"

Execution:
1. weekly-strategy-reflection
   → Win rate 58%, below target
   → Identifies: Losses when VIX < 15

2. signal-generator-validator
   → Tests low VIX scenario
   → Signal still generated (should filter)

3. (Manual) Add VIX > 15 filter to strategy

4. production-readiness-checker
   → Validates change passes all tests

Total: 10 minutes (vs. 2 hours manual)
```

### Example 3: Deployment Troubleshooting
```
User: "Backend returning 502 errors"

Execution:
1. deployment-diagnostics
   → Detects: Healthcheck timing out
   → Root cause: Iron condor init takes 280s

2. performance-analyzer
   → Identifies: Option chain blocking startup
   → Recommends: Move to background task

3. (Manual) Refactor initialization

4. deployment-diagnostics
   → Validates: Startup now 8s

5. production-readiness-checker
   → All systems green

Total: 15 minutes (vs. 90 minutes trial-and-error)
```

---

## Implementation Guide

### Phase 1: Core Testing Skills (Week 1)
**Priority**: HIGHEST IMPACT

1. **end-to-end-trade-tester** - Automates daily testing workflows
2. **signal-generator-validator** - Enables systematic testing
3. **deployment-diagnostics** - Reduces downtime

**Steps**:
```bash
# 1. Create skills directory
mkdir -p .claude/skills

# 2. Create skill files
# Copy markdown structures from this doc into .md files

# 3. Upload to Claude
# Settings → Capabilities → Upload Skill → Upload each file

# 4. Test
# Use skill name in prompt: "Use end-to-end-trade-tester to test SPY"
```

### Phase 2: Analysis Skills (Week 2-3)

4. **performance-analyzer** - Optimizes before scaling
5. **weekly-strategy-reflection** - Automates decision-making
6. **database-migration-applier** - Safer schema evolution

### Phase 3: Production Skills (Week 4)

7. **production-readiness-checker** - Final gate before real money

---

## Security Considerations

### Critical Safety Measures

1. **Paper Trading Enforcement**
   - Skills validate ALPACA_BASE_URL = paper-api.alpaca.markets
   - Fail loudly if real trading credentials detected
   - Require explicit `--real-money` flag (not recommended)

2. **Risk Limit Validation**
   - All execution skills check risk limits before trading
   - Never bypass circuit breakers (daily loss, consecutive losses)
   - Log all risk violations for audit

3. **Position Size Caps**
   - Enforce maximum position size (10 contracts)
   - Require manual approval for large positions (>$10k)
   - Validate Kelly sizing calculation

4. **Testing Endpoint Protection**
   - /api/testing/* endpoints require auth in production
   - Never expose testing endpoints publicly
   - Add IP whitelisting for sensitive operations

5. **Secret Management**
   - Skills never log API keys or credentials
   - Use environment variables, not hardcoded values
   - Validate secrets exist before execution

6. **Audit Trail**
   - All skill executions log to database (who, what, when)
   - Include: skill name, parameters, results, execution time
   - Enable rollback for critical operations

---

## Best Practices

### From the YouTube Video

1. **Toggle Off Unused Skills**
   - Saves tokens and speeds execution
   - Prevents conflicting instructions

2. **Use Descriptive Naming**
   - "end-to-end-trade-tester" not "skill-1"
   - Version with underscores: "tester_v2"

3. **Chain Skills Intentionally**
   - Think of skills as Lego blocks
   - Compose complex workflows from simple skills

4. **Avoid Duplicate Intent**
   - Don't have overlapping skills active
   - Example: Don't use both Anthropic brand guidelines AND custom brand skill

5. **Include Reference Materials**
   - Skills can include docs, presentations, code files
   - Reference materials go in same zip file as skill markdown

### Trade Oracle Specific

1. **Start Small**: Implement top 3 skills first, validate value
2. **Measure Impact**: Track time savings before/after each skill
3. **Iterate**: Refine skill instructions based on real usage
4. **Document**: Keep this guide updated as skills evolve
5. **Share**: Skills can be shared across team members

---

## Expected Benefits

### Quantified Impact

- **Testing Time**: 90% reduction (15 min → 30 sec per test)
- **Analysis Time**: 95% reduction (2-3 hours → 5 min)
- **Deployment Debugging**: 80% reduction (60 min → 10 min)
- **Weekly Reviews**: 97% reduction (60 min → 2 min)

### Qualitative Benefits

- **Better Decisions**: Data-driven insights vs. gut feeling
- **Fewer Errors**: Systematic validation catches edge cases
- **Faster Scaling**: Performance analysis identifies bottlenecks early
- **Knowledge Persistence**: Skills encode institutional knowledge
- **Team Productivity**: New developers can use skills to learn system

---

## Next Steps

1. **Review This Document**: Understand all 7 skills and their benefits
2. **Prioritize**: Decide which skills to implement first (recommend Phase 1)
3. **Create Skill Files**: Copy markdown structures into `.claude/skills/` directory
4. **Upload to Claude**: Settings → Capabilities → Upload Skill
5. **Test Individual Skills**: Try each with real scenarios
6. **Test Skill Chaining**: Compose workflows from multiple skills
7. **Iterate**: Refine based on results
8. **Measure**: Track time savings and error reduction

---

## Questions & Answers

**Q: Can skills access my local files?**
A: Yes, skills can use Read, Grep, Bash tools to access local files.

**Q: Do skills share context with my main session?**
A: Skills see conversation history but execute independently.

**Q: Can I use skills with MCPs?**
A: Yes! Skills can trigger MCPs like context7 for additional context.

**Q: Are skills secure?**
A: Be careful with community skills (like Comet jacking). Only use trusted sources.

**Q: How do I update a skill?**
A: Create new version (name_v2.md), upload, toggle off old version.

**Q: Can skills execute trades automatically?**
A: Only if you explicitly tell them to. Default requires confirmation.

---

## Community Resources

### Finding Skills
- **GitHub**: Search for "claude-skills" repositories
- **Claude Community**: Official forums (when available)
- **Share Your Own**: Consider sharing Trade Oracle skills with trading community

### Contributing Back
If you create valuable skills for trading automation:
1. Sanitize any proprietary logic
2. Share on GitHub with clear documentation
3. Include security warnings for trading automation
4. Tag with "options-trading", "algorithmic-trading"

---

## Conclusion

Claude Skills transform Trade Oracle from a manual system to a highly automated trading platform. By implementing these 7 skills, you'll:

✅ **Test faster** - Automated workflows replace bash scripts
✅ **Deploy confidently** - Intelligent diagnostics catch issues early
✅ **Optimize proactively** - Performance analysis prevents bottlenecks
✅ **Decide data-driven** - Weekly reflections provide actionable insights
✅ **Scale safely** - Systematic validation ensures production readiness

The modular nature of skills allows incremental adoption - start with high-impact skills, measure results, and expand as needed.

**Your competitive advantage**: Most traders don't have automated workflows. Skills give you the speed and consistency of a professional trading desk, powered by AI.

---

**Document Version**: 1.0
**Last Updated**: November 6, 2025
**Author**: Claude Code (with research by Plan agent)
**Status**: Ready for Implementation

**Tomorrow's Testing Checklist**:
- [ ] Test Execute Trade button with puts (downturn strategy)
- [ ] Verify iron condor script during market hours (9:31-9:45am ET)
- [ ] Check position monitor auto-exit conditions
- [ ] Review this guide and decide on Phase 1 skills to implement
