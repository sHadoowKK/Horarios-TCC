param(
    [switch]$OpenBrowser = $true
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"
$seedScript = Join-Path $backend "seed_realista.py"
$startScript = Join-Path $root "start-demo.ps1"

if (-not (Test-Path $python)) {
    throw "Python do ambiente virtual não foi encontrado. Confira se backend\.venv existe."
}
if (-not (Test-Path $seedScript)) {
    throw "Script de dados não encontrado: $seedScript. Atualize a branch antes de executar."
}
if (-not (Test-Path $startScript)) {
    throw "Inicializador de demonstração não encontrado: $startScript."
}

# Não recria o banco enquanto a API está usando os dados.
$apiListener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($apiListener) {
    throw "A API já está aberta na porta 8000. Feche as janelas atuais do Anatinus antes de recriar a base."
}

Write-Host "Criando uma base isolada somente com Informática..." -ForegroundColor Cyan
Push-Location $backend
try {
    & $python $seedScript --informatica-only
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar a base somente de Informática. O Anatinus não será iniciado."
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Base preparada: matriz do 3º INFO extraída da planilha, com aulas conjuntas e grupos A/B." -ForegroundColor Green
Write-Host "Aviso: a disponibilidade docente por dia/período é sintética; a planilha não informa esses bloqueios." -ForegroundColor Yellow

# O seed já criou o banco DEMO. Inicie sem executar novamente o seed fictício.
if ($OpenBrowser) {
    & $startScript -SkipSeed
} else {
    & $startScript -SkipSeed -OpenBrowser:$false
}
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao iniciar a demonstração."
}
