"""Small runtime compatibility shim for the pinned vLLM release.

vLLM 0.29.0 imports the MiniMax-M3 warmup module for every V1 model, even
when the loaded model is Qwen.  On the current Triton/CUDA stack that import
can fail before the first request.  AlgoForge does not serve MiniMax-M3, so a
no-op module is safe for this launcher and keeps the workaround isolated from
the installed vLLM package.
"""

from __future__ import annotations

import os
import sys
import types


if os.environ.get("ALGOFORGE_VLLM_COMPAT") == "1":
    module_name = "vllm.model_executor.warmup.minimax_m3_msa_warmup"
    if module_name not in sys.modules:
        shim = types.ModuleType(module_name)

        def minimax_m3_msa_warmup(_worker) -> None:
            return None

        shim.minimax_m3_msa_warmup = minimax_m3_msa_warmup
        sys.modules[module_name] = shim
