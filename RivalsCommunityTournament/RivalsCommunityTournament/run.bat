@echo off
cd /d %~dp0
echo Checking dependencies (Pillow, for the background image and icons)...
python -m pip install --disable-pip-version-check -q -r requirements.txt
python main.py
if errorlevel 1 pause
