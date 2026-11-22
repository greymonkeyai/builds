@echo off
REM Meridian launcher — documented procedure in LAUNCH.md
cd /d "%~dp0"
python -m app --port 9760 --open
