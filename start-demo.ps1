param(
    [switch]$OpenBrowser = $true,
    [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"
$demoDb = Join-Path $backend "school_schedule_demo.db"

if (-not (Test-Path $python)) {
    throw "Ambiente Python não encontrado. Execute a configuração do backend descrita no README."
}
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    throw "Dependências do frontend não encontradas. Entre em frontend e execute npm install."
}

$apiListener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($apiListener) {
    throw "A API já está aberta na porta 8000. Feche as instâncias atuais do Anatinus antes de iniciar outra demonstração."
}

if ($SkipSeed) {
    if (-not (Test-Path $demoDb)) {
        throw "Banco DEMO não encontrado: $demoDb. Execute primeiro o seed correspondente ao cenário."
    }
    Write-Host "Usando a base DEMO já preparada; nenhum cadastro será recriado." -ForegroundColor Cyan
} else {
    Write-Host "Preparando a base da planilha e gerando o horário de apresentação..." -ForegroundColor Cyan
    Push-Location $backend
    try {
        & $python (Join-Path $backend "seed_apresentacao_planilha.py")
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao criar a base de apresentação da planilha."
        }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $demoDb)) {
    throw "A base de demonstração não foi criada: $demoDb"
}

$databaseUrl = "sqlite:///" + $demoDb.Replace("\", "/")
$previousDatabaseUrl = $env:ANATINUS_DATABASE_URL
$env:ANATINUS_DATABASE_URL = $databaseUrl

$backendQuoted = $backend.Replace("'", "''")
$pythonQuoted = $python.Replace("'", "''")
$frontendQuoted = $frontend.Replace("'", "''")

$backendCommand = "Set-Location '$backendQuoted'; & '$pythonQuoted' -m uvicorn app.main:app --reload"
$frontendCommand = "Set-Location '$frontendQuoted'; npm run dev"

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
    Start-Sleep -Milliseconds 800
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand
} finally {
    if ($null -eq $previousDatabaseUrl) {
        Remove-Item Env:ANATINUS_DATABASE_URL -ErrorAction SilentlyContinue
    } else {
        $env:ANATINUS_DATABASE_URL = $previousDatabaseUrl
    }
}

Start-Sleep -Seconds 2
if ($OpenBrowser) {
    Start-Process "http://localhost:5173"
}

Write-Host ""
if ($SkipSeed) {
    Write-Host "Anatinus iniciou usando a BASE DEMO EXISTENTE." -ForegroundColor Green
} else {
    Write-Host "Anatinus iniciou usando a BASE DA PLANILHA PARA APRESENTAÇÃO." -ForegroundColor Green
}
Write-Host "Frontend: http://localhost:5173"
Write-Host "API:      http://localhost:8000"
Write-Host "Banco:    $demoDb"
Write-Host ""
if ($SkipSeed) {
    Write-Host "Os dados existentes do cenário selecionado foram preservados." -ForegroundColor Yellow
} else {
    Write-Host "Os docentes estão anonimizados; a disponibilidade é ampla e sintética." -ForegroundColor Yellow
}
Write-Host "Os dados ficam separados de backend\school_schedule.db." -ForegroundColor Yellow
