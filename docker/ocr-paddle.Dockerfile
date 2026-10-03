FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir paddlepaddle paddleocr \
    && pip install --no-cache-dir -e .

# PP-OCRv5 model files are cached on first run; mount a persistent model cache in production.
