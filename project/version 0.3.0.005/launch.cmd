@echo off
rem Quorum 0.3.0.005 — owner launch shortcut (C-LauncherTests).
rem Env baked here; launch procedure documented in LAUNCH.md.
set QUORUM_PORT=9790
set QUORUM_RUNTIME=%~dp0runtime
cd /d "%~dp0"
python -m quorum --port %QUORUM_PORT% --runtime "%QUORUM_RUNTIME%"
