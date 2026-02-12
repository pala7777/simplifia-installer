#!/bin/sh
set -e

# SIMPLIFIA Clawdbot Entrypoint
# Workaround: Clawdbot binds to 127.0.0.1, so we proxy 0.0.0.0 → 127.0.0.1

GATEWAY_PORT="${CLAWDBOT_GATEWAY_PORT:-18789}"
BROWSER_PORT="${CLAWDBOT_BROWSER_PORT:-18791}"
INTERNAL_GATEWAY_PORT="18790"
INTERNAL_BROWSER_PORT="18792"

echo "[entrypoint] Setting up socat proxies..."
echo "[entrypoint]   Gateway: 0.0.0.0:${GATEWAY_PORT} → 127.0.0.1:${INTERNAL_GATEWAY_PORT}"
echo "[entrypoint]   Browser: 0.0.0.0:${BROWSER_PORT} → 127.0.0.1:${INTERNAL_BROWSER_PORT}"

# Start socat proxies in background
socat TCP-LISTEN:${GATEWAY_PORT},fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:${INTERNAL_GATEWAY_PORT} &
SOCAT_GW_PID=$!

socat TCP-LISTEN:${BROWSER_PORT},fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:${INTERNAL_BROWSER_PORT} &
SOCAT_BR_PID=$!

# Trap to clean up on exit
cleanup() {
    echo "[entrypoint] Shutting down..."
    kill $SOCAT_GW_PID $SOCAT_BR_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Ensure config directory exists
mkdir -p /root/.config/clawdbot

# Set up minimal config if needed
if [ ! -f /root/.config/clawdbot/clawdbot.yaml ]; then
    echo "[entrypoint] Creating default config..."
    cat > /root/.config/clawdbot/clawdbot.yaml << EOF
gateway:
  mode: local
  bind: loopback
EOF
fi

# Add auth token to config if provided via env
if [ -n "$CLAWDBOT_GATEWAY_TOKEN" ]; then
    echo "[entrypoint] Auth token configured via environment"
fi

echo "[entrypoint] Starting Clawdbot gateway on internal port ${INTERNAL_GATEWAY_PORT}..."

# Start Clawdbot on internal loopback ports
# Override the ports via environment variables
export CLAWDBOT_GATEWAY_PORT="${INTERNAL_GATEWAY_PORT}"
export CLAWDBOT_BROWSER_CONTROL_PORT="${INTERNAL_BROWSER_PORT}"

exec clawdbot gateway run --port ${INTERNAL_GATEWAY_PORT} --allow-unconfigured "$@"
