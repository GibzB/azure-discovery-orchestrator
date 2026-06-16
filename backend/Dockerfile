FROM python:3.12-slim

WORKDIR /app

# azure-cognitiveservices-speech requires OpenSSL + audio libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libasound2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

EXPOSE 8000

# Use exec form so signals propagate correctly (graceful shutdown)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
