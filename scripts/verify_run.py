#!/usr/bin/env python3
"""Emit a bounded SHA-256 manifest for one persisted run.

Examples:
    python scripts/verify_run.py --run-id <32-hex-run-id>
    python scripts/verify_run.py --run-id <32-hex-run-id> --output artifacts/manifest.json

The command reads an existing report and run artifacts only.  It never starts
an agent, updates the SQLite knowledge store, or changes the run directory.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from capability_factory.reproducibility import build_reproducibility, load_run_report  # noqa: E402


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def _has_symlink_ancestor(path: Path) -> bool:
    current = _absolute(path)
    for ancestor in (current, *current.parents):
        try:
            if stat.S_ISLNK(ancestor.lstat().st_mode):
                return True
        except FileNotFoundError:
            continue
        except OSError:
            return True
    return False


def _write_new(path: Path, content: str, run_dir: Path, database: Path) -> None:
    """Create a new regular output atomically; never overwrite or link files."""
    target = _absolute(path)
    root = _absolute(run_dir)
    db = _absolute(database)
    if target == root or target.is_relative_to(root) or target == db:
        raise ValueError("output must be outside the run directory and database")
    target.parent.mkdir(parents=True, exist_ok=True)
    if _has_symlink_ancestor(target) or _has_symlink_ancestor(target.parent):
        raise ValueError("output path contains a symlink ancestor")
    try:
        fd = os.open(
            target,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
        )
    except FileExistsError as error:
        raise ValueError("output already exists; choose a new path") from error
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.EEXIST}:
            raise ValueError("output path is unsafe or already exists") from error
        raise
    try:
        with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as handle:
            fd = None
            handle.write(content)
    finally:
        if fd is not None:
            os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify persisted AxiomForge run artifacts")
    parser.add_argument("--run-id", required=True, help="32-character lowercase run id")
    parser.add_argument("--output", type=Path, help="optional path for the JSON manifest")
    parser.add_argument("--project-root", type=Path, default=ROOT,
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{32}", args.run_id):
        parser.error("--run-id must be a 32-character lowercase UUID hex")
    project = _absolute(args.project_root)
    run_dir = project / "artifacts" / "runs" / args.run_id
    try:
        report = load_run_report(run_dir)
    except ValueError:
        print("run report is missing, unsafe, invalid, or exceeds the read limit", file=sys.stderr)
        return 2
    if report.get("run_id") != args.run_id:
        print("report.json run_id does not match --run-id", file=sys.stderr)
        return 2
    manifest = build_reproducibility(report, run_dir)
    encoded = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        try:
            _write_new(args.output, encoded, run_dir, project / "artifacts" / "knowledge.sqlite3")
        except (OSError, ValueError):
            print("cannot create a new safe --output file", file=sys.stderr)
            return 2
    else:
        print(encoded, end="")
    return 0 if manifest["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
