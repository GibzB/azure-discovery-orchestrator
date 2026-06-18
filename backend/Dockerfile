FROM python:3.12-slim

WORKDIR /app

# System dependencies
# Note: python:3.12-slim is based on Debian trixie where libasound2 → libasound2t64
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libasound2t64 \
    ca-certificates \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install azmcp for Azure MCP server (non-fatal if unavailable at runtime)
RUN npm install -g @azure/mcp@3.0.0-beta.18 || true

# Install Python dependencies (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
