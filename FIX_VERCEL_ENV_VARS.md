# Fix Vercel Environment Variables - CRITICAL BLOCKER

**Date**: November 5, 2025
**Status**: 🔴 **CRITICAL** - Must fix before database migration
**Time Required**: 5 minutes
**Impact**: Frontend API calls will fail without this fix

---

## Problem

Vercel environment variables currently point to `localhost` instead of Railway production URL. This means the frontend will not be able to communicate with the backend in production.

**Current (BROKEN)**:
```
VITE_API_URL="http://localhost:8000\n"
```

**Expected (WORKING)**:
```
VITE_API_URL=https://trade-oracle-production.up.railway.app
```

---

## Fix Instructions

### Step 1: Open Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Navigate to your `trade-oracle` project
3. Click **Settings** in the top navigation
4. Click **Environment Variables** in the left sidebar

---

### Step 2: Update Environment Variables

**Delete or Update These Variables**:

| Variable | Current Value | New Value |
|----------|---------------|-----------|
| `VITE_API_URL` | `http://localhost:8000\n` | `https://trade-oracle-production.up.railway.app` |
| `VITE_SUPABASE_URL` | (if exists) | `https://fltkfgfyjjsijgmhrnqt.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | (if exists) | Your Supabase anon key |

**Remove These Variables** (wrong project):
- `N8N_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL` (wrong naming convention - use `VITE_` prefix)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (wrong naming convention - use `VITE_` prefix)

---

### Step 3: Required Environment Variables

Ensure these 3 variables are set correctly:

```bash
# Backend API URL (Railway)
VITE_API_URL=https://trade-oracle-production.up.railway.app

# Supabase (for real-time updates)
VITE_SUPABASE_URL=https://fltkfgfyjjsijgmhrnqt.supabase.co
VITE_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

**Where to find Supabase keys**:
1. Go to https://app.supabase.com/project/fltkfgfyjjsijgmhrnqt/settings/api
2. Copy **Project URL** → Use as `VITE_SUPABASE_URL`
3. Copy **anon public** key → Use as `VITE_SUPABASE_ANON_KEY`

---

### Step 4: Redeploy Frontend

After updating environment variables, trigger a new deployment:

**Option A: From Vercel Dashboard**
1. Go to **Deployments** tab
2. Click the **⋯** menu on the latest deployment
3. Click **Redeploy**
4. Confirm redeploy

**Option B: From Git**
```bash
cd frontend
git commit --allow-empty -m "chore: Trigger Vercel redeploy after env var fix"
git push origin main
```

Vercel will automatically redeploy with new environment variables.

---

## Verification

After redeployment, test the frontend:

### Test 1: Check API Connection
1. Open https://trade-oracle-lac.vercel.app
2. Open browser console (F12)
3. Look for API requests to `https://trade-oracle-production.up.railway.app`
4. Should see 200 OK responses, NOT errors about `localhost`

### Test 2: Check Backend Status
```bash
# Should return {"status": "healthy"}
curl https://trade-oracle-production.up.railway.app/health
```

### Test 3: Check Frontend API Calls
1. Navigate to Trade Oracle dashboard
2. Should see "Backend: Connected" indicator (green)
3. Should NOT see "Backend: Disconnected" (red)

---

## What This Fixes

- ✅ Frontend can communicate with Railway backend
- ✅ API calls work in production (not just localhost)
- ✅ Dashboard displays real-time data from backend
- ✅ Iron condor endpoints can be called from frontend
- ✅ Position monitoring data displayed correctly

---

## Common Issues

### Issue: "Still seeing localhost in Network tab"

**Solution**: Hard refresh browser cache
1. Open https://trade-oracle-lac.vercel.app
2. Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
3. This clears cached environment variables

### Issue: "Vercel deployment succeeded but env vars didn't update"

**Solution**: Environment variables only apply to NEW deployments
1. Make sure you triggered a redeploy AFTER updating env vars
2. Check deployment logs for "VITE_API_URL" to confirm value
3. May need to redeploy again if timing was off

### Issue: "Cannot find Railway URL"

**Railway Production URL**: `https://trade-oracle-production.up.railway.app`

Verify it's working:
```bash
curl https://trade-oracle-production.up.railway.app/health
```

---

## After This Fix

Once Vercel environment variables are fixed, you can proceed with:

1. ✅ Apply database migration (`002_multi_leg_positions.sql`)
2. ✅ Test iron condor end-to-end
3. ✅ Frontend will display iron condor positions correctly
4. ✅ System ready for production use

---

**Status After Fix**: Frontend fully operational with Railway backend!

