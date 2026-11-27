@echo off
rem Run Quorum IN PLACE from the removable seed medium (C-UsbSeed).
rem Usage on any machine:  launch-seed.cmd   (from the seed folder)
set SEEDPORT=9791
cd /d "%~dp0"
python -m quorum --port %SEEDPORT% --runtime "%~dp0seed-run" --seed-media "%~dp0" --no-browser
