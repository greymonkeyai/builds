@echo off
rem launch.cmd — launches vesta like an installed program on Windows.
setlocal
cd /d "%~dp0"
if not exist "runtime" mkdir "runtime"
python -m vesta --port 9537 %*
