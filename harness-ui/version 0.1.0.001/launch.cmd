@echo off
rem harness-ui 0.1.0.001 — emit once against the default builds root, then open the fleet index.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0emitter\harness-emit.ps1" -Root C:uilds -Once
start "" "file:///C:/builds/index.html"
