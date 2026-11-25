@echo off
setlocal
cd /d "%~dp0"
if exist "IDEA Standards Helper.exe" (
  start "" "IDEA Standards Helper.exe"
) else (
  python "app.py"
  pause
)
