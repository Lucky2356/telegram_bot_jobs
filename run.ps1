# Job Bot launcher for PowerShell / VS Code terminal
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot"

# Force correct Python
$env:PATH = "C:\Program Files\Python312;C:\Program Files\Python312\Scripts;$env:PATH"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "============================="
Write-Host "Job Bot Startup"
Write-Host "============================="
Write-Host "Python: $(python --version)"

# Kill leftover bot processes
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Clean stale DB
Remove-Item "vacancies.db", "vacancies.db-journal" -Force -ErrorAction SilentlyContinue

Write-Host "Starting bot..."
python -u main.py
