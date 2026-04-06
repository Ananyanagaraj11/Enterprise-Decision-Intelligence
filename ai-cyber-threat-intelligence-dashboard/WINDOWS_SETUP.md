# Windows setup – quick start

Your project is here:

```
C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard
```

## 1. Open the project folder

- In **Cursor/VS Code**: File → Open Folder → choose `New folder (2)\ai-cyber-threat-intelligence-dashboard`.
- Or in **Command Prompt**:  
  `cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"`

## 2. Install Python (required)

If you see **'py' is not recognized** or **'python' is not recognized**, Python is not installed or not on PATH. **See [INSTALL_PYTHON.md](INSTALL_PYTHON.md)** for step-by-step instructions.

If `python` or `pip` is not recognized:

1. Download Python from **https://www.python.org/downloads/** (e.g. 3.11).
2. Run the installer and **check “Add python.exe to PATH”**.
3. Close and reopen the terminal, then run the steps below using `python` and `pip`.

If you prefer not to add Python to PATH, use the **Python Launcher** instead:

- Use `py` instead of `python` (e.g. `py -m pip install -r requirements.txt`).
- The scripts in `scripts\` use `py` by default.

## 3. Create environment and install dependencies

**Option A – Double‑click script**

- Double‑click **`scripts\setup_windows.bat`**.  
  It will create a virtual environment and install packages (using `py` if available).

**Option B – Manual (in a terminal in the project folder)**

```cmd
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

(Use `python` instead of `py` if Python is on your PATH.)

## 4. Train (after you have a dataset CSV)

Place your CSV (e.g. UNSW-NB15 or CICIDS2017) in the project, e.g. in a `data` folder, then:

```cmd
venv\Scripts\activate
py training/train.py --data data/UNSW_NB15_traintest.csv --out-dir training/outputs --epochs 50
```

For a quick test with fewer rows:

```cmd
py training/train.py --data data/your_file.csv --out-dir training/outputs --max-rows 50000 --epochs 10
```

## 5. Copy artifacts to backend

```cmd
scripts\copy_artifacts.bat
```

Or manually:

```cmd
mkdir backend\artifacts 2>nul
copy training\outputs\model.pt backend\artifacts\
copy training\outputs\scaler.joblib backend\artifacts\
copy training\outputs\classes.pt backend\artifacts\
copy training\outputs\feature_names.txt backend\artifacts\
```

## 6. Run the API

```cmd
scripts\run_backend.bat
```

Or:

```cmd
venv\Scripts\activate
py -m uvicorn backend.app:app --reload --port 8000
```

Leave this window open. API will be at **http://localhost:8000**.

## 7. Run the dashboard

Open a **second** terminal in the project folder, then:

```cmd
scripts\run_dashboard.bat
```

Or:

```cmd
venv\Scripts\activate
py -m streamlit run dashboard/streamlit_app.py
```

Browser will open at **http://localhost:8501**.

---

**Summary**

| Issue | What to do |
|-------|------------|
| “Path not found” | Use full path: `cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"` |
| “Python/pip not recognized” | Install Python and check “Add to PATH”, or use `py` and `py -m pip` |
| “# not recognized” | `#` is a comment; don’t run that line. Use the `copy` and `py` commands above. |
