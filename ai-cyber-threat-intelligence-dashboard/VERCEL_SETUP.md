# Vercel setup (required)

This repo has a **Python/FastAPI backend** (for Render) and a **static frontend** in `dashboard/`. Vercel must deploy only the frontend.

## In Vercel project → Settings → General

1. **Framework Preset** → set to **Other** (not Python/FastAPI).
2. **Root Directory** → leave **empty** (root). The root `vercel.json` builds from `dashboard/` and sets `outputDirectory` to `dashboard`.
3. Save and **Redeploy**.

If you already set Root Directory to `dashboard`, that’s fine too — but **Framework Preset must be Other**, or the build will fail with “No fastapi entrypoint found”.
