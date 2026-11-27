@echo off
rem Quorum 0.3.0.005 — bench/owner test shortcut (C-LauncherTests).
rem Runs launch hygiene checks then the full 44-scenario suite.
cd /d "%~dp0"
python scripts\launch-check.py
python scripts\scenarios.py
