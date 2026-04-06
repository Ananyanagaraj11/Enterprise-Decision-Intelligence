# No Python in aliases – fix via PATH

On your PC there are **no Python entries** in "App execution aliases". So when you type `python`, Windows is finding **`C:\...\WindowsApps\python.exe`** because that folder is in your **PATH**, not because of an alias.

## Fix

### 1. Install Python from python.org

- Go to **https://www.python.org/downloads/**
- Download and run the installer
- **Check "Add python.exe to PATH"** (bottom of first screen)
- Click **Install Now** and finish

### 2. Check PATH order (after installing)

1. Press **Win**, type **environment variables**, open **Edit the system environment variables**.
2. Click **Environment Variables**.
3. Under **User variables**, select **Path** → **Edit**.
4. Look for these two (or similar):
   - `C:\Users\anany\AppData\Local\Programs\Python\Python3xx\` (or `Python3xx\Scripts`)
   - `C:\Users\anany\AppData\Local\Microsoft\WindowsApps`
5. If **WindowsApps** is above the **Python** folder, use **Move Up** so the **Python** folder(s) are **above** WindowsApps. Then **OK** out.

### 3. New terminal

Close all terminals and Cursor, open a new terminal, then run:

```bat
python --version
```

You should see e.g. `Python 3.12.x`. Then:

```bat
cd "c:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

---

**Summary:** The Store stub is in PATH. Install Python from python.org (with "Add to PATH") and make sure the Python path is above WindowsApps in PATH so `python` runs the real one.
