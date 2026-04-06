# Why "Python was not found" – and the fix

## What we checked

1. **When you type `python`, what actually runs?**  
   → **`C:\Users\anany\AppData\Local\Microsoft\WindowsApps\python.exe`**  
   That file is a **Microsoft Store stub**. It does not run Python. It only shows the message "Python was not found" and suggests the Store. So it is **not a bug in your project** – it is Windows using this stub instead of a real Python.

2. **Is real Python installed?**  
   → You have a folder `AppData\Local\Programs\Python\Python313` but **no `python.exe`** inside it (incomplete or Store-style install).  
   → You have a `.venv` in your user folder, but it points to the **missing** `Python313\python.exe`, so that venv is broken and cannot be used.

3. **Result**  
   → There is **no working Python** on PATH. The only thing that runs for `python` is the Store stub. So "not found" is expected until you fix this.

---

## The fix (do both)

### Step 1: Stop Windows from using the Store stub

1. Press **Win**, type: **`Manage app execution aliases`**, press **Enter**.
2. You will see a list of app execution aliases.
3. Find these two and turn the switch **OFF** for both:
   - **python.exe** (Publisher: App Installer)
   - **python3.exe** (Publisher: App Installer)
4. Close the window.

After this, `C:\...\WindowsApps\python.exe` will no longer be used when you type `python`.

### Step 2: Install real Python

1. Go to: **https://www.python.org/downloads/**
2. Click the yellow **Download Python 3.x.x** button.
3. Run the downloaded installer.
4. On the **first** screen, at the **bottom**, **check**: **"Add python.exe to PATH"**.
5. Click **"Install Now"** and wait until it finishes.
6. Close the installer.

This installs a real `python.exe` (e.g. in `AppData\Local\Programs\Python\Python3xx\`) and adds it to PATH.

### Step 3: Use a new terminal

1. Close **all** Command Prompt and PowerShell windows.
2. Close Cursor completely and open it again (or open a **new** terminal).
3. Run:
   ```bat
   python --version
   ```
   You should see something like `Python 3.12.x` (not "Python was not found").
4. Then run:
   ```bat
   cd "c:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
   python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
   ```

---

## Summary

| Question | Answer |
|----------|--------|
| Is it a mistake in the project? | **No.** The project and command are correct. |
| Why "not found"? | Windows runs the **Store stub** instead of real Python. |
| Why not use your .venv? | That venv points to a **missing** Python313, so it is broken. |
| What to do? | Turn off the **python.exe / python3.exe** app execution aliases, then **install Python from python.org** and add it to PATH. Then use a **new** terminal. |

After Step 1 and 2, "Python was not found" will stop and `python` will run the real Python you installed.
