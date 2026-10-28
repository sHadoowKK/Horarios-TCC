param(
    [ValidateSet("Auto", "Desktop", "Development")]
    [string]$Source = "Auto"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupDir = Join-Path $root "backups"
$developmentDb = Join-Path $root "backend\school_schedule.db"

$localAppData = $env:LOCALAPPDATA
if ([string]::IsNullOrWhiteSpace($localAppData)) {
    $localAppData = Join-Path $HOME "AppData\Local"
}
$desktopDb = Join-Path $localAppData "Anatinus\school_schedule.db"

switch ($Source) {
    "Desktop" {
        $db = $desktopDb
    }
    "Development" {
        $db = $developmentDb
    }
    default {
        if (Test-Path $desktopDb) {
            $db = $desktopDb
        } else {
            $db = $developmentDb
        }
    }
}

if (-not (Test-Path $db)) {
    throw "Banco não encontrado: $db. Use -Source Desktop ou -Source Development para selecionar o banco desejado."
}

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$destination = Join-Path $backupDir "school_schedule_$timestamp.db"

Copy-Item $db $destination

Write-Host ""
Write-Host "Backup criado:" -ForegroundColor Green
Write-Host $destination
Write-Host "Origem: $db"
Write-Host ""
Write-Host "A pasta backups/ não é enviada ao GitHub." -ForegroundColor Yellow
