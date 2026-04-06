# Deploy to GitHub + Vercel + Render (Live Demo URL)

Get a **professional live demo URL** like `https://cyber-threat-demo.vercel.app` + backend at `https://cyber-threat-backend.onrender.com`.

---

## Step 1: Push to GitHub

1. **Create a new repo** on GitHub (e.g. `ai-cyber-threat-dashboard`).

2. **From project folder**, initialize and push:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: AI Cyber Threat Intelligence Dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/ai-cyber-threat-dashboard.git
   git push -u origin main
   ```

---

## Step 2: Deploy Backend to Render (Free)

1. Go to **https://render.com** → Sign up (free).

2. **New** → **Web Service**.

3. **Connect your GitHub repo** (`ai-cyber-threat-dashboard`).

4. Settings:
   - **Name:** `cyber-threat-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
   - **Root Directory:** (leave blank)

5. **Advanced** → Add environment variable:
   - `PORT` = `8000`

6. Click **Create Web Service**. Wait ~5 minutes for deploy.

7. Copy your backend URL: `https://cyber-threat-backend.onrender.com` (or similar).

---

## Step 3: Deploy Frontend to Vercel (Free)

1. Go to **https://vercel.com** → Sign up (free, use GitHub).

2. **Add New Project** → Import your GitHub repo.

3. Settings:
   - **Framework Preset:** Other
   - **Root Directory:** (leave blank)
   - **Build Command:** (leave blank - static files)
   - **Output Directory:** `dashboard`

4. **Environment Variables** (optional, for demo):
   - `NEXT_PUBLIC_API_URL` = `https://cyber-threat-backend.onrender.com`

5. Click **Deploy**. Wait ~1 minute.

6. Your live demo URL: `https://your-repo-name.vercel.app`

---

## Step 4: Update Frontend to Use Deployed Backend

After Vercel deploys, update the dashboard to call your Render backend:

1. In GitHub, edit `dashboard/js/dashboard.js` and `dashboard/js/upload.js`:
   ```javascript
   // Replace the API_BASE line with:
   const API_BASE = 'https://cyber-threat-backend.onrender.com';
   ```

2. Commit and push:
   ```bash
   git add dashboard/js/*.js
   git commit -m "Use deployed backend URL"
   git push
   ```

3. Vercel will auto-redeploy with the new backend URL.

---

## Alternative: Streamlit Cloud (Simpler, One Deployment)

If you prefer the Streamlit dashboard:

1. Push to GitHub (Step 1 above).

2. Go to **https://share.streamlit.io** → Sign in with GitHub.

3. **New app** → Select your repo → `dashboard/streamlit_app.py`.

4. **Advanced settings** → Add secrets:
   ```
   BACKEND_URL = https://cyber-threat-backend.onrender.com
   ```

5. Deploy. Your Streamlit URL: `https://your-app.streamlit.app`

---

## Your Live Demo URLs

After deployment:

- **Frontend (Vercel):** `https://your-repo-name.vercel.app`
- **Backend (Render):** `https://cyber-threat-backend.onrender.com`
- **Streamlit (optional):** `https://your-app.streamlit.app`

Share the **Vercel URL** in your LinkedIn post - it's the cleanest!

---

## Notes

- **Render free tier:** Spins down after 15 min inactivity (cold start ~30s). Upgrade for always-on.
- **Vercel:** Always-on, fast CDN, free custom domain.
- **Model artifacts:** Make sure `backend/artifacts/` is committed (or add a build step that downloads them).
