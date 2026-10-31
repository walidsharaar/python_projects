@echo off
rem Start the Grocery Store app at http://127.0.0.1:5000/  (stop it with Ctrl+C)
cd /d "%~dp0backend"

if not exist "..\.venv\Scripts\python.exe" (
    echo The virtual environment is missing. Run setup.bat first.
    pause
    exit /b 1
)

"..\.venv\Scripts\python.exe" server.py
pause
