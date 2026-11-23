@echo off
cd /d "%~dp0backend"
echo Starting backend on http://localhost:8000 ...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Backend stopped. You can close this window.
pause
