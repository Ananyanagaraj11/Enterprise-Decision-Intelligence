# GitHub Setup & Deployment

Quick guide to push to GitHub and deploy for a live demo URL.

---

## Push to GitHub

```bash
# From project folder
git init
git add .
git commit -m "AI Cyber Threat Intelligence Dashboard - Ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

**Important:** Make sure `backend/artifacts/` (model files) are committed. If they're large, consider Git LFS or hosting them separately.

---

## Deploy Options

### Option A: Vercel (Frontend) + Render (Backend) - Recommended

**Best for:** Professional demo URL like `https://your-app.vercel.app`

1. **Backend (Render):**
   - Go to https://render.com → New Web Service
   - Connect GitHub repo
   - Use `render.yaml` (already in repo) or set:
     - Build: `pip install -r requirements.txt`
     - Start: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
   - Copy backend URL: `https://your-backend.onrender.com`

2. **Frontend (Vercel):**
   - Go to https://vercel.com → Import GitHub repo
   - Framework: Other
   - Root: (blank)
   - Output: `dashboard`
   - **After deploy:** Edit `dashboard/js/config.js` in GitHub, set:
     ```javascript
     window.ENV_API_BASE = 'https://your-backend.onrender.com';
     ```
   - Push → Vercel auto-redeploys

3. **Your live URL:** `https://your-repo-name.vercel.app`

---

### Option B: Streamlit Cloud (Simplest)

**Best for:** Quick deployment, one service

1. Push to GitHub (above)

2. Go to https://share.streamlit.io → Sign in with GitHub

3. New app:
   - Repo: your repo
   - Main file: `dashboard/streamlit_app.py` (if it exists)
   - Python version: 3.11

4. Deploy → URL: `https://your-app.streamlit.app`

**Note:** If `streamlit_app.py` doesn't exist, use Option A (Vercel + Render).

---

## After Deployment

- **Vercel URL:** Share this in LinkedIn (cleanest)
- **Backend URL:** Keep private or document in README
- **Update config.js:** Set `window.ENV_API_BASE` to your Render backend URL

---

## Troubleshooting

- **CORS errors:** Backend already has `allow_origins=["*"]` - should work
- **Model not loading:** Ensure `backend/artifacts/` is in GitHub
- **Cold starts:** Render free tier spins down after 15 min (first request takes ~30s)
