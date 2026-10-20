$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== ANATINUS: verificacao do projeto ===" -ForegroundColor Cyan
Write-Host ""

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/2] Testes do backend..." -ForegroundColor Yellow
Set-Location (Join-Path $root "backend")

$venvPython = Join-Path $root "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "Ambiente virtual nao encontrado em backend\.venv. Crie o venv e instale requirements.txt."
}

& $venvPython -m unittest discover -p "test_*.py"

if ($LASTEXITCODE -ne 0) {
    throw "Os testes do backend falharam."
}

Write-Host ""
Write-Host "[2/2] Build do frontend..." -ForegroundColor Yellow
Set-Location (Join-Path $root "frontend")

if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) {
    Write-Host "node_modules nao encontrado; executando npm install..."
    npm install

    if ($LASTEXITCODE -ne 0) {
        throw "npm install falhou."
    }
}

npm run build

if ($LASTEXITCODE -ne 0) {
    throw "O build do frontend falhou."
}

Set-Location $root

Write-Host ""
Write-Host "OK: backend e frontend passaram na verificacao." -ForegroundColor Green
