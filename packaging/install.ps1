# ============================================================
# SIMPLIFIA Installer - Windows (PowerShell)
# Usage: irm https://install.simplifia.com | iex
# 
# Installs: CLI + Setup + OpenClaw/Clawdbot Runtime (Docker)
# ============================================================

$ErrorActionPreference = "Stop"

# ============================================================
# HELPERS
# ============================================================

function Write-Header {
    Write-Host ""
    Write-Host "⚡ SIMPLIFIA Installer" -ForegroundColor Magenta
    Write-Host "   Automação sem código em 1 comando" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "▶ $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Ask-YesNo {
    param(
        [string]$Prompt,
        [string]$Default = "y"
    )
    
    if ($env:SIMPLIFIA_NONINTERACTIVE -eq "1") {
        return ($Default -eq "y")
    }
    
    $hint = if ($Default -eq "y") { "[S/n]" } else { "[s/N]" }
    $response = Read-Host "? $Prompt $hint"
    
    if ([string]::IsNullOrEmpty($response)) {
        $response = $Default
    }
    
    return ($response -match "^[SsYy]")
}

# ============================================================
# PRE-CHECKS
# ============================================================

Write-Header

Write-Success "Sistema: Windows"

# Check Python
Write-Step "Verificando Python..."

try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
            Write-Error "Python $major.$minor encontrado, mas precisa de 3.9+"
            Write-Host "  Download: https://python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Success "Python $major.$minor encontrado"
    }
} catch {
    Write-Error "Python não encontrado!"
    Write-Host ""
    Write-Host "  Download: https://python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Marque 'Add Python to PATH' durante instalação" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Check pip
try {
    pip --version | Out-Null
    Write-Success "pip disponível"
} catch {
    Write-Warning "pip não encontrado, tentando instalar..."
    try {
        python -m ensurepip --upgrade
        Write-Success "pip instalado"
    } catch {
        Write-Error "Não foi possível instalar pip"
        exit 1
    }
}

# ============================================================
# INSTALL CLI
# ============================================================

Write-Host ""
Write-Step "Instalando SIMPLIFIA CLI..."

# Check if already installed
$existingVersion = $null
try {
    $existingVersion = (simplifia --version 2>&1) -replace '.*?(\d+\.\d+\.\d+).*', '$1'
    Write-Success "SIMPLIFIA $existingVersion já instalado"
    
    if (Ask-YesNo "Atualizar para última versão?" "n") {
        $upgradeFlag = "--upgrade"
    } else {
        $upgradeFlag = $null
        Write-Success "Mantendo versão atual"
    }
} catch {
    $upgradeFlag = "--upgrade"
}

# Install/upgrade
if ($upgradeFlag -or -not $existingVersion) {
    # Install directly from GitHub (package not yet on PyPI)
    Write-Host "  Baixando do GitHub..." -ForegroundColor DarkGray
    pip install --user git+https://github.com/pala7777/simplifia-installer.git 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha na instalação via pip"
        Write-Host "  Tente manualmente:" -ForegroundColor Yellow
        Write-Host "    pip install git+https://github.com/pala7777/simplifia-installer.git" -ForegroundColor Cyan
        exit 1
    }
}

# Add Scripts to PATH if needed
# Get user scripts path from Python
$scriptsPath = $null
try {
    $userBase = (python -c "import site; print(site.USER_BASE)" 2>&1).Trim()
    if ($userBase -and (Test-Path $userBase)) {
        $scriptsPath = Join-Path $userBase "Scripts"
    }
} catch {}

# Fallback to common locations
if (-not $scriptsPath -or -not (Test-Path $scriptsPath -ErrorAction SilentlyContinue)) {
    $fallbackPaths = @(
        "$env:APPDATA\Python\Python312\Scripts",
        "$env:APPDATA\Python\Python311\Scripts",
        "$env:APPDATA\Python\Python310\Scripts",
        "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts",
        "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts"
    )
    foreach ($path in $fallbackPaths) {
        if (Test-Path $path -ErrorAction SilentlyContinue) {
            $scriptsPath = $path
            break
        }
    }
}

if ($scriptsPath -and (Test-Path $scriptsPath -ErrorAction SilentlyContinue)) {
    if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $scriptsPath })) {
        $env:PATH = "$scriptsPath;$env:PATH"
        Write-Warning "Adicionando $scriptsPath ao PATH"
        
        # Persist to user PATH
        $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        if (-not ($userPath -split ';' | Where-Object { $_ -eq $scriptsPath })) {
            [Environment]::SetEnvironmentVariable("PATH", "$scriptsPath;$userPath", "User")
            Write-Success "PATH atualizado permanentemente"
        }
    }
} else {
    Write-Warning "Scripts path não encontrado - pode ser necessário reiniciar o terminal"
}

# Verify installation
try {
    $newVersion = (simplifia --version 2>&1) -replace '.*?(\d+\.\d+\.\d+).*', '$1'
    Write-Success "SIMPLIFIA v$newVersion instalado"
} catch {
    Write-Error "Instalação falhou - 'simplifia' não encontrado"
    Write-Host "  Tente: pip install --user simplifia" -ForegroundColor Yellow
    exit 1
}

# ============================================================
# SETUP (3 perguntas modo iniciante)
# ============================================================

Write-Host ""
Write-Step "Configuração inicial..."

$configPath = "$env:USERPROFILE\.simplifia\config.json"

if (Test-Path $configPath) {
    if (Ask-YesNo "Configuração existente encontrada. Reconfigurar?" "n") {
        simplifia setup --force
    } else {
        Write-Success "Mantendo configuração atual"
    }
} else {
    if ($env:SIMPLIFIA_NONINTERACTIVE -eq "1") {
        $env:SIMPLIFIA_NONINTERACTIVE = "1"
        simplifia setup 2>&1 | Out-Null
    } else {
        simplifia setup
    }
}

# ============================================================
# RUNTIME (Docker)
# ============================================================

Write-Host ""
Write-Step "Verificando runtime OpenClaw/Clawdbot..."

# Check if runtime already installed
$runtimeInstalled = Test-Path "$env:USERPROFILE\.simplifia\clawdbot\docker-compose.yml"

if ($runtimeInstalled) {
    Write-Success "Runtime já instalado"
}

# Check Docker availability
$dockerAvailable = $false
try {
    docker info 2>&1 | Out-Null
    $dockerAvailable = $true
    Write-Success "Docker disponível"
} catch {
    try {
        docker --version 2>&1 | Out-Null
        Write-Warning "Docker instalado mas não está rodando"
        Write-Host "  Inicie o Docker Desktop" -ForegroundColor Yellow
    } catch {
        Write-Warning "Docker não instalado"
    }
}

# Ask about runtime installation
$installRuntime = $false

if ($runtimeInstalled) {
    # Check if running
    $running = (docker ps --filter "name=simplifia-clawdbot" --format "{{.Names}}" 2>&1) -match "simplifia-clawdbot"
    
    if ($running) {
        Write-Success "Runtime já está rodando"
    } else {
        if (Ask-YesNo "Iniciar runtime agora?" "y") {
            simplifia clawdbot start
        }
    }
} elseif ($dockerAvailable) {
    Write-Host ""
    Write-Host "O motor OpenClaw/Clawdbot é necessário para rodar automações." -ForegroundColor Cyan
    Write-Host "Ele roda via Docker (isolado, seguro, fácil de remover)." -ForegroundColor Cyan
    Write-Host ""
    
    if (Ask-YesNo "Instalar o motor OpenClaw/Clawdbot (Docker) agora? (recomendado)" "y") {
        $installRuntime = $true
    } else {
        Write-Warning "Runtime não instalado"
        Write-Host ""
        Write-Host "  Você pode instalar depois com:" -ForegroundColor White
        Write-Host "    simplifia clawdbot install --docker" -ForegroundColor Cyan
        Write-Host "    simplifia clawdbot start" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Nota: Packs exigem o runtime para funcionar." -ForegroundColor Yellow
    }
} else {
    Write-Warning "Docker não disponível - runtime não será instalado"
    Write-Host ""
    Write-Host "  Instale o Docker Desktop: https://docker.com/products/docker-desktop" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Depois rode:" -ForegroundColor White
    Write-Host "    simplifia clawdbot install --docker" -ForegroundColor Cyan
    Write-Host "    simplifia clawdbot start" -ForegroundColor Cyan
}

# Install runtime if requested
if ($installRuntime) {
    Write-Host ""
    Write-Step "Instalando runtime..."
    
    if ($env:SIMPLIFIA_NONINTERACTIVE -eq "1") {
        $env:SIMPLIFIA_NONINTERACTIVE = "1"
        simplifia clawdbot install --docker
    } else {
        simplifia clawdbot install --docker
    }
    
    Write-Step "Iniciando runtime..."
    $runtimeStarted = $false
    try {
        simplifia clawdbot start 2>&1 | Out-Null
        $runtimeStarted = $true
    } catch {
        Write-Warning "Não foi possível iniciar o runtime agora."
        Write-Host "  A imagem Docker será baixada no primeiro uso." -ForegroundColor Yellow
        Write-Host "  Ou inicie manualmente: simplifia clawdbot start" -ForegroundColor Cyan
    }
    
    # Health check (only if started)
    if ($runtimeStarted) {
        Write-Step "Verificando health..."
        $healthOk = $false
        
        for ($i = 1; $i -le 30; $i++) {
            $running = (docker ps --filter "name=simplifia-clawdbot" --filter "status=running" --format "{{.Names}}" 2>&1) -match "simplifia-clawdbot"
            
            if ($running) {
                $healthOk = $true
                break
            }
            
            Start-Sleep -Seconds 1
            Write-Host "." -NoNewline
        }
        Write-Host ""
        
        if ($healthOk) {
            Write-Success "Runtime iniciado e saudável!"
        } else {
            Write-Warning "Runtime iniciado mas health check pendente"
            Write-Host "  Ver logs: simplifia clawdbot logs" -ForegroundColor Cyan
        }
    }
}

# ============================================================
# POST-INSTALLATION
# ============================================================

Write-Host ""
Write-Step "Verificação final..."
simplifia doctor

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ SIMPLIFIA instalado com sucesso!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Próximos passos:" -ForegroundColor White
Write-Host ""
Write-Host "    1. Instalar um pack:"
Write-Host "       simplifia install whatsapp" -ForegroundColor Cyan
Write-Host ""
Write-Host "    2. Testar (modo seguro):"
Write-Host "       simplifia test whatsapp" -ForegroundColor Cyan
Write-Host ""
Write-Host "    3. Atualizar:"
Write-Host "       simplifia update whatsapp" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ⚠ Lembrete: A IA (LLM) é paga à parte pelo provedor" -ForegroundColor Yellow
Write-Host "    (OpenAI, Anthropic, etc). Você controla seus gastos." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Ajuda: https://simplifia.com.br/downloads" -ForegroundColor Blue
Write-Host "  Telegram: https://t.me/simplifia" -ForegroundColor Blue
Write-Host ""
Write-Host "  💡 Se 'simplifia' não for encontrado, feche e reabra o PowerShell." -ForegroundColor Yellow
Write-Host ""
