#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "请先安装项目 Python 虚拟环境：${ROOT_DIR}/.venv" >&2
  exit 1
fi
if [[ ! -f "${ROOT_DIR}/web/dist/index.html" ]]; then
  echo "首次使用：正在构建 Vue 工作台。"
  "${ROOT_DIR}/scripts/build_web.sh"
fi
cd "${ROOT_DIR}"
export ALGOFORGE_API_URL="${ALGOFORGE_API_URL:-http://127.0.0.1:8000}"
exec "${PYTHON_BIN}" -m uvicorn capability_factory.webui:create_ui_app --factory \
  --host "${ALGOFORGE_UI_HOST:-127.0.0.1}" --port "${ALGOFORGE_UI_PORT:-8501}"
