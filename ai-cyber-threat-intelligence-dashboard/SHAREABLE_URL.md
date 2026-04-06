# Get a shareable URL for your dashboard

Your code is pushed to: **https://github.com/Ananyanagaraj11/ai-cyber-threat-dashboard**

---

## Option 1: Permanent URL (best for LinkedIn/portfolio)

Use **Vercel** (frontend) + **Render** (backend). One link works for everyone, 24/7.

### Step 1: Deploy backend on Render (free)

1. Go to **https://render.com** → Sign in with GitHub.
2. **New +** → **Web Service**.
3. Connect repo: **Ananyanagaraj11/ai-cyber-threat-dashboard**.
4. Settings (often auto-filled from `render.yaml`):
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service** and wait ~5–7 minutes.
6. Copy your backend URL, e.g. `https://ai-cyber-threat-dashboard-xxxx.onrender.com`.

### Step 2: Point frontend to your backend

1. In your project, edit **dashboard/js/config.js**.
2. Set:
   ```js
   window.ENV_API_BASE = "https://YOUR-RENDER-URL.onrender.com";
   ```
   (Use the URL from Step 1, no trailing slash.)
3. Commit and push:
   ```bash
   git add dashboard/js/config.js
   git commit -m "Use Render backend URL for shareable demo"
   git push
   ```

### Step 3: Use your Vercel URL

- If you already deployed the frontend on Vercel, it will redeploy on push.
- Your **shareable link** is your Vercel app URL, e.g.  
  **https://ai-cyber-threat-dashboard-lp87.vercel.app**

Share that link; it will use the Render backend.  
(Render free tier may sleep after 15 min; first click can take ~30 s.)

---

## Option 2: Quick one-time link (ngrok)

Good for a quick demo without deploying.

1. Start backend:
   ```bash
   cd ai-cyber-threat-intelligence-dashboard
   python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
   ```
2. In another terminal, run ngrok:
   ```bash
   ngrok http 8000
   ```
3. Copy the **https://xxxx.ngrok-free.app** URL and share it.
4. Keep both terminal windows open while you share.

---

## Summary

| Goal              | What to do                    | Share this URL                          |
|-------------------|-------------------------------|-----------------------------------------|
| Permanent, 24/7   | Render + Vercel + config.js   | Your Vercel URL (e.g. …vercel.app)      |
| Quick one-time    | Backend + ngrok on your PC    | The ngrok https URL                     |

**Repo:** https://github.com/Ananyanagaraj11/ai-cyber-threat-dashboard
