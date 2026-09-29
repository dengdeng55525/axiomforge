"""Check all configured OpenAI-compatible local model replicas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

from capability_factory.settings import load_settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    settings = load_settings(Path(__file__).resolve().parents[1])
    rows = []
    for endpoint in settings.local_endpoints:
        row = {"endpoint": endpoint, "healthy": False}
        try:
            response = httpx.get(endpoint.removesuffix("/v1") + "/health", timeout=args.timeout,
                                 follow_redirects=False, trust_env=False)
            row["health_status"] = response.status_code
            row["healthy"] = response.status_code == 200
            try:
                row["health"] = response.json()
            except ValueError:
                pass
        except httpx.HTTPError as error:
            row["error"] = type(error).__name__
        rows.append(row)
    print(json.dumps({"model": settings.local_model, "endpoints": rows}, ensure_ascii=False, indent=2))
    return 0 if rows and all(row["healthy"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
