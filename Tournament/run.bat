@echo off
cd /d %~dp0

rem Only install the optional extras (Pillow, pygame-ce) if they're missing.
python -c "import PIL, pygame" >nul 2>nul
if errorlevel 1 (
    echo Installing Pillow and pygame-ce - one time only...
    python -m pip install --disable-pip-version-check -q -r requirements.txt
)

rem Launch with pythonw (no console window) and close this window straight away.
where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw main.py
    exit /b 0
)

rem No pythonw found - fall back to a normal launch.
python main.py
if errorlevel 1 pause
