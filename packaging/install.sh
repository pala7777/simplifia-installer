#!/bin/bash
# ============================================================
# SIMPLIFIA Installer - Mac/Linux
# Usage: curl -fsSL https://install.simplifia.com | bash
# 
# Installs: CLI + Setup + OpenClaw/Clawdbot Runtime (Docker)
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Helpers
print_header() {
    echo ""
    echo -e "${PURPLE}${BOLD}⚡ SIMPLIFIA Installer${NC}"
    echo -e "${CYAN}   Automação sem código em 1 comando${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    
    if [ "$SIMPLIFIA_NONINTERACTIVE" = "1" ]; then
        [ "$default" = "y" ] && return 0 || return 1
    fi
    
    local yn_hint="[S/n]"
    [ "$default" = "n" ] && yn_hint="[s/N]"
    
    read -p "$(echo -e "${CYAN}?${NC} $prompt $yn_hint ") " response
    response=${response:-$default}
    
    case "$response" in
        [SsYy]*) return 0 ;;
        *) return 1 ;;
    esac
}

# ============================================================
# PRE-CHECKS
# ============================================================

print_header

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)  OS_TYPE="linux" ;;
    Darwin*) OS_TYPE="mac" ;;
    CYGWIN*|MINGW*|MSYS*)
        print_error "Windows detectado! Use PowerShell:"
        echo ""
        echo -e "    ${BOLD}irm https://install.simplifia.com | iex${NC}"
        echo ""
        exit 1
        ;;
    *)
        print_error "Sistema operacional não suportado: $OS"
        exit 1
        ;;
esac

print_success "Sistema: $OS_TYPE"

# Check Python 3
print_step "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não encontrado!"
    echo ""
    if [ "$OS_TYPE" = "mac" ]; then
        echo "  Instale com: ${BOLD}brew install python3${NC}"
    else
        echo "  Instale com: ${BOLD}sudo apt install python3 python3-pip${NC}"
    fi
    echo ""
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    print_error "Python $PY_VERSION encontrado, mas precisa de 3.9+"
    exit 1
fi

print_success "Python $PY_VERSION encontrado"

# Check pip
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    print_warning "pip não encontrado, tentando instalar..."
    python3 -m ensurepip --upgrade 2>/dev/null || {
        print_error "Não foi possível instalar pip."
        if [ "$OS_TYPE" = "mac" ]; then
            echo "  Instale com: ${BOLD}python3 -m ensurepip${NC}"
        else
            echo "  Instale com: ${BOLD}sudo apt install python3-pip${NC}"
        fi
        exit 1
    }
fi

print_success "pip disponível"

# ============================================================
# INSTALL CLI
# ============================================================

echo ""
print_step "Instalando SIMPLIFIA CLI..."

# Check if already installed
EXISTING_VERSION=""
if command -v simplifia &> /dev/null; then
    EXISTING_VERSION=$(simplifia --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "")
    if [ -n "$EXISTING_VERSION" ]; then
        print_success "SIMPLIFIA $EXISTING_VERSION já instalado"
        if ask_yes_no "Atualizar para última versão?" "n"; then
            UPGRADE_FLAG="--upgrade"
        else
            UPGRADE_FLAG=""
            print_success "Mantendo versão atual"
        fi
    fi
else
    UPGRADE_FLAG="--upgrade"
fi

# Install/upgrade
if [ -n "$UPGRADE_FLAG" ] || [ -z "$EXISTING_VERSION" ]; then
    # Try pipx first (cleaner)
    if command -v pipx &> /dev/null; then
        pipx install simplifia --force 2>/dev/null || \
        pipx install git+https://github.com/pala7777/simplifia-installer.git --force 2>/dev/null || {
            print_warning "pipx falhou, tentando pip..."
            pip3 install --user $UPGRADE_FLAG simplifia 2>/dev/null || \
            pip3 install --user $UPGRADE_FLAG git+https://github.com/pala7777/simplifia-installer.git
        }
    else
        # Use pip --user
        pip3 install --user $UPGRADE_FLAG simplifia 2>/dev/null || \
        pip3 install --user $UPGRADE_FLAG git+https://github.com/pala7777/simplifia-installer.git
    fi
fi

# Add ~/.local/bin to PATH if needed
USER_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
    export PATH="$PATH:$USER_BIN"
    print_warning "Adicionando $USER_BIN ao PATH"
    
    # Add to shell rc
    SHELL_RC=""
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [ -n "$SHELL_RC" ]; then
        if ! grep -q 'export PATH="\$PATH:\$HOME/.local/bin"' "$SHELL_RC" 2>/dev/null; then
            echo 'export PATH="$PATH:$HOME/.local/bin"' >> "$SHELL_RC"
            print_success "PATH atualizado em $SHELL_RC"
        fi
    fi
fi

# Verify installation
if ! command -v simplifia &> /dev/null; then
    # Try direct path
    if [ -f "$USER_BIN/simplifia" ]; then
        alias simplifia="$USER_BIN/simplifia"
    else
        print_error "Instalação falhou - 'simplifia' não encontrado"
        echo "  Tente: ${BOLD}pip3 install --user simplifia${NC}"
        exit 1
    fi
fi

NEW_VERSION=$(simplifia --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
print_success "SIMPLIFIA v$NEW_VERSION instalado"

# ============================================================
# SETUP (3 perguntas modo iniciante)
# ============================================================

echo ""
print_step "Configuração inicial..."

# Check if already configured
if [ -f "$HOME/.simplifia/config.json" ]; then
    if ask_yes_no "Configuração existente encontrada. Reconfigurar?" "n"; then
        simplifia setup --force
    else
        print_success "Mantendo configuração atual"
    fi
else
    # Run setup (will ask 3 questions max in beginner mode)
    if [ "$SIMPLIFIA_NONINTERACTIVE" = "1" ]; then
        SIMPLIFIA_NONINTERACTIVE=1 simplifia setup 2>/dev/null || true
    else
        simplifia setup
    fi
fi

# ============================================================
# RUNTIME (Docker)
# ============================================================

echo ""
print_step "Verificando runtime OpenClaw/Clawdbot..."

# Check if runtime already installed
RUNTIME_INSTALLED=false
if [ -f "$HOME/.simplifia/clawdbot/docker-compose.yml" ]; then
    RUNTIME_INSTALLED=true
    print_success "Runtime já instalado"
fi

# Check Docker availability
DOCKER_AVAILABLE=false
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        DOCKER_AVAILABLE=true
        print_success "Docker disponível"
    else
        print_warning "Docker instalado mas não está rodando"
    fi
else
    print_warning "Docker não instalado"
fi

# Ask about runtime installation
INSTALL_RUNTIME=false

if [ "$RUNTIME_INSTALLED" = true ]; then
    # Already installed, check if running
    if docker ps --filter "name=simplifia-clawdbot" --format "{{.Names}}" 2>/dev/null | grep -q "simplifia-clawdbot"; then
        print_success "Runtime já está rodando"
    else
        if ask_yes_no "Iniciar runtime agora?" "y"; then
            simplifia clawdbot start
        fi
    fi
elif [ "$DOCKER_AVAILABLE" = true ]; then
    echo ""
    echo -e "${CYAN}O motor OpenClaw/Clawdbot é necessário para rodar automações.${NC}"
    echo -e "${CYAN}Ele roda via Docker (isolado, seguro, fácil de remover).${NC}"
    echo ""
    
    if ask_yes_no "Instalar o motor OpenClaw/Clawdbot (Docker) agora? (recomendado)" "y"; then
        INSTALL_RUNTIME=true
    else
        print_warning "Runtime não instalado"
        echo ""
        echo -e "  Você pode instalar depois com:"
        echo -e "    ${BOLD}simplifia clawdbot install --docker${NC}"
        echo -e "    ${BOLD}simplifia clawdbot start${NC}"
        echo ""
        echo -e "  ${YELLOW}Nota: Packs exigem o runtime para funcionar.${NC}"
    fi
else
    print_warning "Docker não disponível - runtime não será instalado"
    echo ""
    if [ "$OS_TYPE" = "mac" ]; then
        echo -e "  Instale o Docker Desktop: ${BOLD}https://docker.com/products/docker-desktop${NC}"
    else
        echo -e "  Instale o Docker: ${BOLD}https://docs.docker.com/engine/install/${NC}"
    fi
    echo ""
    echo -e "  Depois rode:"
    echo -e "    ${BOLD}simplifia clawdbot install --docker${NC}"
    echo -e "    ${BOLD}simplifia clawdbot start${NC}"
fi

# Install runtime if requested
if [ "$INSTALL_RUNTIME" = true ]; then
    echo ""
    print_step "Instalando runtime..."
    
    # Run clawdbot install (non-interactive)
    if [ "$SIMPLIFIA_NONINTERACTIVE" = "1" ]; then
        SIMPLIFIA_NONINTERACTIVE=1 simplifia clawdbot install --docker
    else
        # The clawdbot install command will ask about pulling image
        simplifia clawdbot install --docker
    fi
    
    print_step "Iniciando runtime..."
    simplifia clawdbot start
    
    # Health check
    print_step "Verificando health..."
    HEALTH_OK=false
    for i in {1..30}; do
        if docker ps --filter "name=simplifia-clawdbot" --filter "status=running" --format "{{.Names}}" 2>/dev/null | grep -q "simplifia-clawdbot"; then
            # Check if healthy
            HEALTH=$(docker inspect --format='{{.State.Health.Status}}' simplifia-clawdbot 2>/dev/null || echo "none")
            if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "none" ]; then
                HEALTH_OK=true
                break
            fi
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    if [ "$HEALTH_OK" = true ]; then
        print_success "Runtime iniciado e saudável!"
    else
        print_warning "Runtime iniciado mas health check pendente"
        echo "  Ver logs: ${BOLD}simplifia clawdbot logs${NC}"
    fi
fi

# ============================================================
# POST-INSTALLATION
# ============================================================

echo ""
print_step "Verificação final..."
simplifia doctor

echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅ SIMPLIFIA instalado com sucesso!${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Próximos passos:${NC}"
echo ""
echo -e "    1. Instalar um pack:"
echo -e "       ${CYAN}simplifia install whatsapp${NC}"
echo ""
echo -e "    2. Testar (modo seguro):"
echo -e "       ${CYAN}simplifia test whatsapp${NC}"
echo ""
echo -e "    3. Atualizar:"
echo -e "       ${CYAN}simplifia update whatsapp${NC}"
echo ""
echo -e "  ${YELLOW}⚠ Lembrete: A IA (LLM) é paga à parte pelo provedor${NC}"
echo -e "  ${YELLOW}  (OpenAI, Anthropic, etc). Você controla seus gastos.${NC}"
echo ""
echo -e "  ${BLUE}Ajuda: https://simplifia.com.br/downloads${NC}"
echo -e "  ${BLUE}Telegram: https://t.me/simplifia${NC}"
echo ""
