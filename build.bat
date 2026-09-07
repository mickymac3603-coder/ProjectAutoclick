@echo off
echo ========================================
echo  AutoClicker - Build to .exe
echo ========================================
echo.
echo [1/2] Installing dependencies...
py -m pip install pynput pyinstaller
echo.
echo [2/2] Building .exe...
py -m PyInstaller --onefile --windowed --name AutoClicker --clean main.py
echo.
echo Done! Find your .exe at: dist\AutoClicker.exe
pause
