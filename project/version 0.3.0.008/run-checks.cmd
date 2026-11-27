@echo off
rem run-checks — phase-0/1/2/3 harness driver.
rem   run-checks.cmd baseline|green|sabotage <mode>|launch|all
rem Modes:
rem   baseline            all-red phase-0 run (--bare)
rem   green               full suite, green count = completeness
rem   sabotage <mode>     empty-store|stub-engines|stubbed-endpoints
rem   launch              launch-check legs (clean launch evidence)
rem   all                 green, then all three sabotage passes
setlocal
cd /d "%~dp0"
set MODE=%~1
if "%MODE%"=="" set MODE=green
if /i "%MODE%"=="baseline" goto baseline
if /i "%MODE%"=="green" goto green
if /i "%MODE%"=="sabotage" goto sabotage
if /i "%MODE%"=="launch" goto launch
if /i "%MODE%"=="all" goto all
echo usage: run-checks.cmd baseline^|green^|sabotage ^<mode^>^|launch^|all
exit /b 2
:baseline
python -X utf8 scripts\run-suite.py --baseline
goto done
:green
python -X utf8 scripts\run-suite.py --green
goto done
:sabotage
python -X utf8 scripts\run-suite.py --sabotage %~2
goto done
:launch
python -X utf8 scripts\launch-check.py
goto done
:all
python -X utf8 scripts\run-suite.py --green
python -X utf8 scripts\run-suite.py --sabotage empty-store
python -X utf8 scripts\run-suite.py --sabotage stub-engines
python -X utf8 scripts\run-suite.py --sabotage stubbed-endpoints
goto done
:done
endlocal
