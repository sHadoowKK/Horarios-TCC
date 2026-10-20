$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Ambiente virtual nao encontrado em backend\.venv."
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "node_modules nao encontrado. Execute npm install em frontend antes." -ForegroundColor Yellow
    exit 1
}

$backendCommand = "Set-Location '$backend'; & '$python' -m uvicorn app.main:app --reload"
$frontendCommand = "Set-Location '$frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Sleep -Milliseconds 800
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host ""
Write-Host "Anatinus iniciado em dois terminais." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173"
Write-Host "API:      http://localhost:8000"
