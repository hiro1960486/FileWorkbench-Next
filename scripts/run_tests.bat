@echo off
setlocal
set "QT_QPA_PLATFORM=offscreen"
call "%~dp0launch.bat" -m unittest discover -s tests -p "test_module*.py" -v
set "test_result=%errorlevel%"
pause
exit /b %test_result%
