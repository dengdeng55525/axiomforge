#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STREAMLIT_BIN="${ROOT_DIR}/.venv/bin/streamlit"

if [[ ! -x "${STREAMLIT_BIN}" ]]; then
  echo "未找到项目虚拟环境或 Streamlit：${ROOT_DIR}/.venv/bin/streamlit" >&2
  echo "请先执行：cd ${ROOT_DIR} && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt && .venv/bin/python -m pip install -e '.[dev,ui]'" >&2
  exit 1
fi

cd "${ROOT_DIR}"
export ALGOFORGE_API_URL="${ALGOFORGE_API_URL:-http://127.0.0.1:8000}"
exec "${STREAMLIT_BIN}" run ui/app.py --server.address "${ALGOFORGE_UI_HOST:-127.0.0.1}" --server.port "${ALGOFORGE_UI_PORT:-8501}"
