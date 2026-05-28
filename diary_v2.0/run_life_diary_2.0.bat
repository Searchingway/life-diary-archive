@echo off
setlocal
cd /d "%~dp0.."

set "PYTHON=pythonw"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "from PySide6.QtWebEngineWidgets import QWebEngineView" >nul 2>nul
    if not errorlevel 1 set "PYTHON=.venv\Scripts\pythonw.exe"
)

"%PYTHON%" "%~dp0launcher.pyw"
