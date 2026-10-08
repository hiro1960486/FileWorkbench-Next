@echo off
if "%~1"=="" (
 echo Usage: run_module.bat tree^|rename^|preview^|compare^|hash^|recycle
 pause
 exit /b 1
)
call "%~dp0scripts\launch.bat" "%~dp0scripts\run_module.py" "%~1"
exit /b %errorlevel%
