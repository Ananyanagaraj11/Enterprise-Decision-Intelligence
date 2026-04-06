# Live demo in 2 steps

## 1. Deploy the backend (Render, free)

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. **New** → **Web Service**.
3. Connect repo: `Ananyanagaraj11/ai-cyber-threat-dashboard`.
4. Use these settings:
   - **Name:** `cyber-threat-backend` (so the URL is `https://cyber-threat-backend.onrender.com`)
   - **Environment:** Python 3
   - **Build command:** `pip install -r requirements-render.txt`
   - **Start command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** Free
5. Click **Create Web Service**. Wait for the first deploy (can take 10–20 min for PyTorch).
6. Copy the service URL (e.g. `https://cyber-threat-backend.onrender.com`). If you used a different name, copy that URL.

## 2. Point the frontend at the backend

- **Vercel:** In your Vercel project → **Settings** → **Environment Variables** → add `API_URL` = your Render URL (e.g. `https://cyber-threat-backend.onrender.com`). Then **Redeploy** the latest deployment.
- **GitHub Pages:** If your backend URL is different from `https://cyber-threat-backend.onrender.com`, edit `docs/js/config.js` and set `ENV_API_BASE` to that URL, then push.

If you kept the backend name `cyber-threat-backend`, the frontend is already configured to use that URL and you only need to redeploy Vercel (or do nothing for GitHub Pages) after the backend is live.

---

**Result:** Your Vercel (and GitHub Pages) site will call the Render backend; **CSV Analysis** and **Dashboard** will work as a live demo. Full dataset analyzed (no file or row limits).
