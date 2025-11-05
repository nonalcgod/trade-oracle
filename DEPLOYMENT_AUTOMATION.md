# Trade Oracle - Automated Deployment Guide

This guide explains how to use the automated deployment scripts to get Trade Oracle live in under 20 minutes.

## Overview

We've created 3 automation scripts that handle the entire deployment process:

1. **`setup-credentials.sh`** - Interactive credential setup and CLI authentication
2. **`setup-database.sh`** - Automatic Supabase database creation
3. **`deploy.sh`** - Automated deployment to Railway and Vercel

## Prerequisites

Before starting, create accounts at:
- [Supabase](https://supabase.com) - Database
- [Railway](https://railway.app) - Backend hosting
- [Vercel](https://vercel.com) - Frontend hosting
- [Alpaca Markets](https://alpaca.markets) - Paper trading API
- [Anthropic](https://console.anthropic.com) - Claude API

## Deployment Process

### Step 1: Setup Credentials (5 minutes)

Run the interactive credential setup:

```bash
./setup-credentials.sh
```

This script will:
- Guide you through entering all API keys
- Save credentials to `.env` file (gitignored)
- Authenticate Railway, Vercel, and GitHub CLIs
- Open browser windows for OAuth login

**You'll need to provide:**
- Alpaca API Key & Secret (from paper trading dashboard)
- Supabase URL & Keys (from project settings)
- Anthropic API Key (from console)

### Step 2: Create GitHub Repository (2 minutes)

After credentials are set up, create and push to GitHub:

```bash
# Create private GitHub repo and push
gh repo create trade-oracle --private --source=. --push
```

Or manually:
```bash
# Create repo on GitHub website, then:
git remote add origin https://github.com/YOUR_USERNAME/trade-oracle.git
git add .
git commit -m "Initial commit: Trade Oracle"
git push -u origin main
```

### Step 3: Setup Supabase Database (2 minutes)

#### Option A: Automatic (Recommended)

```bash
./setup-database.sh
```

This automatically runs the schema in your Supabase project.

#### Option B: Manual

1. Go to [Supabase SQL Editor](https://supabase.com/dashboard)
2. Select your `trade-oracle` project
3. Click **SQL Editor** → **New query**
4. Copy contents of `backend/schema.sql`
5. Paste and click **Run**

### Step 4: Deploy Everything (10 minutes)

Run the automated deployment:

```bash
./deploy.sh
```

This script will:
1. ✅ Verify all credentials are present
2. ✅ Check CLI authentication
3. ✅ Push code to GitHub
4. ✅ Deploy backend to Railway with environment variables
5. ✅ Deploy frontend to Vercel with API URL
6. ✅ Test both deployments
7. ✅ Display URLs for backend and frontend

## What Gets Deployed

### Backend (Railway)
- FastAPI application running on Railway
- Environment variables automatically configured
- Health endpoint at `/health`
- API docs at `/docs`
- Weekly cron job for Claude reflections

### Frontend (Vercel)
- React dashboard deployed to Vercel
- Connected to Railway backend
- Environment variable `REACT_APP_API_URL` set automatically
- Accessible at `https://your-project.vercel.app`

## Post-Deployment

After successful deployment:

1. **Visit your dashboard**: The deploy script shows the Vercel URL
2. **Check backend health**: Visit `https://your-railway-url/health`
3. **View API docs**: Visit `https://your-railway-url/docs`
4. **Verify database**: Check Supabase dashboard for tables
5. **Monitor logs**:
   - Railway: https://railway.app/dashboard
   - Vercel: https://vercel.com/dashboard

## Troubleshooting

### "Railway not authenticated"
```bash
railway login
# Follow browser prompts
```

### "Vercel not authenticated"
```bash
vercel login
# Follow email verification
```

### "Missing environment variables"
Edit `.env` file and ensure all values are filled in:
```bash
nano .env  # or use your preferred editor
```

### Database schema failed
Run manually in Supabase SQL Editor:
1. Copy `backend/schema.sql`
2. Paste in SQL Editor
3. Click Run

### Deployment failed
Check logs:
```bash
# Railway logs
railway logs

# Vercel logs
vercel logs
```

## Updating Your Deployment

After making code changes:

```bash
# Commit changes
git add .
git commit -m "Update: description of changes"
git push origin main

# Redeploy (both Railway and Vercel auto-deploy on push)
# Or manually trigger:
./deploy.sh
```

## Environment Variables

All environment variables are stored in `.env` (gitignored). To update:

### Railway Variables
```bash
cd backend
railway variables set VARIABLE_NAME="new value"
```

### Vercel Variables
```bash
cd frontend
vercel env add REACT_APP_API_URL production
# Enter the Railway URL when prompted
```

## Cost Breakdown

| Service | Free Tier | Duration |
|---------|-----------|----------|
| Railway | $5 credit | ~4 weeks |
| Vercel | Unlimited | Forever |
| Supabase | 500MB DB | Forever |
| Alpaca | Paper trading | Forever |
| Anthropic | Pay-per-use | N/A |

**Total monthly cost after free tier**: ~$5-10

## Security Notes

- ✅ `.env` file is gitignored (never committed)
- ✅ All credentials stored locally only
- ✅ Railway and Vercel environment variables encrypted
- ✅ Paper trading only (no real money risk)
- ✅ Private GitHub repository recommended

## Support

If you encounter issues:
1. Check Railway logs: `railway logs`
2. Check Vercel logs: `vercel logs`
3. Verify environment variables: `railway variables` and `vercel env ls`
4. Review Supabase dashboard for database errors

## Quick Reference

```bash
# Setup (one-time)
./setup-credentials.sh   # Configure credentials
gh repo create trade-oracle --private --source=. --push
./setup-database.sh      # Setup Supabase DB

# Deploy
./deploy.sh             # Deploy everything

# Update
git push origin main    # Auto-deploys to Railway & Vercel

# Logs
railway logs            # Backend logs
vercel logs             # Frontend logs

# Variables
railway variables       # View Railway env vars
vercel env ls          # View Vercel env vars
```

---

**Ready to deploy?** Run `./setup-credentials.sh` to get started!
