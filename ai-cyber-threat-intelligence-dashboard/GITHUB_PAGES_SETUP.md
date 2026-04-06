# Demo link using GitHub Pages (github.io)

Your demo will be live at:

**https://ananyanagaraj11.github.io/ai-cyber-threat-dashboard/**

---

## Step 1: Deploy the backend on Render (required for API)

GitHub Pages only serves static files. The dashboard needs a live backend for CSV analysis and predictions.

1. Go to **https://render.com** → Sign in with GitHub.
2. **New +** → **Web Service**.
3. Connect repo: **Ananyanagaraj11/ai-cyber-threat-dashboard**.
4. Build: `pip install -r requirements.txt`  
   Start: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
5. **Create Web Service** and wait for deploy.
6. Copy your backend URL, e.g. `https://ai-cyber-threat-dashboard-xxxx.onrender.com`.

---

## Step 2: Point the demo to your backend

1. Open **docs/js/config.js** in this repo.
2. Replace the placeholder with your Render URL:
   ```js
   window.ENV_API_BASE = "https://YOUR-ACTUAL-RENDER-URL.onrender.com";
   ```
3. Save the file.

---

## Step 3: Enable GitHub Pages

1. On GitHub, open **Ananyanagaraj11/ai-cyber-threat-dashboard**.
2. Go to **Settings** → **Pages** (left sidebar).
3. Under **Build and deployment**:
   - **Source:** Deploy from a branch
   - **Branch:** `main`
   - **Folder:** `/docs`
4. Click **Save**.
5. Wait 1–2 minutes. GitHub will build and publish the site.

---

## Step 4: Push the updated config (if you changed docs/js/config.js)

From your project folder:

```bash
git add docs/
git commit -m "Add GitHub Pages site and set backend URL"
git push origin main
```

After the push, GitHub Pages will redeploy with your backend URL.

---

## Your demo link

**https://ananyanagaraj11.github.io/ai-cyber-threat-dashboard/**

Share this link. It will load the dashboard from GitHub Pages and call your Render backend for predictions and CSV analysis.

**Note:** Render free tier may sleep after 15 minutes of inactivity; the first request after that can take ~30 seconds.
