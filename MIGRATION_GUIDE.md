# RoofwiseBD — Supabase Auth Migration: Production Deployment Guide

## Overview
This guide documents the exact steps to cut over from custom JWT auth to Supabase Auth in production.
Every step requires explicit operator action. No step executes automatically.

## Pre-flight Checklist
- [ ] Supabase project is live: `https://dopfzvcmefjpvdtefvpj.supabase.co`
- [ ] Admin account exists in `public.users`: `admin@roofwisebd.com`
- [ ] `SUPABASE_JWT_SECRET` retrieved from Supabase Dashboard > Settings > API > JWT Secret
- [ ] `SUPABASE_ANON_KEY` retrieved from Supabase Dashboard > Settings > API > Project API keys > anon public
- [ ] `SUPABASE_SERVICE_ROLE_KEY` retrieved and stored securely (never committed to git)
- [ ] Local test of `migrate_admin_to_supabase_auth.py --dry-run` passes
- [ ] Backend tests pass with `AUTH_MODE=legacy`
- [ ] Frontend builds clean with `npm run build`
- [ ] Staging environment tested end-to-end (optional but recommended)

## Step 1: Apply Alembic Migration to Production DB
**OPERATOR ACTION REQUIRED — executes SQL against production**

```bash
export DATABASE_URL="postgresql+psycopg[binary]://postgres.dopfzvcmefjpvdtefvpj:<password>@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
cd backend
python -m alembic upgrade head
```

Verifies: `auth_user_id` column added to `public.users`, `hashed_password` made nullable.

## Step 2: Configure Supabase Auth Settings
In Supabase Dashboard:
- Site URL: `https://roofwisebd.com`
- Redirect URLs: `https://roofwisebd.com/reset-password` (for password reset)
- Email confirmation: Enable for new registrations (recommended)
- Password min length: 8

## Step 3: Migrate Admin Account
**OPERATOR ACTION REQUIRED — creates Supabase auth user**

```bash
export SUPABASE_URL="https://dopfzvcmefjpvdtefvpj.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<service-role-key>"
export DATABASE_URL="postgresql+psycopg[binary]://postgres.dopfzvcmefjpvdtefvpj:<password>@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
python scripts/migrate_admin_to_supabase_auth.py --dry-run  # Inspect first
python scripts/migrate_admin_to_supabase_auth.py             # Execute
```

Expected output: "Migration complete." with the linked auth_user_id UUID.

## Step 4: Verify Admin Account
Test admin login via Supabase Auth (use Supabase Dashboard or curl):
- POST `https://dopfzvcmefjpvdtefvpj.supabase.co/auth/v1/token?grant_type=password`
- Body: `{"email": "admin@roofwisebd.com", "password": "<admin-password>"}`
- Expected: 200 with access_token

## Step 5: Deploy Backend with Supabase Mode
On Render, set environment variables:
```
AUTH_MODE=supabase
SUPABASE_URL=https://dopfzvcmefjpvdtefvpj.supabase.co
SUPABASE_JWT_SECRET=<from-supabase-dashboard>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
COOKIE_SECURE=true
BACKEND_CORS_ORIGINS=https://roofwisebd.com,https://www.roofwisebd.com
FRONTEND_URL=https://roofwisebd.com
```

Deploy the updated backend. The FastAPI server will now verify Supabase JWTs.

## Step 6: Deploy Frontend with Supabase SDK
On Cloudflare Pages, set build environment variables:
```
VITE_SUPABASE_URL=https://dopfzvcmefjpvdtefvpj.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-key>
VITE_API_BASE_URL=https://your-render-backend.onrender.com/api/v1
```

Deploy the updated frontend.

## Step 7: End-to-End Verification
- [ ] Admin login works at `/admin/login`
- [ ] Regular user registration works at `/register`
- [ ] Regular user login works at `/login`
- [ ] Password reset email is sent
- [ ] Guest assessment creates and returns claim token
- [ ] Guest assessment claim after login works
- [ ] Admin can deactivate users (is_active enforcement)

## Rollback Plan
If migration fails:
1. Revert backend env: set `AUTH_MODE=legacy`, redeploy
2. Revert frontend to previous deploy in Cloudflare Pages
3. The `auth_user_id` column is nullable and additive — legacy auth continues to work
4. The Alembic migration can be downgraded: `python -m alembic downgrade a5764b316a82`

## Security Notes
- Existing sessions (UserSession table) are invalidated automatically in Supabase mode
- Supabase tokens have configurable expiry (default 1h access token, 7d refresh token)
- Admin deactivation (is_active=False) is enforced in FastAPI on every request
- CSRF protection is not needed for Bearer token auth (Bearer tokens are CSRF-immune)
- XSS risk: Supabase SDK stores tokens in localStorage. Mitigate with CSP headers.
