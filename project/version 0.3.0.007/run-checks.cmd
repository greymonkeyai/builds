@echo off
rem run-checks.cmd — runs the phase-0 suite: baseline -> green -> sabotage.
setlocal
cd /d "%~dp0"
python scripts\launch-check.py
python scripts\run-suite.py --all
