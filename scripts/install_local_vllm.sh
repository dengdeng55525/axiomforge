#!/usr/bin/env bash
set -Eeuo pipefail

# Install the optional local vLLM runtime into this repository's .venv.
# This is intentionally separate from requirements.txt: the GPU runtime pulls
# several GB of CUDA/PyTorch wheels and must not be installed in CPU CI.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/.venv/bin/python}"
INDEX_URL="${LOCAL_LLM_PIP_INDEX_URL:-https://pypi.org/simple}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "未找到项目 Python：${PYTHON_BIN}" >&2
  echo "请先在项目根目录创建 .venv，或设置 PYTHON_BIN。" >&2
  exit 1
fi

echo "使用 Python：${PYTHON_BIN}"
echo "安装索引：${INDEX_URL}"
"${PYTHON_BIN}" -m pip install --upgrade pip setuptools wheel --index-url "${INDEX_URL}"
"${PYTHON_BIN}" -m pip install --requirement "${ROOT_DIR}/requirements-local-vllm.txt" --index-url "${INDEX_URL}"

"${PYTHON_BIN}" - <<'PY'
import torch
import vllm

print(f"vLLM {vllm.__version__}")
print(f"PyTorch {torch.__version__}; CUDA build={torch.version.cuda}")
print(f"CUDA available={torch.cuda.is_available()}; devices={torch.cuda.device_count()}")
if not torch.cuda.is_available():
    raise SystemExit("PyTorch 未检测到 CUDA；请检查 NVIDIA 驱动、CUDA 兼容性和容器 GPU 映射。")
PY

echo "安装完成：现在可以直接运行 ./scripts/start_local_vllm.sh。"
