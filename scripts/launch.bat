@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\src"
if exist ".venv\Scripts\python.exe" (
 ".venv\Scripts\python.exe" %*
 goto result
)
where py >nul 2>&1
if not errorlevel 1 (
 py -3 %*
 goto result
)
where python >nul 2>&1
if not errorlevel 1 (
 python %*
 goto result
)
echo [ERROR] Python not found.
pause
exit /b 1
:result
set "launch_result=%errorlevel%"
if not "%launch_result%"=="0" (
 echo [ERROR] Exit code: %launch_result%
 pause
)
exit /b %launch_result%
