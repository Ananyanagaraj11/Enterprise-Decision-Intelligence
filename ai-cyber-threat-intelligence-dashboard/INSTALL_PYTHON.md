# Install Python on Windows

The project needs **Python 3.10 or newer**. If you see `'py' is not recognized` or `'python' is not recognized`, or **"Python was not found; run without arguments to install from the Microsoft Store"**, follow these steps.

## 0. Fix "Microsoft Store" / App alias (do this first)

Windows can redirect `python` to the Microsoft Store instead of real Python. Turn that off:

1. Press **Win**, type **Manage app execution aliases**, open it.
2. Find **App Installer - python.exe** and **App Installer - python3.exe**.
3. Set both to **Off**.

Then install Python from python.org (step 1 below). Do **not** install Python from the Microsoft Store for this project.

---

## 1. Download Python

1. Open: **https://www.python.org/downloads/**
2. Click the yellow button **Download Python 3.x.x** (e.g. 3.12 or 3.11).

## 2. Run the installer

1. Double-click the downloaded file (e.g. `python-3.12.x-amd64.exe`).
2. **Important:** On the first screen, **check the box: “Add python.exe to PATH”** (at the bottom).
3. Click **Install Now** (or **Customize** if you want to change the install location).
4. Wait for installation to finish, then click **Close**.

## 3. Use a new terminal

- **Close** any Command Prompt or PowerShell windows you had open.
- Open a **new** terminal (or Cursor’s terminal).
- This makes Windows pick up the updated PATH.

## 4. Run setup again

In the project folder run:

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
scripts\setup_windows.bat
```

Or in Cursor: open the project folder, then in the terminal run:

```cmd
scripts\setup_windows.bat
```

This will create the virtual environment and install all dependencies. After that, `run_backend.bat` and `run_dashboard.bat` will work (they use the venv’s `python`).

## 5. Check that Python is installed

Close all terminals, open a **new** one, then:

```cmd
python --version
```

You should see something like `Python 3.12.x`. If you still get “not recognized”, the PATH was not set: run the Python installer again and make sure **“Add python.exe to PATH”** is checked.
