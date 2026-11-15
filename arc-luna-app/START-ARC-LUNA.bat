@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   ARC LUNA - LUNASIGHT
echo ==========================================
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python was not found. Install Python 3.10 or newer, then run this file again.
    pause
    exit /b 1
  )
  set "PY=python"
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating project environment...
  %PY% -m venv .venv
  if errorlevel 1 goto failed
)
echo Installing required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Starting ARC LUNA at http://127.0.0.1:8000
start "" http://127.0.0.1:8000
".venv\Scripts\python.exe" app.py
goto end
:failed
echo Setup failed. Check your Python installation and internet connection.
pause
:end
endlocal
