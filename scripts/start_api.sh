#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "未找到项目虚拟环境：${ROOT_DIR}/.venv" >&2
  echo "请先执行：cd ${ROOT_DIR} && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt && .venv/bin/python -m pip install -e '.[dev,ui]'" >&2
  exit 1
fi

cd "${ROOT_DIR}"
exec "${PYTHON_BIN}" -m capability_factory serve --host "${ALGOFORGE_HOST:-127.0.0.1}" --port "${ALGOFORGE_API_PORT:-8000}"
