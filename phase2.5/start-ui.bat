@echo off
echo Starting Rika Atlas Dashboard UI...
echo ==================================
cd ui
echo.
echo Installing dependencies if needed...
call npm install
echo.
echo Starting development server...
echo UI will be available at:
echo   http://localhost:5173
echo   http://127.0.0.1:5173
echo.
call npm run dev
pause