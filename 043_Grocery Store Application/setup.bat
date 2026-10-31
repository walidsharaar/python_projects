@echo off
rem One-time setup: virtual environment, packages, .env and database.
setlocal
cd /d "%~dp0"

echo [1/4] Creating virtual environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv || goto :error
)

echo [2/4] Installing packages...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || goto :error

echo [3/4] Checking .env...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo Created .env from .env.example.
    echo Open .env, replace "change-me" in DATABASE_URL with a password of your choice,
    echo save it and run setup.bat again.
    goto :end
)

echo [4/4] Creating database user, database, tables and sample data...
cd backend
"..\.venv\Scripts\python.exe" init_db.py --create-db --seed || goto :error

echo.
echo Setup complete. Start the app with run.bat
goto :end

:error
echo.
echo Setup failed - see the message above.
pause
exit /b 1

:end
pause
