@echo off
rem chorus seed — run in place from removable media.
rem Writes the courier seed-log on this medium; asks before staging locally.
cd /d "%~dp0"
python -m chorus --seed %*
