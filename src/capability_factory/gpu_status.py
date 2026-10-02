"""Read-only GPU visibility status for the AxiomForge console.

The probe is intentionally small and process-local.  It calls ``nvidia-smi``
when the executable is available, never changes CUDA or proxy environment
variables, and returns a bounded four-slot view that also works on CPU-only
machines and in mock runs.
"""

from __future__ import annotations

import csv
import io
import shutil
import subprocess
from typing import Any

_QUERY = (
    "index,name,utilization.gpu,memory.used,memory.total,temperature.gpu"
)


def _slot(index: int, state: str = "unavailable", **values: Any) -> dict[str, Any]:
    return {
        "index": index,
        "label": f"GPU {index}",
        "state": state,
        "enabled": state == "enabled",
        "name": values.get("name"),
        "utilization_percent": values.get("utilization_percent"),
        "memory_used_mib": values.get("memory_used_mib"),
        "memory_total_mib": values.get("memory_total_mib"),
        "temperature_c": values.get("temperature_c"),
    }


def _number(value: str) -> int | float | None:
    value = value.strip()
    if not value or value.lower() in {"n/a", "not supported", "[not supported]"}:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def _empty(expected_count: int, status: str, message: str) -> dict[str, Any]:
    expected_count = max(0, min(int(expected_count), 4))
    return {
        "schema_version": "gpu-status.v1",
        "status": status,
        "source": "nvidia-smi",
        "expected_count": expected_count,
        "visible_count": 0,
        "enabled_count": 0,
        "message": message,
        "devices": [_slot(index) for index in range(4)],
    }


def probe_gpus(expected_count: int = 4, timeout_seconds: float = 1.0) -> dict[str, Any]:
    """Return a safe, bounded snapshot of visible NVIDIA GPU devices.

    ``expected_count`` describes the selected local deployment plan.  Four
    device slots are always returned so the UI remains stable when the host
    has zero, one, or four cards.  Probe failures are represented as data and
    never make the health endpoint fail.
    """

    expected_count = max(0, min(int(expected_count), 4))
    binary = shutil.which("nvidia-smi")
    if binary is None:
        return _empty(expected_count, "unavailable", "未检测到 nvidia-smi，当前按 CPU/Mock 环境运行")
    try:
        completed = subprocess.run(
            [binary, f"--query-gpu={_QUERY}", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=max(0.1, min(float(timeout_seconds), 3.0)),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return _empty(expected_count, "error", f"GPU 状态读取失败：{type(exc).__name__}")
    if completed.returncode != 0:
        return _empty(expected_count, "error", "nvidia-smi 返回错误，GPU 状态暂不可用")

    records: dict[int, dict[str, Any]] = {}
    for row in csv.reader(io.StringIO(completed.stdout or "")):
        if len(row) < 6:
            continue
        try:
            index = int(row[0].strip())
        except ValueError:
            continue
        if not 0 <= index < 4 or index in records:
            continue
        records[index] = {
            "name": row[1].strip() or None,
            "utilization_percent": _number(row[2]),
            "memory_used_mib": _number(row[3]),
            "memory_total_mib": _number(row[4]),
            "temperature_c": _number(row[5]),
        }

    devices = [
        _slot(index, "enabled", **records[index]) if index in records else _slot(index)
        for index in range(4)
    ]
    visible_count = len(records)
    status = "ready" if visible_count >= expected_count and visible_count else "partial"
    if visible_count == 0:
        status = "unavailable"
    return {
        "schema_version": "gpu-status.v1",
        "status": status,
        "source": "nvidia-smi",
        "expected_count": expected_count,
        "visible_count": visible_count,
        "enabled_count": visible_count,
        "message": (
            f"已发现 {visible_count}/4 张 GPU"
            if visible_count
            else "未发现可用 GPU，当前按 CPU/Mock 环境运行"
        ),
        "devices": devices,
    }
