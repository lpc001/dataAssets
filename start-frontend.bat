@echo off
cd /d "%~dp0frontend"

if not exist "node_modules" (
  echo node_modules not found, running npm install ...
  call npm install
  if errorlevel 1 (
    echo npm install failed. Please check Node.js and network.
    pause
    exit /b 1
  )
)

echo Starting frontend on http://localhost:5173 ...
call npm run dev
echo.
echo Frontend stopped. You can close this window.
pause
