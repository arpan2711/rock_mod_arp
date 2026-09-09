@echo off
title Rocksmith Song Manager
cd /d "%~dp0"
echo Starting Rocksmith Song Manager...
echo Closing this window stops the manager.
echo.
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 server.py
) else (
  python server.py
)
if errorlevel 1 pause
