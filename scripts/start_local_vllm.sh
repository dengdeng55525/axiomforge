#!/usr/bin/env bash
set -Eeuo pipefail

# Launch four independent Qwen2.5-Coder-14B-AWQ OpenAI-compatible replicas.
# The application remains a client: this script owns the GPU processes and
# prints LOCAL_LLM_ENDPOINTS for the API process.  Keep it in the foreground
# so Ctrl-C reliably tears down every vLLM child.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${LOCAL_LLM_PROFILE:-four_gpu_14b}"
AVAILABLE_GPUS="${LOCAL_LLM_AVAILABLE_GPUS:-4}"
# Prefer the project virtual environment even when the operator did not run
# `source .venv/bin/activate`.  VLLM_BIN remains an escape hatch for a system
# installation or a container-provided executable.
VLLM_BIN="${VLLM_BIN:-${ROOT_DIR}/.venv/bin/vllm}"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  exec "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/serve_local_vllm.py" --help
fi

if [[ "${VLLM_BIN}" == */* ]]; then
  if [[ ! -x "${VLLM_BIN}" ]]; then
    echo "未找到 vLLM 可执行文件：${VLLM_BIN}" >&2
    echo "请在项目 .venv 中安装 vLLM，或设置 VLLM_BIN 指向可执行文件。" >&2
    exit 1
  fi
else
  RESOLVED_VLLM_BIN="$(command -v "${VLLM_BIN}" || true)"
  if [[ -z "${RESOLVED_VLLM_BIN}" ]]; then
    echo "未找到 vLLM 可执行文件：${VLLM_BIN}" >&2
    echo "请在项目 .venv 中安装 vLLM，或设置 VLLM_BIN 指向可执行文件。" >&2
    exit 1
  fi
  VLLM_BIN="${RESOLVED_VLLM_BIN}"
fi

if [[ ! -x "${VLLM_BIN}" ]]; then
  echo "vLLM 路径不可执行：${VLLM_BIN}" >&2
  echo "请检查 .venv/bin/vllm 权限，或设置 VLLM_BIN 指向可执行文件。" >&2
  exit 1
fi

cd "${ROOT_DIR}"
exec "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/serve_local_vllm.py" \
  --profile "${PROFILE}" \
  --available-gpus "${AVAILABLE_GPUS}" \
  --vllm-bin "${VLLM_BIN}" \
  "$@"
