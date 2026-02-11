#!/bin/bash
# ============================================================
# SIMPLIFIA Installer - Mac/Linux
# Usage: curl -fsSL https://simplifia.com.br/install.sh | bash
# 
# TRUE beginner path: downloads standalone binary (no Python needed)
# Fallback: pip install if binary download fails
# ============================================================

set -e

# ============================================================
# CONFIG
# ============================================================

SIMPLIFIA_VERSION="v1.0.1"
SIMPLIFIA_BIN_DIR="$HOME/.simplifia/bin"
SIMPLIFIA_BIN_PATH="$SIMPLIFIA_BIN_DIR/simplifia"

# Detect OS for binary download
OS="$(uname -s)"
case "$OS" in
    Linux*)  BINARY_NAME="simplifia-linux" ;;
    Darwin*) BINARY_NAME="simplifia-macos" ;;
    *)       BINARY_NAME="" ;;
esac

SIMPLIFIA_BIN_URL="https://github.com/pala7777/simplifia-installer/releases/download/$SIMPLIFIA_VERSION/$BINARY_NAME"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ============================================================
# HELPERS
# ============================================================

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

add_to_path() {
    local path_to_add="$1"
    
    # Add to current session
    if [[ ":$PATH:" != *":$path_to_add:"* ]]; then
        export PATH="$path_to_add:$PATH"
    fi
    
    # Add to shell rc file
    local shell_rc=""
    if [ -f "$HOME/.zshrc" ]; then
        shell_rc="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        shell_rc="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        shell_rc="$HOME/.bash_profile"
    fi
    
    if [ -n "$shell_rc" ]; then
        if ! grep -q "export PATH=\"$path_to_add:\$PATH\"" "$shell_rc" 2>/dev/null; then
            echo "export PATH=\"$path_to_add:\$PATH\"" >> "$shell_rc"
            return 0
        fi
    fi
    return 1
}

# ============================================================
# MAIN INSTALLER
# ============================================================

print_header

# Detect OS
case "$OS" in
    Linux*)  OS_TYPE="linux" ;;
    Darwin*) OS_TYPE="mac" ;;
    CYGWIN*|MINGW*|MSYS*)
        print_error "Windows detectado! Use PowerShell:"
        echo ""
        echo -e "    ${BOLD}irm https://simplifia.com.br/install.ps1 | iex${NC}"
        echo ""
        exit 1
        ;;
    *)
        print_error "Sistema operacional não suportado: $OS"
        exit 1
        ;;
esac

print_success "Sistema: $OS_TYPE"

# Create bin directory
mkdir -p "$SIMPLIFIA_BIN_DIR"

# ============================================================
# STEP 1: Try downloading standalone binary (BEGINNER PATH)
# ============================================================

print_step "Baixando SIMPLIFIA..."

binary_downloaded=false

if [ -n "$BINARY_NAME" ]; then
    if curl -fsSL "$SIMPLIFIA_BIN_URL" -o "$SIMPLIFIA_BIN_PATH" 2>/dev/null; then
        chmod +x "$SIMPLIFIA_BIN_PATH"
        
        # Test if it works
        if "$SIMPLIFIA_BIN_PATH" --version >/dev/null 2>&1; then
            binary_downloaded=true
            print_success "SIMPLIFIA baixado com sucesso!"
        else
            print_warning "Binário não funciona neste sistema. Tentando método alternativo..."
            rm -f "$SIMPLIFIA_BIN_PATH"
        fi
    else
        print_warning "Download do binário falhou. Tentando método alternativo..."
    fi
fi

# ============================================================
# STEP 2: Fallback to pip install if binary failed
# ============================================================

if [ "$binary_downloaded" = false ]; then
    print_step "Usando instalação via Python..."
    
    # Check Python
    python_available=false
    if command -v python3 &> /dev/null; then
        PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
        PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
        
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 9 ]; then
            python_available=true
            print_success "Python $PY_VERSION encontrado"
        fi
    fi
    
    if [ "$python_available" = false ]; then
        print_error "Python 3.9+ não encontrado!"
        echo ""
        if [ "$OS_TYPE" = "mac" ]; then
            echo -e "  Instale com: ${BOLD}brew install python3${NC}"
        else
            echo -e "  Instale com: ${BOLD}sudo apt install python3 python3-pip${NC}"
        fi
        echo ""
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        print_warning "pip não encontrado, tentando instalar..."
        python3 -m ensurepip --upgrade 2>/dev/null || {
            print_error "Não foi possível instalar pip."
            exit 1
        }
    fi
    print_success "pip disponível"
    
    # Install via pip
    print_step "Instalando via pip..."
    
    if command -v pipx &> /dev/null; then
        pipx install git+https://github.com/pala7777/simplifia-installer.git --force 2>/dev/null || \
        pip3 install --user git+https://github.com/pala7777/simplifia-installer.git
    else
        pip3 install --user git+https://github.com/pala7777/simplifia-installer.git
    fi
    
    # Find and copy to our bin dir
    USER_BIN="$HOME/.local/bin"
    if [ -f "$USER_BIN/simplifia" ]; then
        cp "$USER_BIN/simplifia" "$SIMPLIFIA_BIN_PATH"
        chmod +x "$SIMPLIFIA_BIN_PATH"
        print_success "SIMPLIFIA instalado via pip!"
    else
        print_error "simplifia não encontrado após instalação"
        exit 1
    fi
fi

# ============================================================
# STEP 3: Add to PATH
# ============================================================

print_step "Configurando PATH..."

if add_to_path "$SIMPLIFIA_BIN_DIR"; then
    print_success "PATH atualizado"
else
    print_success "PATH já configurado"
fi

# ============================================================
# STEP 4: Setup wizard
# ============================================================

echo ""
print_step "Configuração inicial..."

CONFIG_PATH="$HOME/.simplifia/config.json"

if [ ! -f "$CONFIG_PATH" ]; then
    if [ "$SIMPLIFIA_NONINTERACTIVE" = "1" ]; then
        "$SIMPLIFIA_BIN_PATH" setup 2>/dev/null || true
    else
        "$SIMPLIFIA_BIN_PATH" setup
    fi
else
    print_success "Configuração existente mantida"
fi

# ============================================================
# STEP 5: Runtime (Docker) - if available
# ============================================================

echo ""
print_step "Verificando runtime Docker..."

DOCKER_AVAILABLE=false
DOCKER_IMAGE="ghcr.io/pala7777/simplifia-clawdbot:latest"
IMAGE_EXISTS=false

if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        DOCKER_AVAILABLE=true
        print_success "Docker disponível"
        
        # Check if image exists
        if docker manifest inspect "$DOCKER_IMAGE" &> /dev/null; then
            IMAGE_EXISTS=true
            print_success "Imagem Docker disponível"
        fi
    fi
fi

if [ "$DOCKER_AVAILABLE" = true ] && [ "$IMAGE_EXISTS" = true ]; then
    echo ""
    echo -e "${CYAN}O motor OpenClaw/Clawdbot é necessário para rodar automações.${NC}"
    
    if ask_yes_no "Instalar o runtime agora? (recomendado)" "y"; then
        print_step "Instalando runtime..."
        "$SIMPLIFIA_BIN_PATH" clawdbot install --docker
        "$SIMPLIFIA_BIN_PATH" clawdbot start
    fi
elif [ "$DOCKER_AVAILABLE" = false ]; then
    echo ""
    echo -e "  ${YELLOW}💡 Para rodar automações, instale o Docker:${NC}"
    if [ "$OS_TYPE" = "mac" ]; then
        echo -e "     ${CYAN}https://docker.com/products/docker-desktop${NC}"
    else
        echo -e "     ${CYAN}https://docs.docker.com/engine/install/${NC}"
    fi
fi

# ============================================================
# STEP 6: Success check (REQUIRED)
# ============================================================

echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Verificação Final${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo ""

# Test 1: Version
print_step "Testando simplifia --version..."
VERSION_OUTPUT=$("$SIMPLIFIA_BIN_PATH" --version 2>&1) || {
    print_error "FALHA: simplifia --version não funciona"
    exit 1
}
echo -e "  ${GREEN}$VERSION_OUTPUT${NC}"

# Test 2: Doctor
echo ""
print_step "Testando simplifia doctor..."
"$SIMPLIFIA_BIN_PATH" doctor

# ============================================================
# SUCCESS MESSAGE
# ============================================================

echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅ SIMPLIFIA instalado com sucesso!${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Próximo passo:${NC}"
echo ""
echo -e "    ${CYAN}simplifia install whatsapp${NC}"
echo ""
echo -e "  ${BOLD}Outros comandos:${NC}"
echo -e "    ${NC}simplifia list        → Ver packs disponíveis${NC}"
echo -e "    ${NC}simplifia doctor      → Verificar ambiente${NC}"
echo -e "    ${NC}simplifia --help      → Ajuda completa${NC}"
echo ""
echo -e "  ${YELLOW}⚠ Lembrete: A IA (LLM) é paga à parte pelo provedor${NC}"
echo -e "  ${YELLOW}  (OpenAI, Anthropic, etc). Você controla seus gastos.${NC}"
echo ""
echo -e "  ${BLUE}📚 Ajuda: https://simplifia.com.br/downloads${NC}"
echo -e "  ${BLUE}💬 Telegram: https://t.me/simplifia${NC}"
echo ""
echo -e "  ${YELLOW}💡 Se 'simplifia' não for encontrado, feche e reabra o terminal.${NC}"
echo ""
