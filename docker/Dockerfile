# SIMPLIFIA Clawdbot Runtime
# Runs Clawdbot in a container for SIMPLIFIA users

FROM node:22-slim

# Install system dependencies (including socat for bind workaround)
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    git \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Install clawdbot globally
RUN npm install -g clawdbot@latest

# Create workspace and config directories
RUN mkdir -p /root/.clawdbot /root/.config/clawdbot /root/clawd /data

# Set working directory
WORKDIR /root/clawd

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports:
# - 18789: Gateway/Canvas (proxied via socat to work with Docker networking)
# - 18791: Browser control (if needed)
EXPOSE 18789 18791

# Health check - checks the proxied gateway port
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://127.0.0.1:18790/health || curl -sf http://127.0.0.1:18789/clawdbot/canvas/ || exit 1

# Use entrypoint script which sets up socat proxy
ENTRYPOINT ["/entrypoint.sh"]
