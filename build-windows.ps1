$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "Este script deve ser executado no Windows."
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python não foi encontrado. Instale Python 3.12 e marque a opção para adicioná-lo ao PATH."
}

if (-not (Get-Command node -ErrorAction SilentlyContinue) -or
    -not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js e npm não foram encontrados. Instale Node.js 22 LTS."
}

if (-not (Test-Path $venvPython)) {
    Write-Host "[1/5] Criando ambiente Python..." -ForegroundColor Cyan
    python -m venv (Join-Path $backend ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Não foi possível criar o ambiente Python." }
}

Write-Host "[2/5] Instalando dependências do backend e do empacotamento..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar pip." }

& $venvPython -m pip install -r (Join-Path $backend "requirements-desktop.txt")
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências Python." }

Write-Host "[3/5] Instalando dependências e compilando o frontend..." -ForegroundColor Cyan
Push-Location $frontend
try {
    if (Test-Path "package-lock.json") {
        npm ci
    } else {
        npm install
    }
    if ($LASTEXITCODE -ne 0) { throw "npm falhou ao instalar as dependências." }

    npm run build
    if ($LASTEXITCODE -ne 0) { throw "O build do frontend falhou." }
} finally {
    Pop-Location
}

Write-Host "[4/5] Executando testes automatizados do backend..." -ForegroundColor Cyan
Push-Location $backend
try {
    & $venvPython -m unittest discover -p "test_*.py"
    if ($LASTEXITCODE -ne 0) { throw "Os testes do backend falharam; o EXE não será empacotado." }

    $buildArgs = @(
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name", "Anatinus",
        "--distpath", (Join-Path $root "dist"),
        "--workpath", (Join-Path $root "build\pyinstaller"),
        "--specpath", (Join-Path $root "build\spec"),
        "--paths", $backend,
        "--add-data", "$frontend\dist;frontend_dist",
        "--collect-all", "ortools",
        "--collect-all", "webview",
        "--collect-all", "pythonnet",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "uvicorn.lifespan.off",
        "app\desktop.py"
    )

    Write-Host "[5/5] Empacotando Anatinus.exe..." -ForegroundColor Cyan
    & $venvPython -m PyInstaller @buildArgs
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou ao gerar o executável." }
} finally {
    Pop-Location
}

$appDirectory = Join-Path $root "dist\Anatinus"
$exePath = Join-Path $appDirectory "Anatinus.exe"
if (-not (Test-Path $exePath)) {
    throw "O empacotamento terminou sem encontrar dist\Anatinus\Anatinus.exe."
}

$releaseDirectory = Join-Path $root "release"
New-Item -ItemType Directory -Path $releaseDirectory -Force | Out-Null
$archivePath = Join-Path $releaseDirectory "Anatinus-Windows-x64.zip"
if (Test-Path $archivePath) { Remove-Item $archivePath -Force }
Compress-Archive -Path (Join-Path $appDirectory "*") -DestinationPath $archivePath -CompressionLevel Optimal

Write-Host ""
Write-Host "SUCESSO: pacote desktop criado." -ForegroundColor Green
Write-Host "Executável: $exePath"
Write-Host "Pacote:     $archivePath"
Write-Host "Extraia o ZIP inteiro e abra Anatinus.exe. Não mova o EXE sozinho."
