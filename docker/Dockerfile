# SIMPLIFIA Clawdbot Runtime
# Runs Clawdbot in a container for SIMPLIFIA users

FROM node:22-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install clawdbot globally
RUN npm install -g clawdbot@latest

# Create workspace and config directories
RUN mkdir -p /root/.clawdbot /root/clawd /data

# Set working directory
WORKDIR /root/clawd

# Expose Clawdbot web UI port
EXPOSE 18789

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:18789/health || exit 1

# Default command - start gateway
CMD ["clawdbot", "gateway", "start", "--foreground"]
