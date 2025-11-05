@echo off
echo ========================================
echo SmartOrder PRO - Diagnostic Intelligent
echo by MAIGA ABOUBAKR - SAFELOGIC
echo ========================================
echo.

REM Essayer Python depuis venv
if exist "venv\Scripts\python.exe" (
    echo [INFO] Using Python from venv...
    venv\Scripts\python.exe tools\diagnostic_intelligent.py
    goto :end
)

REM Essayer python3
where python3 >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Using python3...
    python3 tools\diagnostic_intelligent.py
    goto :end
)

REM Essayer python
where python >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Using python...
    python tools\diagnostic_intelligent.py
    goto :end
)

REM Si aucun Python trouvé
echo [ERROR] Python not found!
echo Please install Python 3.10+ or activate virtual environment
exit /b 1

:end
echo.
echo ========================================
echo Diagnostic terminé!
echo Consultez les rapports dans logs/
echo ========================================
pause
