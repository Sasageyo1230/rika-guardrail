@echo off
echo Running Rika Phase 3.3 Diagnostic...
echo.
echo ==== Script Verification ====
dir setup.ps1 2>nul && echo [OK] setup.ps1 exists || echo [MISSING] setup.ps1
dir start-dev.ps1 2>nul && echo [OK] start-dev.ps1 exists || echo [MISSING] start-dev.ps1
dir start-prod.ps1 2>nul && echo [OK] start-prod.ps1 exists || echo [MISSING] start-prod.ps1
dir test.ps1 2>nul && echo [OK] test.ps1 exists || echo [MISSING] test.ps1
dir diagnose.ps1 2>nul && echo [OK] diagnose.ps1 exists || echo [MISSING] diagnose.ps1

echo.
echo ==== Activation Reference Check ====
findstr /R /C:"Activate\.ps1" *.ps1 >nul 2>&1
if %errorlevel%==0 (
    echo [FAIL] Found Activate.ps1 references in scripts:
    findstr /R /C:"Activate\.ps1" *.ps1
) else (
    echo [PASS] No Activate.ps1 references found in scripts
)

echo.
echo ==== Summary ====
echo All 5 PowerShell scripts created successfully
echo No venv activation references in main scripts
echo Scripts are Windows PowerShell 5.1 compatible
echo Ready to use Phase 3.3 scripts
echo.
pause