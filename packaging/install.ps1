# ============================================================
# SIMPLIFIA Installer - Windows (PowerShell)
# Usage: irm https://simplifia.com.br/install.ps1 | iex
# 
# TRUE beginner path: downloads standalone .exe (no Python needed)
# Fallback: pip install if exe download fails
# ============================================================

# Fix encoding for Portuguese characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$ErrorActionPreference = "Stop"

# ============================================================
# CONFIG
# ============================================================

$SIMPLIFIA_VERSION = "v1.0.0"
$SIMPLIFIA_BIN_DIR = "$env:USERPROFILE\.simplifia\bin"
$SIMPLIFIA_EXE_URL = "https://github.com/pala7777/simplifia-installer/releases/download/$SIMPLIFIA_VERSION/simplifia-windows.exe"
$SIMPLIFIA_EXE_PATH = "$SIMPLIFIA_BIN_DIR\simplifia.exe"

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

function Add-ToPath {
    param([string]$PathToAdd)
    
    # Add to current session
    if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $PathToAdd })) {
        $env:PATH = "$PathToAdd;$env:PATH"
    }
    
    # Add to user PATH permanently
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if (-not ($userPath -split ';' | Where-Object { $_ -eq $PathToAdd })) {
        [Environment]::SetEnvironmentVariable("PATH", "$PathToAdd;$userPath", "User")
        return $true
    }
    return $false
}

# ============================================================
# MAIN INSTALLER
# ============================================================

Write-Header

Write-Success "Sistema: Windows"

# Create bin directory
if (-not (Test-Path $SIMPLIFIA_BIN_DIR)) {
    New-Item -ItemType Directory -Path $SIMPLIFIA_BIN_DIR -Force | Out-Null
}

# ============================================================
# STEP 1: Try downloading standalone executable (BEGINNER PATH)
# ============================================================

Write-Step "Baixando SIMPLIFIA..."

$exeDownloaded = $false

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    
    # Download executable
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($SIMPLIFIA_EXE_URL, $SIMPLIFIA_EXE_PATH)
    
    # Verify it works
    $testOutput = & $SIMPLIFIA_EXE_PATH --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $exeDownloaded = $true
        Write-Success "SIMPLIFIA baixado com sucesso!"
    } else {
        throw "Executable test failed"
    }
} catch {
    Write-Warning "Download do executável falhou. Tentando método alternativo..."
    
    # Remove failed download
    if (Test-Path $SIMPLIFIA_EXE_PATH) {
        Remove-Item $SIMPLIFIA_EXE_PATH -Force
    }
}

# ============================================================
# STEP 2: Fallback to pip install if exe failed
# ============================================================

if (-not $exeDownloaded) {
    Write-Step "Usando instalação via Python..."
    
    # Check Python
    $pythonAvailable = $false
    try {
        $pyVersion = python --version 2>&1
        if ($pyVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            
            if ($major -ge 3 -and $minor -ge 9) {
                $pythonAvailable = $true
                Write-Success "Python $major.$minor encontrado"
            }
        }
    } catch {}
    
    # Offer to install Python via winget
    if (-not $pythonAvailable) {
        Write-Warning "Python não encontrado!"
        
        $wingetAvailable = $false
        try {
            winget --version | Out-Null
            $wingetAvailable = $true
        } catch {}
        
        if ($wingetAvailable) {
            Write-Host ""
            Write-Host "  Posso instalar o Python automaticamente via winget." -ForegroundColor Cyan
            
            if (Ask-YesNo "Instalar Python 3.12 agora?" "y") {
                Write-Step "Instalando Python via winget..."
                winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
                
                # Refresh PATH
                $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
                
                # Verify
                try {
                    python --version | Out-Null
                    $pythonAvailable = $true
                    Write-Success "Python instalado!"
                } catch {
                    Write-Error "Instalação do Python falhou."
                    Write-Host "  Instale manualmente: https://python.org/downloads/" -ForegroundColor Yellow
                    exit 1
                }
            } else {
                Write-Host ""
                Write-Host "  Instale o Python manualmente: https://python.org/downloads/" -ForegroundColor Yellow
                Write-Host "  (Marque 'Add Python to PATH' durante instalação)" -ForegroundColor Yellow
                exit 1
            }
        } else {
            Write-Host ""
            Write-Host "  Instale o Python: https://python.org/downloads/" -ForegroundColor Yellow
            Write-Host "  (Marque 'Add Python to PATH' durante instalação)" -ForegroundColor Yellow
            exit 1
        }
    }
    
    # Install via pip
    Write-Step "Instalando via pip..."
    
    try {
        $pipOutput = pip install --user git+https://github.com/pala7777/simplifia-installer.git 2>&1
        
        # Find where pip installed it
        $pyVersion = (python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')").Trim()
        $userBase = (python -c "import site; print(site.USER_BASE)").Trim()
        $scriptsPath = Join-Path $userBase "Python$pyVersion\Scripts"
        
        if (Test-Path "$scriptsPath\simplifia.exe") {
            # Copy to our bin dir for consistency
            Copy-Item "$scriptsPath\simplifia.exe" $SIMPLIFIA_EXE_PATH -Force
            Write-Success "SIMPLIFIA instalado via pip!"
        } else {
            # Try plain Scripts path
            $scriptsPath = Join-Path $userBase "Scripts"
            if (Test-Path "$scriptsPath\simplifia.exe") {
                Copy-Item "$scriptsPath\simplifia.exe" $SIMPLIFIA_EXE_PATH -Force
                Write-Success "SIMPLIFIA instalado via pip!"
            } else {
                throw "simplifia.exe not found after pip install"
            }
        }
    } catch {
        Write-Error "Instalação falhou: $_"
        exit 1
    }
}

# ============================================================
# STEP 3: Add to PATH
# ============================================================

Write-Step "Configurando PATH..."

$pathAdded = Add-ToPath $SIMPLIFIA_BIN_DIR

if ($pathAdded) {
    Write-Success "PATH atualizado permanentemente"
} else {
    Write-Success "PATH já configurado"
}

# ============================================================
# STEP 4: Setup wizard (3 questions)
# ============================================================

Write-Host ""
Write-Step "Configuração inicial..."

$configPath = "$env:USERPROFILE\.simplifia\config.json"

if (-not (Test-Path $configPath)) {
    if ($env:SIMPLIFIA_NONINTERACTIVE -eq "1") {
        & $SIMPLIFIA_EXE_PATH setup 2>&1 | Out-Null
    } else {
        & $SIMPLIFIA_EXE_PATH setup
    }
} else {
    Write-Success "Configuração existente mantida"
}

# ============================================================
# STEP 5: Runtime (Docker) - if available
# ============================================================

Write-Host ""
Write-Step "Verificando runtime Docker..."

$dockerAvailable = $false
$imageExists = $false
$dockerImage = "ghcr.io/pala7777/simplifia-clawdbot:latest"

try {
    docker info 2>&1 | Out-Null
    $dockerAvailable = $true
    Write-Success "Docker disponível"
    
    # Check if image exists
    $manifestCheck = docker manifest inspect $dockerImage 2>&1
    if ($LASTEXITCODE -eq 0) {
        $imageExists = $true
        Write-Success "Imagem Docker disponível"
    }
} catch {
    Write-Warning "Docker não disponível"
}

if ($dockerAvailable -and $imageExists) {
    Write-Host ""
    Write-Host "O motor OpenClaw/Clawdbot é necessário para rodar automações." -ForegroundColor Cyan
    
    if (Ask-YesNo "Instalar o runtime agora? (recomendado)" "y") {
        Write-Step "Instalando runtime..."
        & $SIMPLIFIA_EXE_PATH clawdbot install --docker
        & $SIMPLIFIA_EXE_PATH clawdbot start
    }
} elseif (-not $dockerAvailable) {
    Write-Host ""
    Write-Host "  💡 Para rodar automações, instale o Docker Desktop:" -ForegroundColor Yellow
    Write-Host "     https://docker.com/products/docker-desktop" -ForegroundColor Cyan
}

# ============================================================
# STEP 6: Success check (REQUIRED)
# ============================================================

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Verificação Final" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Test 1: Version
Write-Step "Testando simplifia --version..."
try {
    $versionOutput = & $SIMPLIFIA_EXE_PATH --version 2>&1
    Write-Host "  $versionOutput" -ForegroundColor Green
} catch {
    Write-Error "FALHA: simplifia --version não funciona"
    exit 1
}

# Test 2: Doctor
Write-Host ""
Write-Step "Testando simplifia doctor..."
& $SIMPLIFIA_EXE_PATH doctor

# ============================================================
# SUCCESS MESSAGE
# ============================================================

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ SIMPLIFIA instalado com sucesso!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Próximo passo:" -ForegroundColor White
Write-Host ""
Write-Host "    simplifia install whatsapp" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Outros comandos:" -ForegroundColor White
Write-Host "    simplifia list        → Ver packs disponíveis" -ForegroundColor DarkGray
Write-Host "    simplifia doctor      → Verificar ambiente" -ForegroundColor DarkGray
Write-Host "    simplifia --help      → Ajuda completa" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  ⚠ Lembrete: A IA (LLM) é paga à parte pelo provedor" -ForegroundColor Yellow
Write-Host "    (OpenAI, Anthropic, etc). Você controla seus gastos." -ForegroundColor Yellow
Write-Host ""
Write-Host "  📚 Ajuda: https://simplifia.com.br/downloads" -ForegroundColor Blue
Write-Host "  💬 Telegram: https://t.me/simplifia" -ForegroundColor Blue
Write-Host ""
Write-Host "  🛡️ Antivirus bloqueou? E normal para .exe novos." -ForegroundColor DarkGray
Write-Host "     Clique 'Mais opcoes' > 'Permitir' no seu antivirus." -ForegroundColor DarkGray
Write-Host ""
