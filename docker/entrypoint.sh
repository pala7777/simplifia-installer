#!/bin/bash
set -e

# SIMPLIFIA Clawdbot Entrypoint
# Workaround: Clawdbot binds to 127.0.0.1, so we proxy 0.0.0.0 → 127.0.0.1

GATEWAY_PORT="${CLAWDBOT_GATEWAY_PORT:-18789}"
BROWSER_PORT="${CLAWDBOT_BROWSER_PORT:-18791}"
INTERNAL_GATEWAY_PORT="18790"
INTERNAL_BROWSER_PORT="18792"

echo "=============================================="
echo "[entrypoint] SIMPLIFIA Clawdbot Docker Runtime"
echo "=============================================="
echo "[entrypoint] External ports (0.0.0.0):"
echo "[entrypoint]   Gateway: ${GATEWAY_PORT}"
echo "[entrypoint]   Browser: ${BROWSER_PORT}"
echo "[entrypoint] Internal ports (127.0.0.1):"
echo "[entrypoint]   Gateway: ${INTERNAL_GATEWAY_PORT}"
echo "[entrypoint]   Browser: ${INTERNAL_BROWSER_PORT}"
echo "=============================================="

# Ensure config directory exists
mkdir -p /root/.config/clawdbot

# Set config using clawdbot CLI to ensure it's in the right location
echo "[entrypoint] Setting gateway.mode=local via clawdbot config..."
clawdbot config set gateway.mode local 2>&1 || true
clawdbot config set gateway.bind loopback 2>&1 || true
echo "[entrypoint] Config set. Verifying..."
clawdbot config get 2>&1 | head -10 || true

if [ -n "$CLAWDBOT_GATEWAY_TOKEN" ]; then
    echo "[entrypoint] Auth token: configured via CLAWDBOT_GATEWAY_TOKEN"
else
    echo "[entrypoint] Auth token: NOT SET (requests may fail)"
fi

echo "[entrypoint] Starting socat proxies with debug..."

# Start socat proxies in background with debug output
socat -d -d TCP-LISTEN:${GATEWAY_PORT},fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:${INTERNAL_GATEWAY_PORT} 2>&1 | sed 's/^/[socat-gw] /' &
SOCAT_GW_PID=$!
echo "[entrypoint] Gateway socat started (PID: $SOCAT_GW_PID)"

socat -d -d TCP-LISTEN:${BROWSER_PORT},fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:${INTERNAL_BROWSER_PORT} 2>&1 | sed 's/^/[socat-br] /' &
SOCAT_BR_PID=$!
echo "[entrypoint] Browser socat started (PID: $SOCAT_BR_PID)"

# Give socat a moment to bind
sleep 1

# Verify socat is listening
echo "[entrypoint] Verifying socat listeners..."
ss -tlnp 2>/dev/null | grep -E ":(${GATEWAY_PORT}|${BROWSER_PORT})" || netstat -tlnp 2>/dev/null | grep -E ":(${GATEWAY_PORT}|${BROWSER_PORT})" || echo "[entrypoint] (listener check skipped)"

# Trap to clean up on exit
cleanup() {
    echo "[entrypoint] Shutting down..."
    kill $SOCAT_GW_PID $SOCAT_BR_PID 2>/dev/null || true
    exit 0
}
trap cleanup TERM INT

echo "[entrypoint] Starting Clawdbot gateway on 127.0.0.1:${INTERNAL_GATEWAY_PORT}..."

# Override the ports via environment variables
export CLAWDBOT_GATEWAY_PORT="${INTERNAL_GATEWAY_PORT}"
export CLAWDBOT_BROWSER_CONTROL_PORT="${INTERNAL_BROWSER_PORT}"

# Start Clawdbot in background so we can run self-test
clawdbot gateway run --port ${INTERNAL_GATEWAY_PORT} --allow-unconfigured "$@" &
CLAWDBOT_PID=$!
echo "[entrypoint] Clawdbot started (PID: $CLAWDBOT_PID)"

# Wait for Clawdbot to be ready
echo "[entrypoint] Waiting for Clawdbot to be ready..."
for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -sf http://127.0.0.1:${INTERNAL_GATEWAY_PORT}/clawdbot/canvas/ -o /dev/null 2>/dev/null; then
        echo "[entrypoint] ✓ Clawdbot ready on internal port ${INTERNAL_GATEWAY_PORT}"
        break
    fi
    if curl -sf http://127.0.0.1:${INTERNAL_GATEWAY_PORT}/health -o /dev/null 2>/dev/null; then
        echo "[entrypoint] ✓ Clawdbot health OK on internal port ${INTERNAL_GATEWAY_PORT}"
        break
    fi
    echo "[entrypoint] Waiting... ($i/10)"
    sleep 2
done

# Self-test
echo "=============================================="
echo "[entrypoint] SELF-TEST"
echo "=============================================="

CONTAINER_IP=$(hostname -i 2>/dev/null | awk '{print $1}' || echo "unknown")
echo "[entrypoint] Container IP: ${CONTAINER_IP}"

echo "[test] 1. Internal loopback (127.0.0.1:${INTERNAL_GATEWAY_PORT})..."
INTERNAL_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:${INTERNAL_GATEWAY_PORT}/clawdbot/canvas/ 2>/dev/null || echo "000")
echo "[test]    Result: HTTP ${INTERNAL_CODE}"

echo "[test] 2. Via socat proxy (127.0.0.1:${GATEWAY_PORT})..."
PROXY_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:${GATEWAY_PORT}/clawdbot/canvas/ 2>/dev/null || echo "000")
echo "[test]    Result: HTTP ${PROXY_CODE}"

echo "[test] 3. Via container IP (${CONTAINER_IP}:${GATEWAY_PORT})..."
if [ "$CONTAINER_IP" != "unknown" ]; then
    CONTAINER_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://${CONTAINER_IP}:${GATEWAY_PORT}/clawdbot/canvas/ 2>/dev/null || echo "000")
    echo "[test]    Result: HTTP ${CONTAINER_CODE}"
else
    echo "[test]    Skipped (no container IP)"
fi

echo "=============================================="
# Check for actual HTTP response (not 000 which means connection failed)
if [ "$INTERNAL_CODE" != "000" ] && [ "$INTERNAL_CODE" != "000000" ] && [ "$PROXY_CODE" != "000" ] && [ "$PROXY_CODE" != "000000" ]; then
    echo "[entrypoint] ✓ SELF-TEST PASSED - Service reachable!"
else
    echo "[entrypoint] ✗ SELF-TEST FAILED"
    echo "[entrypoint]   Internal: ${INTERNAL_CODE} (expected: 200/401, got connection failure)"
    echo "[entrypoint]   Proxy: ${PROXY_CODE} (expected: 200/401, got connection failure)"
    echo "[entrypoint]   Check Clawdbot logs above for errors!"
fi
echo "=============================================="
echo "[entrypoint] Ready. Host should now be able to reach:"
echo "[entrypoint]   http://localhost:${GATEWAY_PORT}/clawdbot/canvas/"
echo "[entrypoint]   http://localhost:${BROWSER_PORT}/"
echo "=============================================="

# Wait for Clawdbot process
wait $CLAWDBOT_PID
