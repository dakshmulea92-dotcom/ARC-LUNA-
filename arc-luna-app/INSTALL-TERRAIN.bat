@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run START-ARC-LUNA.bat first to create the virtual environment.
  pause
  exit /b 1
)
echo Installing optional LOLA GeoTIFF processing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements-terrain.txt
if errorlevel 1 (
  echo Installation failed. If your Python version has no compatible Rasterio wheel,
  echo create a Python 3.12 environment and try again.
  pause
  exit /b 1
)
echo Terrain support installed.
pause
endlocal
