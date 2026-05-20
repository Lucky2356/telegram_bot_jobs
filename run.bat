@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%"
set PYTHONIOENCODING=utf-8

echo =============================
echo  Job Bot
echo =============================
echo [OK] Python: 
python --version

del /q vacancies.db 2>nul
del /q vacancies.db-journal 2>nul
echo [OK] Database cleaned

echo [OK] Starting bot...
echo =============================
echo  Bot is running. Open http://127.0.0.1:8000
echo  Press Ctrl+C to stop
echo =============================
python -u main.py
pause
