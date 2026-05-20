@echo off
cd /d "%~dp0"
set "PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%"
echo Starting Job Bot...
python main.py
pause
