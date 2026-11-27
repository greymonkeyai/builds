@echo off
rem chorus — launch like an installed program.
rem Two-part execution: partition mount + readiness gate, then surface.
cd /d "%~dp0"
python -m chorus %*
