@echo off
title Rocksmith - restore RSMods
cd /d "%~dp0"
if exist xinput1_3.dll.off (
  ren xinput1_3.dll.off xinput1_3.dll
  echo RSMods restored.
) else (
  echo RSMods is already active.
)
timeout /t 3 >nul
