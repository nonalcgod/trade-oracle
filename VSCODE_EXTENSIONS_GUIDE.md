# VSCode Extensions Guide for Claude Code Terminal Workflow

**Last Updated:** 2025-11-06
**For:** Trade Oracle - Terminal-Based AI Development (NetworkChuck Method)

This guide explains how to use VSCode extensions to **amplify** Claude Code's effectiveness when working in the terminal.

---

## Philosophy: VSCode as "Eyes", Claude Code as "Hands"

**VSCode Role:**
- Visualize errors and warnings inline (Error Lens)
- Show git history and blame (GitLens)
- Test API endpoints (REST Client / Thunder Client)
- Query database directly (PostgreSQL extension)
- Format code automatically (Black, Prettier)

**Claude Code Role (in Terminal):**
- Write and edit code based on what you describe
- Fix errors you copy from VSCode's inline display
- Implement features across multiple files
- Run tests and handle git operations
- Deploy to Railway/Vercel

**Key Insight:** VSCode shows you problems → You describe them to Claude → Claude fixes them → VSCode confirms the fix. This creates a tight feedback loop.

---

## Installation

### Automatic (Recommended)

1. Open VSCode in the `trade-oracle` directory
2. VSCode will detect `.vscode/extensions.json` and prompt:
   ```
   Do you want to install the recommended extensions for this repository?
   ```
3. Click **Install All**

### Manual

Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux), type `Extensions: Show Recommended Extensions`, and install individually.

---

## Essential Extensions for Claude Code Workflow

### 1. **Error Lens** (usernamehw.errorlens)

**What it does:** Shows errors and warnings **inline** at the end of each line (not just in the Problems panel).

**Why it's critical for Claude:**
- You can **screenshot** errors and send to Claude Code
- You can **copy** the exact error message without scrolling through Problems panel
- Claude sees errors in context with the surrounding code

**Example Workflow:**
```
VSCode shows inline error:
  Line 45: Argument of type 'str' cannot be assigned to parameter 'symbol' of type 'Decimal'

You tell Claude:
  > Fix the type error on line 45 in backend/api/data.py

Claude reads the file, sees the error, fixes it immediately
```

**Settings (already configured):**
```json
"errorLens.enabledDiagnosticLevels": ["error", "warning"],
"errorLens.followCursor": "activeLine"
```

---

### 2. **GitLens** (eamodio.gitlens)

**What it does:** Shows git blame, commit history, and authorship inline in the editor.

**Why it's useful for Claude:**
- See who wrote code and when (helps Claude understand intent)
- View commit messages inline (gives Claude context on past decisions)
- Compare file history before asking Claude to refactor

**Example Workflow:**
```
You hover over a function and see:
  Written by: Joshua James, 3 days ago
  Commit: "FEATURE: Add position monitoring with 50% profit exit"

You tell Claude:
  > Refactor the position monitoring logic to support iron condors
  > (Claude now knows this is recent work and understands the context)
```

**Tip:** Use `Cmd+Shift+G` to open GitLens side panel and explore full file history.

---

### 3. **REST Client** (humao.rest-client)

**What it does:** Test HTTP API endpoints directly in VSCode (no Postman/Insomnia needed).

**Why it's perfect for Claude:**
- Create `.http` files with API requests
- Claude can generate test requests for you
- See responses inline without switching windows

**Example Workflow:**

**Step 1:** Create `test-api.http` in project root:
```http
### Health Check
GET http://localhost:8000/health

### Get Latest Option Data
GET http://localhost:8000/api/data/latest/SPY241206C00600000

### Generate Signal
POST http://localhost:8000/api/strategies/signal
Content-Type: application/json

{
  "symbol": "SPY241206C00600000",
  "underlying_symbol": "SPY",
  "current_price": 12.50,
  "iv": 0.35,
  "delta": 0.45
}
```

**Step 2:** Click "Send Request" above each `###` section

**Step 3:** If API fails, copy error response and tell Claude:
```
> API returned 422 error: "Field 'gamma' required but missing"
> Fix the Signal model in backend/models/trading.py
```

**Settings (already configured):**
```json
"rest-client.environmentVariables": {
  "development": { "apiUrl": "http://localhost:8000" },
  "production": { "apiUrl": "https://trade-oracle-production.up.railway.app" }
}
```

Switch environments with `Cmd+Shift+P` → `REST Client: Switch Environment`

---

### 4. **PostgreSQL Extension** (ms-ossdata.vscode-postgresql)

**What it does:** Query Supabase database directly from VSCode.

**Why it's useful for Claude:**
- Verify data Claude inserted/updated
- Export query results to share with Claude
- Test SQL migrations before Claude applies them

**Setup:**

1. Press `Cmd+Shift+P` → `PostgreSQL: Add Connection`
2. Enter your Supabase connection string:
   ```
   postgresql://postgres:[password]@[project-ref].supabase.co:5432/postgres
   ```
3. Save connection as "Trade Oracle Supabase"

**Example Workflow:**
```sql
-- Check if position monitor created trades
SELECT * FROM trades
WHERE action = 'CLOSE_LONG'
ORDER BY timestamp DESC
LIMIT 10;

-- Verify IV data seeding
SELECT symbol, COUNT(*) as tick_count
FROM option_ticks
GROUP BY symbol;
```

**Tip:** Save common queries in `sql/queries.sql` and ask Claude to generate new ones:
```
> Write a SQL query to find all positions that hit 50% profit target
```

---

### 5. **Thunder Client** (rangav.vscode-thunder-client)

**What it does:** GUI-based API testing (alternative to REST Client if you prefer clicking over writing `.http` files).

**Why it's useful:**
- Visual environment/variable management
- Import/export collections
- Better for complex multi-step API workflows

**Example Workflow:**
1. Create collection: "Trade Oracle API Tests"
2. Add requests for each endpoint
3. Export collection as JSON
4. Share with Claude to generate test cases:
   ```
   > Generate Thunder Client test cases for all iron condor endpoints
   ```

---

### 6. **Docker Extension** (ms-azuretools.vscode-docker)

**What it does:** Manage Docker containers, images, and Dockerfiles from VSCode.

**Why it's critical for Railway:**
- Build/test Dockerfile locally before pushing to Railway
- See container logs without terminal commands
- Validate docker-compose.yml syntax

**Example Workflow:**

**Step 1:** Right-click `Dockerfile` → `Build Image`

**Step 2:** If build fails, copy error and tell Claude:
```
> Docker build failed with "ModuleNotFoundError: No module named 'supabase'"
> Fix requirements-railway.txt
```

**Step 3:** Right-click image → `Run` to test locally

**Tip:** Use `Cmd+Shift+P` → `Docker: Prune System` to clean up old containers/images.

---

### 7. **Black Formatter** (ms-python.black-formatter)

**What it does:** Auto-formats Python code to PEP 8 standards on save.

**Why it helps Claude:**
- Ensures consistent code style across all files
- Reduces formatting noise in git diffs
- Claude's code automatically matches project style

**Settings (already configured):**
```json
"[python]": {
  "editor.defaultFormatter": "ms-python.black-formatter",
  "editor.formatOnSave": true
},
"black-formatter.args": ["--line-length", "100"]
```

**Tip:** If Claude writes code that's not formatted, just save the file and Black will fix it automatically.

---

### 8. **Prettier** (esbenp.prettier-vscode)

**What it does:** Auto-formats JavaScript/TypeScript/React code on save.

**Why it helps Claude:**
- Consistent frontend code style
- No manual formatting needed after Claude edits
- Matches industry standards (important for sharing code)

**Settings (already configured):**
```json
"[typescript]": {
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true
}
```

---

## Productivity Boosters

### 9. **Path Intellisense** (christian-kohler.path-intellisense)

**What it does:** Autocompletes file paths as you type.

**Why it helps with Claude:**
- No typos when referencing files
- Faster communication: "Fix backend/api/risk.py line 45" (autocompleted, no mistakes)

---

### 10. **Better Comments** (aaron-bond.better-comments)

**What it does:** Highlights TODO/FIXME/NOTE/HACK comments in different colors.

**Why it's useful for Claude workflow:**
- Leave TODOs for Claude to implement later
- Mark FIXME sections for Claude to review
- Add NOTE comments to explain why code exists (helps Claude understand context)

**Example:**
```python
# TODO: Implement earnings blackout detection (ask Claude)
# FIXME: This IV rank calculation is slow (optimize with Claude)
# NOTE: Hardcoded 2% risk limit - DO NOT CHANGE without backtest (tell Claude)
```

---

### 11. **Markdown All-in-One** (yzhang.markdown-all-in-one)

**What it does:** Powerful markdown editing with preview, table of contents, formatting shortcuts.

**Why it's critical for this project:**
- Edit `CLAUDE.md` (this context file) efficiently
- Preview documentation before committing
- Generate TOCs for long docs like `0DTE_IRON_CONDOR_EXPERT_GUIDE.md`

**Shortcuts:**
- `Cmd+Shift+V`: Preview markdown
- `Cmd+K V`: Preview side-by-side
- `Cmd+B`: Bold text
- `Cmd+I`: Italic text

---

## Advanced Workflows

### Workflow 1: Fix Backend Errors with Claude

1. **VSCode shows error** (Error Lens): `Line 120: 'Symbol' object has no attribute 'underlying_symbol'`
2. **You copy error** to clipboard
3. **Tell Claude:**
   ```
   > I'm getting this error in backend/api/iron_condor.py:
   > Line 120: 'Symbol' object has no attribute 'underlying_symbol'
   > Fix it
   ```
4. **Claude reads file** (using Read tool)
5. **Claude identifies issue** (accessing wrong attribute)
6. **Claude fixes code** (using Edit tool)
7. **You save file** in VSCode
8. **Error Lens clears** (confirms fix)

---

### Workflow 2: Test API Endpoint with REST Client

1. **Create `test-iron-condor.http`:**
   ```http
   ### Generate Iron Condor Signal
   POST http://localhost:8000/api/iron-condor/signal
   Content-Type: application/json

   {
     "underlying_symbol": "SPY"
   }
   ```
2. **Click "Send Request"**
3. **API returns 500 error:** `"detail": "No strikes found for SPY"`
4. **Tell Claude:**
   ```
   > API endpoint /api/iron-condor/signal returned 500 error
   > Error message: "No strikes found for SPY"
   > Debug the strike selection logic in backend/strategies/iron_condor.py
   ```
5. **Claude investigates** (reads logs, checks Alpaca API)
6. **Claude finds issue** (no 0DTE options available in paper trading)
7. **Claude explains** and suggests using QQQ instead

---

### Workflow 3: Query Database and Fix Data Issues

1. **Open PostgreSQL extension** (sidebar icon)
2. **Run query:**
   ```sql
   SELECT * FROM positions WHERE status = 'in_progress' AND created_at < NOW() - INTERVAL '7 days';
   ```
3. **Results show** 3 stale positions from a week ago
4. **Tell Claude:**
   ```
   > I found 3 positions stuck in 'in_progress' status for 7+ days
   > Position IDs: 12, 15, 18
   > Write a script to clean up stale positions and prevent this in the future
   ```
5. **Claude creates** `backend/scripts/cleanup_stale_positions.py`
6. **Claude adds** monitoring logic to position_monitor.py

---

### Workflow 4: Build and Test Docker Image Locally

1. **Right-click Dockerfile** → `Build Image`
2. **Build fails** with error:
   ```
   ERROR: Could not find a version that satisfies the requirement supabase==2.15.1
   ```
3. **Tell Claude:**
   ```
   > Docker build failed - supabase version not found
   > Here's the error: [paste full error]
   > Fix requirements-railway.txt
   ```
4. **Claude updates** requirements-railway.txt (removes pin or updates version)
5. **You rebuild** image (right-click Dockerfile → Build Image)
6. **Build succeeds**
7. **Right-click image** → `Run` to test locally
8. **Open http://localhost:8000/health** to verify

---

## Extensions to AVOID (Conflicts with Claude Code)

**DO NOT INSTALL:**
- ❌ **GitHub Copilot** - Redundant with Claude Code, different completion style
- ❌ **Cursor AI Extension** - This is a different tool (Cursor IDE vs Claude Code)
- ❌ **Continue** - Another AI coding assistant (conflicts with Claude)
- ❌ **Tabnine** - AI autocomplete (unnecessary with Claude Code)

**Why avoid these?**
- Multiple AI assistants create confusion (which one is writing code?)
- Different coding styles conflict
- Wastes token budget on redundant suggestions
- Claude Code in terminal is more powerful (200K context, full file access)

---

## Keyboard Shortcuts (Optimized for Claude Workflow)

### File Navigation
- `Cmd+P`: Quick file open (tell Claude exact file name)
- `Cmd+Shift+P`: Command palette (access all extensions)
- `Cmd+B`: Toggle sidebar (more screen space for terminal)

### Editing
- `Cmd+/`: Toggle comment (mark code for Claude to review)
- `Cmd+D`: Select next occurrence (find all instances before asking Claude to refactor)
- `Cmd+Shift+L`: Select all occurrences

### Git (with GitLens)
- `Cmd+Shift+G`: Open Git panel
- `Option+Click` on line number: Show git blame inline

### Terminal
- `Ctrl+` ` `: Toggle terminal (switch between Claude and code)
- `Cmd+Shift+` ` `: New terminal (run Claude in one, tests in another)

### REST Client
- `Cmd+Alt+R`: Send HTTP request at cursor

---

## Troubleshooting

### Error Lens Not Showing Errors

**Problem:** Error Lens installed but no inline errors appear.

**Solution:**
1. Check if Pylance is active: `Cmd+Shift+P` → `Python: Select Interpreter`
2. Reload window: `Cmd+Shift+P` → `Developer: Reload Window`
3. Verify settings:
   ```json
   "errorLens.enabledDiagnosticLevels": ["error", "warning"]
   ```

---

### PostgreSQL Extension Can't Connect to Supabase

**Problem:** "Connection refused" or "SSL required" error.

**Solution:**
1. Get connection string from Supabase dashboard: Settings → Database → Connection String (Direct)
2. Format: `postgresql://postgres.xxxx:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres`
3. Enable SSL in connection settings (toggle "SSL" to ON)

---

### REST Client Returns CORS Error

**Problem:** API request fails with CORS policy error.

**Solution:** This only happens in browser, not REST Client. If you see CORS errors:
1. Verify you're using REST Client (not browser DevTools)
2. Check `backend/main.py` has correct CORS origins:
   ```python
   allow_origins=["http://localhost:5173", "https://trade-oracle-lac.vercel.app"]
   ```
3. Restart backend: `cd backend && python main.py`

---

### Docker Extension Shows No Containers

**Problem:** Extension shows empty containers/images list.

**Solution:**
1. Verify Docker Desktop is running
2. Check Docker daemon: `docker ps` in terminal
3. Reload VSCode: `Cmd+Shift+P` → `Developer: Reload Window`

---

## Pro Tips

### 1. Use Multi-Terminal Layout

**Setup:**
1. Open integrated terminal: `Ctrl+` `
2. Click `+` icon → `Split Terminal`
3. Layout:
   - **Left Terminal:** Claude Code session (always running)
   - **Right Terminal:** Backend server (`python main.py`)
   - **Bottom Terminal:** Frontend server (`npm run dev`)

**Benefit:** Never lose Claude context by switching terminals.

---

### 2. Create Keyboard Shortcut for REST Client

**Add to `keybindings.json`:**
```json
[
  {
    "key": "cmd+shift+r",
    "command": "rest-client.request",
    "when": "editorTextFocus && editorLangId == 'http'"
  }
]
```

**Benefit:** Send API requests instantly (`Cmd+Shift+R` instead of clicking "Send Request").

---

### 3. Use Error Lens with Screenshots

**Workflow:**
1. Error appears inline in VSCode
2. Press `Cmd+Shift+4` (Mac) to screenshot the error + surrounding code
3. Save screenshot
4. Tell Claude:
   ```
   > I'm getting an error - see screenshot at /path/to/screenshot.png
   > (Claude reads image and sees error in context)
   ```

**Benefit:** Claude sees exact visual context, not just text error message.

---

### 4. Create Saved Queries in PostgreSQL Extension

**Setup:**
1. Open PostgreSQL extension
2. Right-click connection → `New Query`
3. Write common query (e.g., "Show all open positions")
4. Save as `queries/open_positions.sql`
5. Add to workspace for quick access

**Benefit:** Verify Claude's database changes instantly without rewriting queries.

---

### 5. Use GitLens File History Before Major Refactors

**Workflow:**
1. Before asking Claude to refactor a file, right-click file → `Open File History`
2. Review recent commits and changes
3. Tell Claude:
   ```
   > I need to refactor backend/api/execution.py
   > Recent changes: Added multi-leg support (commit 74f469b)
   > Make sure refactor preserves multi-leg functionality
   ```

**Benefit:** Claude has context on recent work and won't accidentally break new features.

---

## Integration with Claude Code Sessions

### Starting a Session with VSCode Ready

**Step 1:** Open VSCode in `trade-oracle` directory

**Step 2:** Open 3 terminals (split layout):
- Left: `claude` (launch Claude Code)
- Right: `cd backend && python main.py`
- Bottom: `cd frontend && npm run dev`

**Step 3:** Open key files in tabs:
- `CLAUDE.md` (context file)
- `backend/api/iron_condor.py` (main work file)
- `test-api.http` (for testing)

**Step 4:** Tell Claude:
```
> I'm ready to work. VSCode is open with backend running on port 8000 and frontend on 5173.
> What's our current status?
```

**Benefit:** Claude knows your environment is ready, and you can instantly test changes.

---

### Ending a Session with Context Saved

**Step 1:** Tell Claude:
```
> @session-closer wrap up today's work
```

**Step 2:** Claude will:
- Update `CLAUDE.md` with today's progress
- Commit changes to git
- Close cleanly

**Step 3:** Close VSCode terminals (but keep tabs open)

**Step 4:** Next session:
- Reopen same VSCode tabs
- Claude auto-loads context from `CLAUDE.md`
- No re-explaining needed!

---

## Summary: Your Ultimate Setup

**Installed Extensions:**
- ✅ Error Lens (inline errors for Claude to fix)
- ✅ GitLens (code history for Claude context)
- ✅ REST Client (API testing without leaving VSCode)
- ✅ PostgreSQL (database queries inline)
- ✅ Docker (test Railway builds locally)
- ✅ Black + Prettier (auto-formatting)
- ✅ Markdown All-in-One (edit CLAUDE.md efficiently)

**VSCode as Your "Command Center":**
- **See** errors inline (Error Lens)
- **Test** APIs visually (REST Client)
- **Query** database (PostgreSQL)
- **Track** changes (GitLens)
- **Build** Docker images (Docker extension)

**Claude Code as Your "Engineer":**
- **Fix** errors you point out
- **Write** code across multiple files
- **Test** changes via terminal
- **Deploy** to Railway/Vercel
- **Update** documentation

**Result:** You control what gets built, Claude handles the implementation details. VSCode gives you visibility, Claude Code gives you velocity.

---

## Resources

- VSCode Keyboard Shortcuts: `Cmd+K Cmd+S`
- Extension Marketplace: https://marketplace.visualstudio.com/vscode
- REST Client Docs: https://marketplace.visualstudio.com/items?itemName=humao.rest-client
- GitLens Docs: https://gitlens.amod.io
- Docker Extension: https://code.visualstudio.com/docs/containers/overview

---

*Last updated: 2025-11-06 | For questions, ask Claude Code in terminal!*
