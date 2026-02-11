#!/bin/bash
# ============================================================
# SIMPLIFIA - Test Script for Clean Environment
# 
# Run this in a clean Ubuntu VM/Container:
#   docker run -it --rm ubuntu:24.04 bash
#   curl -fsSL <this-script-url> | bash
# ============================================================

set -e

echo "=============================================="
echo "🧪 SIMPLIFIA Clean Install Test"
echo "=============================================="
echo ""

# Pre-test: show environment
echo "📋 Environment:"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"
echo "  User: $(whoami)"
echo "  Python: $(python3 --version 2>/dev/null || echo 'not installed')"
echo "  Docker: $(docker --version 2>/dev/null || echo 'not installed')"
echo ""

# Step 1: Install dependencies (for clean Ubuntu)
echo "📦 Installing dependencies..."
apt-get update -qq
apt-get install -y -qq curl python3 python3-pip git > /dev/null 2>&1
echo "✓ Dependencies installed"
echo ""

# Step 2: Run installer
echo "🚀 Running installer..."
echo "----------------------------------------"
curl -fsSL https://raw.githubusercontent.com/pala7777/simplifia-installer/main/packaging/install.sh | SIMPLIFIA_NONINTERACTIVE=1 bash
echo "----------------------------------------"
echo ""

# Step 3: Verify CLI
echo "🔍 Verifying CLI..."
export PATH="$PATH:$HOME/.local/bin"

if command -v simplifia &> /dev/null; then
    echo "✓ simplifia found"
    simplifia --version
else
    echo "✗ simplifia NOT found in PATH"
    echo "  Checking ~/.local/bin..."
    ls -la ~/.local/bin/ 2>/dev/null || echo "  ~/.local/bin does not exist"
    exit 1
fi
echo ""

# Step 4: Run doctor
echo "🩺 Running doctor..."
simplifia doctor
echo ""

# Step 5: List packs
echo "📦 Listing packs..."
simplifia list
echo ""

# Step 6: Install WhatsApp pack
echo "⬇️ Installing WhatsApp pack..."
simplifia install whatsapp
echo ""

# Step 7: Test WhatsApp pack
echo "🧪 Testing WhatsApp pack..."
simplifia test whatsapp
echo ""

# Step 8: Status
echo "📊 Status..."
simplifia status
echo ""

# Final summary
echo "=============================================="
echo "✅ ALL TESTS PASSED!"
echo "=============================================="
echo ""
echo "Note: Docker runtime test requires docker-in-docker or host Docker."
echo "Run 'simplifia clawdbot doctor' on a machine with Docker to test runtime."
