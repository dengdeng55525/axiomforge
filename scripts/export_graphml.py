#!/usr/bin/env python3
"""Export the persisted capability graph to a portable GraphML file.

This is intentionally a separate offline command so graph export never needs a
running API, browser session, or LLM credential.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capability_factory.graph_export import write_graphml
from capability_factory.knowledge import KnowledgeStore


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("artifacts/knowledge.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/graph.graphml"))
    args = parser.parse_args()
    store = KnowledgeStore(args.database)
    store.initialize()
    print(json.dumps(write_graphml(args.output, store.graph()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
