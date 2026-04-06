# Deploy Backend to Render - Quick Guide

## ✅ Pre-Deployment Checklist

- [x] Code pushed to GitHub: `Ananyanagaraj11/ai-cyber-threat-dashboard`
- [x] `render.yaml` configured correctly
- [x] `backend/artifacts/` contains model files (model.pt, scaler.joblib, classes.pt, feature_names.txt)
- [x] `requirements.txt` has all dependencies

## 🚀 Deployment Steps

### 1. Go to Render
👉 https://render.com → Sign up/Login (use GitHub)

### 2. Create Web Service
- Click **"New +"** → **"Web Service"**
- Connect GitHub repo: `Ananyanagaraj11/ai-cyber-threat-dashboard`
- Render will auto-detect `render.yaml` ✅

### 3. Verify Settings (Auto-filled from render.yaml)
- **Name:** `cyber-threat-backend`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`

### 4. Deploy
- Click **"Create Web Service"**
- Wait ~5-7 minutes for first deployment
- Watch build logs for progress

### 5. Copy Backend URL
After deployment, copy your URL:
```
https://cyber-threat-backend-xxxx.onrender.com
```

### 6. Update Frontend Config
Once you have the Render URL, update `dashboard/js/config.js`:
```javascript
window.ENV_API_BASE = "https://your-backend-url.onrender.com";
```

Then push to GitHub → Vercel auto-redeploys ✅

---

## 📋 Render Free Tier Notes

- **Spins down** after 15 minutes of inactivity
- **Cold start** takes ~30 seconds on first request after spin-down
- **Always-on** available on paid plans ($7/month)

---

## 🔍 Troubleshooting

### Build Fails
- Check build logs for errors
- Verify `requirements.txt` has all dependencies
- Ensure Python version is compatible

### Service Won't Start
- Check start command: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
- Verify `backend/app.py` exists
- Check health endpoint: `https://your-backend.onrender.com/health`

### Model Files Missing
- Ensure `backend/artifacts/` is committed to GitHub
- Check `.gitignore` doesn't exclude `.pt` or `.joblib` files

---

## ✅ After Deployment

1. Test backend: `https://your-backend.onrender.com/health`
2. Should return: `{"status": "healthy"}`
3. Update frontend config with Render URL
4. Push changes → Vercel redeploys
5. Test CSV upload on Vercel frontend

---

**Need help?** Check Render logs or ask for assistance!
