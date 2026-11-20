# RoofwiseBD Backend — Deployment Guide

## Files Created

| File | Purpose |
|---|---|
| `backend/Procfile` | Render / Heroku start command |
| `backend/runtime.txt` | Python version pin (Render/Heroku) |
| `backend/.python-version` | Python version pin (Railway / Nixpacks) |
| `backend/railway.json` | Railway build + deploy config |
| `render.yaml` | Render Blueprint (repo root) |

---

## Option A — Render (Recommended)

### 1. Connect your repo
1. Go to [render.com](https://render.com) → **New → Blueprint**
2. Connect your GitHub repo — Render will auto-detect `render.yaml` at the repo root
3. Click **Apply Blueprint**

### 2. Set secret environment variables
In the Render Dashboard → **roofwisebd-backend → Environment**,
add these (Render masked them so they never appear in logs):

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql://postgres.<ref>:<password>@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres` |
| `SUPABASE_URL` | `https://dopfzvcmefjpvdtefvpj.supabase.co` |
| `SUPABASE_ANON_KEY` | *(your anon key)* |
| `SUPABASE_JWT_SECRET` | *(your JWT secret)* |

> All other variables are pre-filled in `render.yaml` as non-secret values.

### 3. Deploy
Click **Deploy** — first build takes ~3 min.
Your backend URL will be: `https://roofwisebd-backend.onrender.com`

> **Free tier caveat:** Render free web services spin down after 15 min of inactivity.
> Upgrade to **Starter ($7/mo)** for always-on. Railway's free tier is similar.

---

## Option B — Railway

### 1. Connect your repo
1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
2. Select your repo; Railway auto-detects `backend/railway.json`
3. Set **Root Directory** = `backend` in Railway settings

### 2. Set environment variables
In Railway Dashboard → **Variables**, add:

| Variable | Value |
|---|---|
| `DATABASE_URL` | *(Supabase pooler URL)* |
| `SUPABASE_URL` | `https://dopfzvcmefjpvdtefvpj.supabase.co` |
| `SUPABASE_ANON_KEY` | *(your anon key)* |
| `SUPABASE_JWT_SECRET` | *(your JWT secret)* |
| `ENVIRONMENT` | `production` |
| `AUTH_MODE` | `supabase` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `none` |
| `BACKEND_CORS_ORIGINS` | `https://roofwisebd.pages.dev,https://roofwisebd.com,https://www.roofwisebd.com` |
| `BACKEND_CORS_ORIGIN_REGEX` | `^https://([a-zA-Z0-9_-]+\.)*(pages\.dev\|roofwisebd\.com)$` |
| `FRONTEND_URL` | `https://roofwisebd.pages.dev` |
| `RATE_LIMIT_FAILURE_POLICY` | `strict_quota` |
| `RATE_LIMIT_ESTIMATED_WORKERS` | `2` |

### 3. Generate a domain
In Railway → **Settings → Networking → Generate Domain**
Your backend URL: `https://roofwisebd-backend-production.up.railway.app`

---

## After Backend is Live

1. **Update frontend env var** (Cloudflare Pages Dashboard → Settings → Environment Variables):
   ```
   VITE_API_BASE_URL = https://<your-backend-url>/api/v1
   ```

2. **Update `frontend/.env.local`** for local dev (optional):
   ```
   VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
   ```
   (keep localhost for local dev; Cloudflare Pages uses the env var set in the dashboard)

3. **Verify the health endpoint** after deploy:
   ```
   curl https://<your-backend-url>/api/v1/health
   # Expected: {"status":"healthy","service":"RoofwiseBD","version":"1.0.0"}
   ```

4. **Configure Supabase Dashboard** (manual):
   - Auth → URL Configuration → Site URL: `https://roofwisebd.pages.dev`
   - Auth → URL Configuration → Redirect URLs: add `https://roofwisebd.pages.dev/auth/callback`

---

## Start Command Reference

```bash
# What Render/Railway runs:
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2

# Local dev equivalent:
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

`--workers 2` is safe for free-tier instances (512 MB RAM).
Upgrade to `--workers 4` on paid plans.
