# Git Setup & First Push — RoofwiseBD

## Step 1 — Install Git for Windows

Download and install from: https://git-scm.com/download/win
- Accept all defaults during install
- After install, **open a new PowerShell or Command Prompt window**

Verify:
```powershell
git --version
# Expected: git version 2.x.x.windows.x
```

---

## Step 2 — Configure Git identity (one-time)

```powershell
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## Step 3 — Create a GitHub repository

1. Go to https://github.com/new
2. Name it e.g. `roofwisebd-web`
3. Set to **Private** (recommended — contains production config)
4. Do NOT initialize with README/gitignore (we have our own)
5. Copy the repo URL: `https://github.com/<your-username>/roofwisebd-web.git`

---

## Step 4 — Initialize and push

Run these commands in PowerShell from the project root:

```powershell
cd "F:\RoofWiseBD Web"

# Initialize git repo
git init

# Set default branch name to main
git branch -M main

# Add GitHub remote (replace with your actual repo URL)
git remote add origin https://github.com/<your-username>/roofwisebd-web.git

# Stage everything (respects .gitignore — secrets excluded automatically)
git add .

# Verify what will be committed — check NO .env files appear
git status

# If any .env files appear in the list, run this BEFORE committing:
# git rm --cached backend/.env frontend/.env.local

# Create first commit
git commit -m "Initial commit: RoofwiseBD with Supabase auth, Render/Railway deploy config"

# Push to GitHub
git push -u origin main
```

---

## Step 5 — Verify secrets are excluded

After `git add .`, run this check:

```powershell
# Should return NO results — if any .env files show up, do NOT commit yet
git diff --cached --name-only | Select-String "\.env"
git diff --cached --name-only | Select-String "\.db"
```

If any appear, unstage them:
```powershell
git rm --cached backend/.env
git rm --cached frontend/.env.local
# etc.
```

---

## What WILL be committed (safe files)

```
backend/
  main.py
  requirements.txt
  requirements-ml.txt
  runtime.txt
  .python-version
  Procfile
  railway.json
  alembic.ini
  alembic/
  app/
  tests/
  .env.example          ← safe, contains only placeholders

frontend/
  src/
  public/
  index.html
  package.json
  vite.config.ts
  tsconfig.json
  .env.example          ← safe, contains only placeholders

render.yaml             ← safe, no secrets (sync:false for secrets)
DEPLOYMENT.md
GIT_SETUP.md
.gitignore

scripts/
  migrate_to_supabase.py
  migrate_sqlite_data_to_postgres.py
  verify_supabase_migration.py
  db_connection_helper.py
```

## What will NOT be committed (blocked by .gitignore)

```
backend/.env            ← DATABASE_URL, JWT_SECRET, etc.
frontend/.env.local     ← VITE_SUPABASE_ANON_KEY, etc.
backend/*.db            ← all SQLite files
backend/uploads/        ← user-uploaded images
node_modules/
__pycache__/
frontend/dist/
*.log
```

---

## After pushing — connect to Render

1. Go to render.com → **New → Blueprint**
2. Connect your GitHub repo
3. Render detects `render.yaml` automatically
4. Set the 4 secret env vars in Render Dashboard (DATABASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_JWT_SECRET)
5. Deploy

See `DEPLOYMENT.md` for full Render/Railway instructions.
