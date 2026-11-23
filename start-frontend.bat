@echo off
cd /d "%~dp0frontend"
echo Starting frontend on http://localhost:5173 ...
npm run dev
echo.
echo Frontend stopped. You can close this window.
pause
