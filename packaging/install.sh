#!/bin/bash
# SIMPLIFIA Installer - Mac/Linux
# Usage: curl -fsSL https://install.simplifia.com | bash

set -e

echo "🚀 Instalando SIMPLIFIA..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.9+ primeiro."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PY_VERSION encontrado"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "⚠ pip3 não encontrado, tentando instalar..."
    python3 -m ensurepip --upgrade 2>/dev/null || {
        echo "❌ Não foi possível instalar pip. Instale manualmente."
        exit 1
    }
fi

# Install simplifia
echo "📦 Instalando simplifia via pip..."
pip3 install --user --upgrade simplifia 2>/dev/null || \
pip3 install --user --upgrade git+https://github.com/pala7777/simplifia-installer.git

# Add to PATH if needed
USER_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
    echo ""
    echo "⚠ Adicione ao seu PATH:"
    echo "  export PATH=\"\$PATH:$USER_BIN\""
    echo ""
    echo "  Ou adicione esta linha ao seu ~/.bashrc ou ~/.zshrc"
fi

echo ""
echo "✅ SIMPLIFIA instalado!"
echo ""
echo "Próximos passos:"
echo "  simplifia doctor         # Verificar ambiente"
echo "  simplifia list           # Ver packs disponíveis"
echo "  simplifia install whatsapp  # Instalar um pack"
echo ""
