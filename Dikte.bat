@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo Sanal ortam bulunamadi.
    echo Once su komutu calistir:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" -m dikte
