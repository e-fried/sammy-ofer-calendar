@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Refreshing the calendar now and every 24 hours. Keep this window open.
".venv\Scripts\python.exe" run_calendar.py --watch
if errorlevel 1 goto failed
exit /b 0
:failed
echo Setup or update failed. Install Python 3.10 or newer from python.org if Python is missing.
pause
exit /b 1
