@echo off
REM Console launcher for DesktopPlus — shows errors (unlike double-clicking .pyw)
cd /d "%~dp0"
echo DesktopPlus debug launch
echo.
py -c "import sys; print(sys.executable); print(sys.version)"
echo.
py "%~dp0DesktopPlus.pyw"
echo.
echo Exit code: %ERRORLEVEL%
echo Log file: %~dp0desktopplus.log
pause
