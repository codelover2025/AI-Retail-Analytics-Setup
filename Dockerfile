FROM python:3.11-slim

WORKDIR /app

# Install curl (used for docker-compose healthchecks) and GL libraries for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./

# Cache pip downloads and install dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-ml.txt

COPY shared/ shared/
COPY edge_ai/ edge_ai/
COPY backend_core/ backend_core/
COPY scripts/ scripts/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
