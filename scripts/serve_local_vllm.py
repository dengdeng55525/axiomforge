"""Start and supervise the configured local vLLM replica pool.

This deliberately lives outside the API process.  It does not download
weights itself; vLLM will resolve the pinned model revision on first start.
Use ``--dry-run`` to inspect commands without touching CUDA.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_planner():
    spec = importlib.util.spec_from_file_location("algoforge_plan_inference", ROOT / "scripts" / "plan_inference.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/plan_inference.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _config() -> dict:
    return json.loads((ROOT / "configs" / "inference_profiles.json").read_text(encoding="utf-8"))


def _terminate(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + 15
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=os.environ.get("LOCAL_LLM_PROFILE", "four_gpu_14b"))
    parser.add_argument("--available-gpus", type=int, default=int(os.environ.get("LOCAL_LLM_AVAILABLE_GPUS", "4")))
    parser.add_argument("--vllm-bin", default=os.environ.get("VLLM_BIN", "vllm"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    planner = _load_planner()
    plan = planner.build_plan(_config(), args.profile, args.available_gpus)
    endpoints = plan["endpoints"]
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if args.dry_run:
        return 0

    logs = ROOT / "artifacts" / "local_llm"
    logs.mkdir(parents=True, exist_ok=True)
    print("LOCAL_LLM_ENDPOINTS=" + ",".join(item["base_url"] for item in endpoints), flush=True)
    print("LOCAL_LLM_MODEL=" + str(plan.get("served_model_name") or endpoints[0]["served_model_name"]), flush=True)

    processes: list[subprocess.Popen] = []
    try:
        for endpoint in endpoints:
            env = os.environ.copy()
            env.update(endpoint["environment"])
            env.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
            log_path = logs / f"{endpoint['name']}.log"
            log = log_path.open("ab")
            argv = list(endpoint["argv"])
            # plan_inference intentionally emits a vLLM CLI command.  Resolve
            # it here so tests and operators can use an absolute VLLM_BIN.
            argv[0] = args.vllm_bin
            print(f"starting {endpoint['name']} on CUDA_VISIBLE_DEVICES={env['CUDA_VISIBLE_DEVICES']} -> {log_path}", flush=True)
            process = subprocess.Popen(
                argv,
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            processes.append(process)

        def stop(_signum, _frame):
            _terminate(processes)
            raise SystemExit(0)

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    print(f"vLLM replica exited with code {code}; stopping the remaining replicas", file=sys.stderr, flush=True)
                    return code or 1
            time.sleep(2)
    finally:
        _terminate(processes)


if __name__ == "__main__":
    raise SystemExit(main())
