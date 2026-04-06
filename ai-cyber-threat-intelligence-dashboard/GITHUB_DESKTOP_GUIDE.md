# Push Code Using GitHub Desktop

## Step-by-Step Guide

### 1. Download & Install GitHub Desktop
- Go to: https://desktop.github.com/
- Click "Download for Windows"
- Run the installer
- Sign in with your GitHub account (Ananyanagaraj11)

### 2. Add Your Local Repository

1. Open GitHub Desktop
2. Click **File** → **Add Local Repository**
3. Click **Choose...**
4. Navigate to:
   ```
   C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard
   ```
5. Click **Add repository**

### 3. Connect to Your GitHub Repo

GitHub Desktop will show:
- **"This directory does not appear to be a Git repository"** → Click **"create a repository"**
- Or if it detects files → It will show "Publish repository" button

**If you see "Publish repository":**
- Click it
- Make sure:
  - **Owner:** Ananyanagaraj11
  - **Name:** ai-cyber-threat-dashboard
  - **Description:** 🛡️ AI-powered cyber threat intelligence dashboard with real-time attack detection, ML classification, and interactive SOC-style visualization. Built with PyTorch, FastAPI, and Plotly.
  - **Keep this code private:** Unchecked (for public repo)
- Click **"Publish repository"**

**If repo already exists:**
- GitHub Desktop will ask to connect to existing repo
- Select: `Ananyanagaraj11/ai-cyber-threat-dashboard`
- Click **"Connect"**

### 4. Commit & Push

1. You'll see all your files in the left panel under **"Changes"**
2. At the bottom, write commit message:
   ```
   Complete AI Cyber Threat Intelligence Dashboard - ML model, FastAPI backend, interactive dashboard, CSV analysis, deployment configs
   ```
3. Click **"Commit to main"** (bottom left)
4. Click **"Push origin"** (top toolbar, or "Publish branch" if first time)

### 5. Verify

- Go to: https://github.com/Ananyanagaraj11/ai-cyber-threat-dashboard
- You should see all folders: `backend/`, `dashboard/`, `training/`, `scripts/`, etc.

### 6. Next: Deploy

After code is pushed, follow **DEPLOY.md** to:
- Deploy backend to Render
- Deploy frontend to Vercel
- Get your live demo URL

---

## Troubleshooting

**"Repository already exists" error:**
- GitHub Desktop → Repository → Repository Settings → Remote
- Set remote URL to: `https://github.com/Ananyanagaraj11/ai-cyber-threat-dashboard.git`

**"Authentication failed":**
- GitHub Desktop → File → Options → Accounts
- Sign out and sign back in

**Files not showing:**
- Make sure you're in the correct folder
- Check that `.gitignore` isn't excluding important files
