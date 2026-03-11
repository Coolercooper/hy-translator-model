FROM python:3.11-slim

ARG GGUF_MODEL_FILE=HY-MT1.5-1.8B-Q4_K_M.gguf

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# ─────────────────────────────────────────────────────────────
WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY app.py .
RUN mkdir -p /models
COPY --from=modelsrc /${GGUF_MODEL_FILE} /models/${GGUF_MODEL_FILE}

ENV PATH="/app/.venv/bin:${PATH}"
ENV MODEL_FILE=/models/${GGUF_MODEL_FILE} \
    MAX_NEW_TOKENS=256 \
    PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=1

EXPOSE 8000
CMD uvicorn app:app --host 0.0.0.0 --port 8000 --workers $UVICORN_WORKERS
