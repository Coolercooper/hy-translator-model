#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "run_mac.sh 仅用于 macOS 原生 Metal 模式。"
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

export CMAKE_ARGS="${CMAKE_ARGS:-} -DGGML_METAL=on"
export FORCE_CMAKE=1
export LLAMA_BACKEND="${LLAMA_BACKEND:-metal}"
export LLAMA_N_GPU_LAYERS="${LLAMA_N_GPU_LAYERS:--1}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"
export UVICORN_WORKERS="${UVICORN_WORKERS:-1}"

uv sync --no-dev
./.venv/bin/pip install --no-cache-dir --force-reinstall --no-binary=:all: llama-cpp-python

exec ./.venv/bin/uvicorn app:app --host "$HOST" --port "$PORT" --workers "$UVICORN_WORKERS"