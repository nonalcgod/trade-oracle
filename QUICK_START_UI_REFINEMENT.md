# Quick Start: Progressive UI Refinement

**30-second guide to running your first iteration**

---

## Prerequisites

✅ Vite dev server running:
```bash
cd frontend && npm run dev
```

✅ Browser shows Trade Oracle at `http://localhost:3000`

---

## Run Iteration 1

```bash
# From project root:
./scripts/progressive-ui-refinement.sh 1
```

This will:

1. **📸 Capture Screenshots** (Automatic)
   - Playwright takes full-page + component screenshots
   - Saved to: `frontend/tests/visual/screenshots/`

2. **🔍 Analyze UI** (Manual - you'll be prompted)
   - Open new terminal: `claude`
   - Type:
     ```
     @benai-ui-critic analyze the screenshots in tests/visual/screenshots/dashboard-full-desktop.png
     and create a detailed analysis report. Save it as tests/visual/analysis/visual-analysis-iteration-1.md
     ```
   - Wait for report (2-3 minutes)
   - Press ENTER when done

3. **🛠️ Implement Fixes** (Manual - you'll be prompted)
   - In Claude Code, type:
     ```
     @benai-ui-implementer read the feedback from tests/visual/analysis/visual-analysis-iteration-1.md
     and implement the top 3-5 high-priority fixes. Make targeted, component-level changes only.
     ```
   - Wait for changes (3-5 minutes)
   - Check browser: `http://localhost:3000`
   - Press ENTER when done

4. **📦 Git Commit** (Semi-automatic)
   - Review changes shown
   - Type `y` to commit
   - Iteration 1 saved to git!

---

## Expected Result

**Before**: Compliance score ~50-60%
- Gray background instead of cream
- Small hero font size
- Sharp rectangular corners
- Wrong color palette

**After Iteration 1**: Compliance score ~80%
- ✅ Warm cream background (#F5F1E8)
- ✅ Hero balance 48-56px
- ✅ Rounded corners (16px)
- ✅ Ben AI color palette

---

## View Results

```bash
# Browser
open http://localhost:3000

# Analysis report
cat frontend/tests/visual/analysis/visual-analysis-iteration-1.md

# Screenshots
open frontend/tests/visual/screenshots/

# Git commit
git log -1
```

---

## Run Iteration 2

```bash
./scripts/progressive-ui-refinement.sh 2
```

Repeat until compliance >= 95% or 5 iterations complete!

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Backend: Disconnected" | Check `frontend/.env.local` has Railway URL |
| "Vite not running" | Run `cd frontend && npm run dev` |
| "Screenshots empty" | Wait for page to load, check browser console |
| "Agent didn't save file" | Manually create `tests/visual/analysis/` directory |

---

## Full Documentation

See `PROGRESSIVE_UI_REFINEMENT.md` for complete guide (2,500+ words).

---

**Let's make this UI pixel-perfect! 🎨**
