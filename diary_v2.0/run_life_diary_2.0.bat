@echo off
setlocal
cd /d "%~dp0.."

set "PYTHON=python"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "from PySide6.QtWebEngineWidgets import QWebEngineView" >nul 2>nul
    if not errorlevel 1 set "PYTHON=.venv\Scripts\python.exe"
)

"%PYTHON%" "%~dp0launcher.py"
