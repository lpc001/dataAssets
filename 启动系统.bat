@echo off
title Platform Base Launcher
cd /d "%~dp0"

echo ============================================
echo    Platform Base Launcher
echo ============================================
echo.
echo Starting backend (port 8000) and frontend (port 5173)...
echo.
start "Platform-Backend-8000" cmd /k "%~dp0start-backend.bat"
start "Platform-Frontend-5173" cmd /k "%~dp0start-frontend.bat"
echo Done. Two windows opened:
echo    Backend  : http://localhost:8000
echo    Frontend : http://localhost:5173
echo.
echo Login: admin / admin123
echo Keep both windows open. Close them to stop the system.
echo.
timeout /t 10
