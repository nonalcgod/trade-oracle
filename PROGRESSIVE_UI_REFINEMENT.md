# Progressive UI Refinement System

**Automated feedback loop for iterative UI improvements using dual-agent architecture**

## Overview

This system uses **Playwright visual testing** + **two specialized AI agents** to progressively refine the Trade Oracle UI to match the Ben AI aesthetic through automated iterations.

### The Workflow

```
┌─────────────────┐
│ 1. Capture      │  Playwright screenshots (full page + components)
│    Screenshots  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Analyze UI   │  benai-ui-critic agent compares to UI_DESIGN_PROMPT.md
│    (Critic)     │  Generates detailed feedback with compliance score
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Implement    │  benai-ui-implementer agent makes 3-5 targeted fixes
│    Fixes        │  Component-level edits only, no breaking changes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Git Commit   │  Atomic commit with descriptive message
│                 │  Tracks iteration progress
└────────┬────────┘
         │
         ▼
         │
   ┌────┴────────┐
   │ Compliance  │
   │ >= 95%?     │◄─────────┐
   └────┬───┬────┘          │
        │   │                │
       Yes  No               │
        │   │                │
        │   └───────────────┘
        │    (Repeat: Max 5 iterations)
        ▼
    ┌──────┐
    │ Done │
    └──────┘
```

---

## Quick Start

### Prerequisites

1. **Vite dev server running** on `http://localhost:3000`
   ```bash
   cd frontend
   npm run dev
   ```

2. **Playwright installed** (already done if you followed setup)
   ```bash
   cd frontend
   npm install -D @playwright/test
   ```

3. **Agent definitions created** (✅ done - see `.claude/agents/`)
   - `benai-ui-critic.md`
   - `benai-ui-implementer.md`

### Run First Iteration

```bash
# From project root:
./scripts/progressive-ui-refinement.sh 1
```

This will:
1. ✅ Capture screenshots automatically (Playwright)
2. 🤖 Prompt you to launch **benai-ui-critic** agent
3. 🛠️ Prompt you to launch **benai-ui-implementer** agent
4. 📦 Create git commit with changes
5. 📊 Show progress summary

---

## Detailed Workflow

### Step 1: Capture Screenshots

**Automatic (via Playwright)**

```bash
cd frontend
npm run test:visual:capture
```

**Output**:
- `tests/visual/screenshots/dashboard-full-desktop.png` (MacBook Pro 14" @ 1512×982)
- `tests/visual/screenshots/dashboard-full-tablet.png` (iPad @ 1024×1366)
- `tests/visual/screenshots/dashboard-full-mobile.png` (iPhone 14 Pro @ 393×852)
- `tests/visual/screenshots/portfolio-component.png`
- `tests/visual/screenshots/trades-component.png`
- `tests/visual/screenshots/positions-component.png`
- `tests/visual/screenshots/charts-component.png`

**Troubleshooting**:
- If "Backend: Disconnected" → Check `.env.local` has Railway URL
- If no screenshots → Check Vite is running on port 3000
- If components missing → Check DOM selectors in `capture-dashboard.spec.ts`

---

### Step 2: Analyze UI (benai-ui-critic)

**Manual (via Claude Code)**

1. Open terminal and run:
   ```bash
   claude
   ```

2. In Claude Code, type:
   ```
   @benai-ui-critic analyze the screenshots in tests/visual/screenshots/dashboard-full-desktop.png
   and create a detailed analysis report. Save it as tests/visual/analysis/visual-analysis-iteration-1.md
   ```

3. Wait for agent to complete (2-3 minutes)

**What the Agent Does**:
- Reads `UI_DESIGN_PROMPT.md` (Ben AI specification)
- Analyzes screenshots against design rules:
  - Color compliance (cream bg, emerald/rose/teal/amber)
  - Typography hierarchy (48-56px hero, monospace numbers)
  - Component styling (rounded-2xl, shadows, borders)
  - Spacing consistency (p-6, space-y-6)
  - Icon usage (Lucide React, correct sizes/colors)
- Generates compliance score (0-100%)
- Prioritizes issues (High/Medium/Low)
- Provides specific fixes with Tailwind class examples

**Output**:
- `tests/visual/analysis/visual-analysis-iteration-1.md` (detailed feedback)

**Example Feedback Snippet**:
```markdown
## Compliance Score: 65%

### High Priority Issues

1. **Page Background Color** 🔴 CRITICAL
   - Current: `bg-gray-100` (sterile gray)
   - Expected: `bg-[#F5F1E8]` (Ben AI cream)
   - Impact: Loses signature warm aesthetic
   - Fix: App.tsx line 42: Change className to `bg-[#F5F1E8]`

2. **Hero Balance Font Size** 🟠 MEDIUM
   - Current: 36-40px (too small)
   - Expected: 48-56px (`text-5xl lg:text-6xl`)
   - Impact: Hero metric not prominent enough
   - Fix: Portfolio.tsx line 67: `<h1 className="text-5xl font-mono font-bold lg:text-6xl">`
```

---

### Step 3: Implement Fixes (benai-ui-implementer)

**Manual (via Claude Code)**

1. In Claude Code, type:
   ```
   @benai-ui-implementer read the feedback from tests/visual/analysis/visual-analysis-iteration-1.md
   and implement the top 3-5 high-priority fixes. Make targeted, component-level changes only.
   ```

2. Wait for agent to complete (3-5 minutes)

3. Verify changes in browser at `http://localhost:3000`

**What the Agent Does**:
- Reads feedback from critic
- Triages issues by impact vs effort
- Makes 3-5 focused changes:
  - Tailwind class swaps (e.g., `bg-gray-100` → `bg-[#F5F1E8]`)
  - Typography updates (e.g., `text-4xl` → `text-5xl lg:text-6xl`)
  - Spacing tweaks (e.g., `p-4` → `p-6`)
- Preserves existing functionality (no API changes)
- Tests in browser (no regressions)

**Output**:
- Modified files: `frontend/src/App.tsx`, `Portfolio.tsx`, etc.
- Changes visible in browser immediately (Vite hot reload)

---

### Step 4: Git Commit

**Semi-Automatic (orchestrator prompts you)**

```bash
git add frontend/src/ frontend/tests/visual/
git commit -m "UI: Iteration 1 - Fix cream background, hero font size, card corners

- App.tsx: Change bg-gray-100 → bg-[#F5F1E8] (Ben AI cream)
- Portfolio.tsx: Increase hero balance text-4xl → text-5xl lg:text-6xl
- Portfolio.tsx, Trades.tsx: Update rounded-lg → rounded-2xl (16px corners)

Compliance Score: 65% → 82% (benai-ui-critic feedback)
Analysis: tests/visual/analysis/visual-analysis-iteration-1.md

Co-Authored-By: benai-ui-critic <noreply@anthropic.com>
Co-Authored-By: benai-ui-implementer <noreply@anthropic.com>
"
```

**Why Commit Per Iteration?**
- Rollback capability (if changes break something)
- Track progress numerically (compliance scores)
- Atomic changesets (easy to review)
- Git history shows refinement journey

---

### Step 5: Next Iteration

```bash
# Repeat with iteration 2
./scripts/progressive-ui-refinement.sh 2
```

**Stopping Criteria**:
- ✅ Compliance score >= 95% (near-perfect Ben AI match)
- ✅ Zero high-priority issues
- ✅ Maximum 5 iterations reached
- ✅ Developer satisfaction with visual state

---

## File Structure

```
trade-oracle/
├── .claude/
│   └── agents/
│       ├── benai-ui-critic.md           # Visual analysis specialist
│       ├── benai-ui-implementer.md       # Code generation specialist
│       └── benai-ui-expert.md            # Comprehensive UI expert (reference)
├── frontend/
│   ├── tests/
│   │   └── visual/
│   │       ├── screenshots/              # Playwright captures
│   │       │   ├── dashboard-full-desktop.png
│   │       │   ├── dashboard-full-tablet.png
│   │       │   ├── dashboard-full-mobile.png
│   │       │   ├── portfolio-component.png
│   │       │   ├── trades-component.png
│   │       │   ├── positions-component.png
│   │       │   └── charts-component.png
│   │       ├── analysis/                 # Critic feedback reports
│   │       │   ├── visual-analysis-iteration-1.md
│   │       │   ├── visual-analysis-iteration-2.md
│   │       │   └── ...
│   │       └── capture-dashboard.spec.ts # Playwright test
│   ├── playwright.config.ts              # Playwright configuration
│   └── package.json                      # Test scripts added
├── scripts/
│   └── progressive-ui-refinement.sh      # Orchestrator script
├── UI_DESIGN_PROMPT.md                   # Ben AI specification (497 lines)
└── PROGRESSIVE_UI_REFINEMENT.md          # This file
```

---

## Agent Details

### benai-ui-critic

**Role**: Visual design analyst

**Expertise**:
- Screenshot analysis and pixel-perfect comparison
- Design system compliance auditing
- Color theory, typography, spacing evaluation
- Financial dashboard best practices

**Input**:
- Screenshots (PNG files)
- UI_DESIGN_PROMPT.md (Ben AI spec)
- Previous iteration feedback (if iteration > 1)

**Output**:
- Markdown report (`visual-analysis-iteration-N.md`)
- Compliance score (0-100%)
- Prioritized issue list (High/Medium/Low)
- Specific fixes with Tailwind class examples

**Strengths**:
- Ruthless but constructive feedback
- Identifies violations of Ben AI aesthetic
- Provides actionable, specific fixes
- Tracks progress across iterations

---

### benai-ui-implementer

**Role**: Frontend code generator

**Expertise**:
- React + TypeScript component refactoring
- Tailwind CSS v4 utility-first styling
- Progressive enhancement (small, safe changes)
- Git workflow best practices

**Input**:
- Critic feedback (`visual-analysis-iteration-N.md`)
- Current codebase state

**Output**:
- Modified source files (component-level edits)
- No breaking changes
- Type-safe TypeScript
- Tailwind utilities only (no CSS files)

**Strengths**:
- Surgical, targeted fixes
- Preserves existing functionality
- Makes 3-5 high-impact changes per iteration
- Safe, reversible commits

---

## Common Workflows

### Workflow 1: First-Time Setup

```bash
# 1. Ensure dev server is running
cd frontend
npm run dev

# 2. Run first iteration
cd ..
./scripts/progressive-ui-refinement.sh 1

# 3. Follow prompts to launch agents
```

### Workflow 2: Continue Refinement

```bash
# Run next iteration (auto-detects iteration number)
./scripts/progressive-ui-refinement.sh
```

### Workflow 3: Manual Analysis Only

```bash
# Capture screenshots only
cd frontend
npm run test:visual:capture

# Then manually launch @benai-ui-critic agent in Claude Code
```

### Workflow 4: Manual Implementation Only

```bash
# If you already have feedback report, just implement
# In Claude Code:
@benai-ui-implementer read tests/visual/analysis/visual-analysis-iteration-2.md
and implement the top 3 fixes
```

### Workflow 5: Rollback Iteration

```bash
# If iteration broke something, rollback
git log --oneline  # Find iteration commit
git revert <commit-hash>

# Or reset to previous iteration
git reset --hard HEAD~1
```

---

## Troubleshooting

### Issue: "Vite dev server not running"

**Solution**:
```bash
cd frontend
npm run dev
# Wait for "Local: http://localhost:3000/"
```

### Issue: "Backend: Disconnected" in screenshots

**Solution**:
```bash
# Check .env.local in frontend directory
cat frontend/.env.local

# Should contain:
VITE_API_URL=https://trade-oracle-production.up.railway.app

# If missing or wrong, update it
echo 'VITE_API_URL=https://trade-oracle-production.up.railway.app' > frontend/.env.local

# Restart Vite
cd frontend
npm run dev
```

### Issue: "Playwright tests fail"

**Solution**:
```bash
# Reinstall Playwright browsers
cd frontend
npx playwright install

# Run tests with UI mode for debugging
npm run test:visual:ui
```

### Issue: "Agent doesn't create analysis file"

**Solution**:
- Ensure agent prompt includes: "Save it as tests/visual/analysis/visual-analysis-iteration-N.md"
- Check file permissions: `ls -la frontend/tests/visual/analysis/`
- Manually create directory: `mkdir -p frontend/tests/visual/analysis`

### Issue: "Git commit has merge conflicts"

**Solution**:
```bash
# Resolve conflicts manually
git status
git diff  # Review conflicts

# Edit files to resolve
# Then:
git add .
git commit -m "UI: Iteration N - Resolve conflicts"
```

### Issue: "Compliance score not improving"

**Solution**:
- Review critic feedback carefully
- Focus on HIGH priority issues first
- Ensure implementer is making correct changes
- Check browser for visual verification
- Run multiple iterations (some issues need 2-3 passes)

---

## Advanced Usage

### Custom Screenshot Sizes

Edit `frontend/tests/visual/capture-dashboard.spec.ts`:

```typescript
test('capture full page - custom viewport', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 });  // 1080p desktop

  await page.screenshot({
    path: 'tests/visual/screenshots/dashboard-full-1080p.png',
    fullPage: true,
    animations: 'disabled',
  });
});
```

### Visual Regression Testing

Compare against baseline:

```bash
cd frontend
npm run test:visual  # Runs visual regression tests
```

This will auto-create baselines on first run, then compare on subsequent runs.

### Mask Dynamic Content

Edit `capture-dashboard.spec.ts` to mask elements that change frequently:

```typescript
await expect(page).toHaveScreenshot('dashboard.png', {
  mask: [
    page.locator('text=/updated.*ago/i'),  // "Updated 3s ago"
    page.locator('text=/\\d{1,2}:\\d{2}:\\d{2}/'),  // Timestamps
    page.locator('.recharts-line'),  // Charts (if data changes)
  ],
});
```

---

## Expected Iteration Results

### Iteration 1 (Target: 60% → 80%)
**Focus**: Foundation fixes
- ✅ Cream background (#F5F1E8)
- ✅ Hero typography size increase
- ✅ Color palette corrections (emerald/rose/teal/amber)

**Typical Changes**:
- `App.tsx`: Background color
- `Portfolio.tsx`: Hero font size
- Global: Color class names

---

### Iteration 2 (Target: 80% → 90%)
**Focus**: Component refinement
- ✅ Rounded corners consistency (rounded-2xl)
- ✅ Spacing improvements (p-6, space-y-6)
- ✅ Pill badge styling

**Typical Changes**:
- All components: Border radius
- All components: Padding/margins
- PillBadge usage

---

### Iteration 3 (Target: 90% → 95%)
**Focus**: Visual polish
- ✅ Icon sizes and colors
- ✅ Responsive spacing adjustments
- ✅ Shadow consistency

**Typical Changes**:
- Icon imports and usage
- Responsive Tailwind classes
- Shadow classes

---

### Iteration 4-5 (Target: 95%+)
**Focus**: Pixel-perfect details
- ✅ Minor typography tweaks
- ✅ Animation smoothness
- ✅ Edge cases

**Typical Changes**:
- Fine-tuning spacing
- Hover states
- Transition timing

---

## Success Criteria

### UI is Ready When:
- ✅ **Compliance score >= 95%** - Near-perfect Ben AI match
- ✅ **Zero high-priority issues** - All critical problems fixed
- ✅ **Visual consistency** - Every component follows design system
- ✅ **Production-ready** - Stable, tested, deployable
- ✅ **Developer satisfaction** - Looks like a FAANG product

### Screenshots Should Show:
- ✅ Warm cream background (#F5F1E8)
- ✅ Hero balance 48-56px monospace
- ✅ All cards rounded-2xl (16px corners)
- ✅ Correct color semantics (green=profit, red=loss, teal=neutral, amber=warning)
- ✅ Pill badges properly styled
- ✅ Status dots with pulse animation
- ✅ All numbers in monospace font with 2 decimal places

---

## Tips for Best Results

### For Critic Agent:
- Provide full-page screenshot for complete context
- Ask for specific compliance score (0-100%)
- Request prioritization (High/Medium/Low)
- Include previous iteration feedback for progress tracking

### For Implementer Agent:
- Start with high-impact, low-effort fixes
- Make 3-5 changes per iteration (stay focused)
- Test in browser after each change
- Preserve existing data fetching logic

### For Manual Review:
- Check browser after each iteration
- Verify no console errors
- Test responsive behavior (desktop, tablet, mobile)
- Run `npm run build` to ensure TypeScript compiles

---

## Next Steps

1. **Run first iteration**: `./scripts/progressive-ui-refinement.sh 1`
2. **Review feedback**: `cat frontend/tests/visual/analysis/visual-analysis-iteration-1.md`
3. **Check browser**: Verify changes at `http://localhost:3000`
4. **Continue**: Run iteration 2 if needed
5. **Celebrate**: When compliance >= 95%! 🎉

---

## Resources

- **UI Specification**: `UI_DESIGN_PROMPT.md` (497 lines)
- **Ben AI Visual Reference**: `design-reference/BENAI_VISUAL_REFERENCE.md` (**PRIMARY REFERENCE** - extracted from actual screenshots)
- **Agent Definitions**: `.claude/agents/benai-ui-critic.md`, `benai-ui-implementer.md`
- **Playwright Docs**: https://playwright.dev/docs/screenshots
- **Tailwind CSS v4**: https://tailwindcss.com/docs
- **Ben AI Website**: https://ben.ai (design inspiration)

---

**Built with ❤️ using progressive automation and AI-driven testing**
