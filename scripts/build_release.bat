@echo off
call "%~dp0launch.bat" "%~dp0build_windows.py"
set "build_result=%errorlevel%"
if "%build_result%"=="0" (
 echo EXE: dist\FileWorkbench_Next.exe
 echo ZIP: release\FileWorkbench_Next_3.3_RC_Windows_x64.zip
)
pause
exit /b %build_result%
