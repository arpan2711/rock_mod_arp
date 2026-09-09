@echo off
title Rocksmith - run WITHOUT RSMods
cd /d "%~dp0"
if exist xinput1_3.dll.off (
  echo RSMods is already disabled. Launching...
) else (
  if not exist xinput1_3.dll ( echo xinput1_3.dll not found. & pause & exit /b )
  ren xinput1_3.dll xinput1_3.dll.off
  echo RSMods disabled.
)
echo.
echo Launching Rocksmith completely unmodded.
echo Try one of your downloaded songs.
echo.
echo When you are done, run:  Restore RSMods.bat
echo.
start "" Rocksmith2014.exe
timeout /t 6 >nul
