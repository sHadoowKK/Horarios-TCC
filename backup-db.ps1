$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$db = Join-Path $root "backend\school_schedule.db"
$backupDir = Join-Path $root "backups"

if (-not (Test-Path $db)) {
    throw "Banco nao encontrado em backend\school_schedule.db."
}

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$destination = Join-Path $backupDir "school_schedule_$timestamp.db"

Copy-Item $db $destination

Write-Host ""
Write-Host "Backup criado:" -ForegroundColor Green
Write-Host $destination
Write-Host ""
Write-Host "A pasta backups/ nao e enviada ao GitHub." -ForegroundColor Yellow
