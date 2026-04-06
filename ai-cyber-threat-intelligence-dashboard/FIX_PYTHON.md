# What Is Not Found and How to Fix It

## What is wrong

When you run `python`, Windows runs a **Microsoft Store stub**, not real Python. So you see "Python was not found" and the backend never starts.

Your PC has a folder `AppData\Local\Programs\Python\Python313` but **no python.exe** there. So there is no real Python to run.

---

## Fix (do both steps)

### Step 1: Turn off the Store python alias

1. Press **Win**, type **Manage app execution aliases**, press Enter.
2. Find **App Installer - python.exe** and **python3.exe** and set both to **Off**.
3. Close the window.

### Step 2: Install Python from python.org

1. Go to **https://www.python.org/downloads/**
2. Click **Download Python 3.x.x**
3. Run the installer and **check "Add python.exe to PATH"** at the bottom.
4. Click **Install Now**, then Close.

### Step 3: Use a new terminal

1. Close all terminals and Cursor (or open a new terminal).
2. Run:
   ```
   cd "c:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
   python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
   ```
3. Open in browser: **http://localhost:8000/dashboard/analysis.html**

---

## Summary

| Not found | Why |
|-----------|-----|
| Real python command | Only Store stub is in PATH; no python.exe. |
| localhost:8000 | Backend does not start because python does not run. |

After Step 1 and 2 and 3, python will work and the backend will start.
