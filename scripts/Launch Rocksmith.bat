@echo off
title Launch Rocksmith
cd /d "%~dp0"
echo Launching Rocksmith...
start "" Rocksmith2014.exe
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 "SongManager\uplay_skip.py"
) else (
  python "SongManager\uplay_skip.py"
)
