# Setup Without Installing Python on Your System

If you get **"Python was not found"** or **Microsoft Store** opens, use **portable Python** instead. It downloads Python into the project folder and does not touch your system.

## One-time setup

1. Open Command Prompt or PowerShell.
2. Go to the project folder:
   ```cmd
   cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
   ```
3. Run:
   ```cmd
   scripts\install_portable_python.bat
   ```
4. Wait for the download and install (internet required). When it finishes, you will have a `python_portable` folder in the project.

## Run the app

- **API (Terminal 1):** `scripts\run_backend.bat`
- **Dashboard (Terminal 2):** `scripts\run_dashboard.bat`

## Train a model (after you have a dataset CSV)

```cmd
scripts\run_train.bat data\your_file.csv
```

Then copy artifacts and run backend/dashboard:

```cmd
scripts\copy_artifacts.bat
scripts\run_backend.bat
```
(In another window: `scripts\run_dashboard.bat`)

No need to install Python system-wide or change Windows settings.
