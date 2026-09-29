#!/usr/bin/env bash
set -Eeuo pipefail

# Launch four independent Qwen2.5-Coder-14B-AWQ OpenAI-compatible replicas.
# The application remains a client: this script owns the GPU processes and
# prints LOCAL_LLM_ENDPOINTS for the API process.  Keep it in the foreground
# so Ctrl-C reliably tears down every vLLM child.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${LOCAL_LLM_PROFILE:-four_gpu_14b}"
AVAILABLE_GPUS="${LOCAL_LLM_AVAILABLE_GPUS:-4}"
VLLM_BIN="${VLLM_BIN:-vllm}"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  exec "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/serve_local_vllm.py" --help
fi

if ! command -v "${VLLM_BIN}" >/dev/null 2>&1; then
  echo "未找到 vLLM 可执行文件：${VLLM_BIN}" >&2
  echo "请在 GPU 环境安装与 CUDA/驱动匹配的 vllm，或设置 VLLM_BIN 指向 vllm。" >&2
  exit 1
fi

cd "${ROOT_DIR}"
exec "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/serve_local_vllm.py" \
  --profile "${PROFILE}" \
  --available-gpus "${AVAILABLE_GPUS}" \
  --vllm-bin "${VLLM_BIN}"
