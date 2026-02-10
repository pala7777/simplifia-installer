# SIMPLIFIA Installer - Windows (PowerShell)
# Usage: irm https://install.simplifia.com | iex

$ErrorActionPreference = "Stop"

Write-Host "🚀 Instalando SIMPLIFIA..." -ForegroundColor Cyan

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "✓ $pyVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado. Instale Python 3.9+ primeiro." -ForegroundColor Red
    Write-Host "   Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check pip
try {
    pip --version | Out-Null
    Write-Host "✓ pip encontrado" -ForegroundColor Green
} catch {
    Write-Host "⚠ pip não encontrado, tentando instalar..." -ForegroundColor Yellow
    python -m ensurepip --upgrade
}

# Install simplifia
Write-Host "📦 Instalando simplifia via pip..." -ForegroundColor Cyan
try {
    pip install --user --upgrade simplifia
} catch {
    Write-Host "Tentando instalação via GitHub..." -ForegroundColor Yellow
    pip install --user --upgrade git+https://github.com/pala7777/simplifia-installer.git
}

# Check if Scripts is in PATH
$userScripts = "$env:APPDATA\Python\Python*\Scripts"
$pathDirs = $env:PATH -split ";"
$scriptsInPath = $pathDirs | Where-Object { $_ -like "*Python*Scripts*" }

if (-not $scriptsInPath) {
    Write-Host ""
    Write-Host "⚠ Adicione a pasta Scripts do Python ao PATH:" -ForegroundColor Yellow
    Write-Host "   $userScripts" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "✅ SIMPLIFIA instalado!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "  simplifia doctor            # Verificar ambiente"
Write-Host "  simplifia list              # Ver packs disponíveis"
Write-Host "  simplifia install whatsapp  # Instalar um pack"
Write-Host ""
