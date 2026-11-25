@echo off
setlocal
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "IDEA Standards Helper" ^
  --icon "app_icon.ico" ^
  --add-data "standards.lsp;." ^
  --add-data "app_icon.ico;." ^
  app.py
echo.
echo Done. The .exe is in the "dist" folder.
pause
