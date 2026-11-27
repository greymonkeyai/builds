@echo off
rem hearth launcher — launches the app like an installed program.
rem Launch hygiene: refuses to claim a port another instance owns.
setlocal
set PORT=%~1
if "%PORT%"=="" set PORT=9540
set DATA=%~2
if "%DATA%"=="" set DATA=%~dp0runtime\default
cd /d "%~dp0"
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:%PORT%/api/health 2>nul | findstr /b "200" >nul
if %errorlevel%==0 (
    echo hearth already running on port %PORT% — not launching a second owner.
    start "" http://127.0.0.1:%PORT%/
    exit /b 0
)
if not exist "%DATA%" mkdir "%DATA%"
start "hearth" /min python -m hearth --port %PORT% --data "%DATA%"
echo waiting for readiness gate...
:wait
curl -s -o nul http://127.0.0.1:%PORT%/api/health 2>nul
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak >nul
    goto wait
)
start "" http://127.0.0.1:%PORT%/
echo hearth up on http://127.0.0.1:%PORT%/
endlocal
