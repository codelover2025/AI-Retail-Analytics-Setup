FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-ml.txt

COPY shared/ shared/
COPY edge_ai/ edge_ai/
COPY backend_core/ backend_core/
COPY scripts/ scripts/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
