@echo off
rem Vantage — launches the local installation like an installed program.
cd /d "%~dp0"
python -m app --port 9770 --open %*
