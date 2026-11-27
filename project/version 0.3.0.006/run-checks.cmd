@echo off
rem chorus — run launch-check then the full 71-scenario suite.
cd /d "%~dp0"
python scripts\run-suite.py
