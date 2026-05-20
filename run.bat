@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%"

echo =============================
echo Job Bot Startup
echo =============================
echo Python path:
where python
echo.
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Check C:\Program Files\Python312\
    pause
    exit /b 1
)
echo.
echo Deleting old database (schema refresh)...
del /q vacancies.db 2>nul
del /q vacancies.db-journal 2>nul
echo.
echo Starting...
set PYTHONIOENCODING=utf-8
python -u main.py
pause
