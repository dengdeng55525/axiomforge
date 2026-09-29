#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STREAMLIT_BIN="${ROOT_DIR}/.venv/bin/streamlit"
if [[ ! -x "${STREAMLIT_BIN}" ]]; then
  echo "未找到旧版 Streamlit UI：${ROOT_DIR}/.venv/bin/streamlit" >&2
  exit 1
fi
cd "${ROOT_DIR}"
export ALGOFORGE_API_URL="${ALGOFORGE_API_URL:-http://127.0.0.1:8000}"
exec "${STREAMLIT_BIN}" run ui/app.py --server.address "${ALGOFORGE_UI_HOST:-127.0.0.1}" --server.port "${ALGOFORGE_UI_PORT:-8501}"
