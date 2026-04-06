# Deploy frontend on Vercel (leave Render)

## 1. Deploy the dashboard on Vercel

1. Go to **[vercel.com](https://vercel.com)** → Sign in with GitHub.
2. **Add New** → **Project** → Import **Ananyanagaraj11/ai-cyber-threat-dashboard**.
3. **Configure:**
   - **Root Directory:** click Edit → set to **`dashboard`**.
   - **Framework Preset:** Other (or leave as is).
   - **Build Command:** leave empty.
   - **Output Directory:** leave empty.
4. **Environment Variables (optional):**  
   If you use another backend later, add:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend-url.com`  
   (You can then set `window.ENV_API_BASE` in `dashboard/js/config.js` from this in a small script, or just edit config.js.)
5. Click **Deploy**.

Your app will be at **https://your-project.vercel.app**.

---

## 2. Backend: Vercel cannot run it

The app needs a **Python backend** (FastAPI + PyTorch) for:

- `/analyze/csv`
- `/predict`
- `/api/last-analysis`
- `/health`

Vercel is for static sites and serverless; it **cannot** run this backend (PyTorch is too large for serverless limits). So you have two options:

### Option A – Backend elsewhere (recommended)

Run the backend on a host that supports Python + enough memory:

- **Railway** – [railway.app](https://railway.app) (free tier, often faster than Render).
- **Fly.io** – [fly.io](https://fly.io) (free tier).
- **Your own server or laptop** – e.g. `uvicorn backend.app:app --host 0.0.0.0 --port 8000` and use ngrok if you want a public URL.

Then:

1. Get the backend URL (e.g. `https://your-app.railway.app`).
2. In the repo, set it in **`dashboard/js/config.js`**:
   ```js
   window.ENV_API_BASE = "https://your-backend-url.com";
   ```
3. Commit and push; Vercel will redeploy and the frontend will call that backend.

### Option B – No backend (demo only)

If you only want to show the **UI** (no real CSV analysis or predictions):

- Deploy only the frontend on Vercel (steps above).
- Leave `window.ENV_API_BASE` as `null` in `config.js`.
- Buttons like “Analyze File” will fail with “Backend not reachable” unless you point them at a running backend (Option A).

---

## 3. Summary

| Part        | Where        | Notes                                      |
|------------|--------------|--------------------------------------------|
| Frontend   | **Vercel**   | Root Directory = `dashboard`, then Deploy. |
| Backend    | **Not Vercel** | Use Railway, Fly.io, or run locally.     |

After deploy, set **`dashboard/js/config.js`** (or env) to your backend URL and push so the Vercel site uses it.
