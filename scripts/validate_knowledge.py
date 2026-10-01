#!/usr/bin/env python3
"""Run the read-only knowledge governance quality gate.

Examples:
    python scripts/validate_knowledge.py --database artifacts/knowledge.sqlite3
    python scripts/validate_knowledge.py --database artifacts/knowledge.sqlite3 --output report.json

The command never calls a model and never mutates the database.  A non-zero
exit status means errors were found or the database contains no capabilities;
``--strict`` also treats warnings as a failed gate.  Report files are created
exclusively, so an existing report, database hardlink or symlink is preserved.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from capability_factory.knowledge_governance import validate_database


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AlgoForge capability knowledge provenance")
    parser.add_argument("--database", type=Path, required=True, help="KnowledgeStore SQLite database")
    parser.add_argument("--output", type=Path, help="Create a new quality report file (must not exist)")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    args = parser.parse_args()

    try:
        report = validate_database(args.database)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.error(str(error))
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        # Preserve lexical ancestors until they have been checked.  Resolving
        # first would hide a symlink in a parent directory from this policy.
        output_path = args.output.expanduser().absolute()
        if any(path.is_symlink() for path in (output_path, *output_path.parents)):
            parser.error("--output and its parent directories must not be symlinks")
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        except OSError as error:
            parser.error(f"cannot create --output: {error}")
    else:
        print(payload, end="")
    summary = report["summary"]
    return int(report["status"] != "passed" or (args.strict and summary["warnings"] > 0))


if __name__ == "__main__":
    raise SystemExit(main())
