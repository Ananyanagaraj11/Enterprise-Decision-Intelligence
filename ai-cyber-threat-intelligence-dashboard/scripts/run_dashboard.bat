@echo off
cd /d "%~dp0\.."
echo Starting Streamlit dashboard (browser will open)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    python -m streamlit run dashboard/streamlit_app.py
) else if exist python_portable\python.exe (
    python_portable\python.exe -m streamlit run dashboard/streamlit_app.py
) else (
    python -m streamlit run dashboard/streamlit_app.py
    if errorlevel 1 py -m streamlit run dashboard/streamlit_app.py
)
pause
