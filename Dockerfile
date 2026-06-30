# Christian Bot — single image for daemon, dashboard, and bot services.
# Per-service command is selected in docker-compose.yml.
# ponytail: single-stage build. Three small Python services don't justify
# multi-stage gymnastics; the image is dominated by python:3.11-slim + node.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# System deps: curl (healthchecks), jq (heartbeat age check), git (claude installer),
# Node.js 20.x (mcp-substack), ca-certificates.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl jq git ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching than copying all source).
COPY pyproject.toml uv.lock* ./
RUN pip install --upgrade pip && pip install .

# Claude CLI (InstructionParser + manual parse exec). npm global install.
RUN npm install -g @anthropic-ai/claude-code || \
    echo "ponytail: claude install skipped — install manually if InstructionParser needs it"

# Application source.
COPY src/ ./src/
COPY config.yaml ./

# Runtime volume is provided by docker-compose (named volume `runtime`).
# Individual services override CMD.
CMD ["python", "-m", "src.ops"]
