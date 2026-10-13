@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Python environment not found. Follow docs\DEMO_GUIDE.md to install the dependencies first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" start_demo.py
pause
