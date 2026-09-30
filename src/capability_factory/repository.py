"""Extract source-grounded capabilities from pinned Git blobs without imports."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit

from capability_factory.ingestion import TABULAR, TEXT


def _hash(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def extract_repository(
    repository: Path, paths: list[str], *, repository_url: str, license_id: str,
    task_types: list[str], revision: str = "HEAD",
) -> dict:
    """Inspect explicitly selected Python files at a resolved commit.

    No clone, checkout, imports, hooks or source execution occur. Dirty working
    files cannot change the snapshot. Task applicability and license are operator
    declarations; signatures, docstrings and imports are AST observations.
    """
    repository = Path(repository).resolve(strict=True)
    parsed = urlsplit(repository_url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("repository_url must be a credential-free HTTPS repository URL")
    repository_url = repository_url.rstrip("/").removesuffix(".git")
    if not license_id.strip() or len(license_id) > 100:
        raise ValueError("Declare the repository license (or NOASSERTION)")
    if not task_types or not set(task_types) <= {TABULAR, TEXT}:
        raise ValueError("Declare supported task types for the selected source")
    if not paths or len(paths) > 50 or len(set(paths)) != len(paths):
        raise ValueError("Select 1..50 distinct Python file paths")
    for path in paths:
        relative = PurePosixPath(path)
        if (relative.is_absolute() or ".." in relative.parts or str(relative) != path
                or relative.suffix != ".py" or any(c in path for c in "\x00\n\r\t:\\")):
            raise ValueError("Paths must be literal repository-relative Python files")

    def git(*arguments: str) -> bytes:
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update(GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
                           GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
        try:
            result = subprocess.run(
                ["git", "--no-pager", "--literal-pathspecs", "-C", str(repository),
                 "-c", "core.hooksPath=/dev/null", *arguments],
                capture_output=True, timeout=20, check=False, env=environment,
            )
        except subprocess.TimeoutExpired:
            raise ValueError("Git snapshot read exceeded its time budget") from None
        if result.returncode:
            raise ValueError("Git snapshot could not be read; check repository, revision and paths")
        return result.stdout

    commit = git("rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode().strip()
    listing = git("ls-tree", "-lz", commit, "--", *paths)
    entries = {}
    total_bytes = 0
    for raw in listing.split(b"\x00"):
        if not raw:
            continue
        metadata, name = raw.split(b"\t", 1)
        mode, kind, oid, size = metadata.decode().split()
        name = name.decode("utf-8")
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("Only regular Git blobs are accepted; symlinks are excluded")
        size = int(size)
        if size > 256 * 1024:
            raise ValueError("A selected source file exceeds 256 KiB")
        total_bytes += size
        entries[name] = (oid, size)
    if set(entries) != set(paths):
        raise ValueError("Every selected file must exist in the committed snapshot")
    if total_bytes > 2 * 1024 * 1024:
        raise ValueError("Repository extraction exceeds the 2 MiB total source budget")

    sources, cards, files, issues = [], [], [], []
    for path in sorted(paths):
        oid, expected_size = entries[path]
        raw = git("cat-file", "blob", oid)
        if len(raw) != expected_size:
            raise ValueError("Git blob length does not match its manifest")
        file_hash = _hash(raw)
        files.append({"path": path, "git_blob": oid, "sha256": file_hash, "bytes": len(raw)})
        try:
            tree = ast.parse(raw, filename=path)
        except (SyntaxError, ValueError) as error:
            issues.append({"path": path, "error_type": type(error).__name__})
            continue
        imports = sorted({ast.unparse(node) for node in ast.walk(tree)
                          if isinstance(node, (ast.Import, ast.ImportFrom))})
        symbols = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append((node.name, node))
                if isinstance(node, ast.ClassDef):
                    symbols.extend((f"{node.name}.{method.name}", method) for method in node.body
                                   if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)))
        for symbol, node in symbols:
            if len(sources) >= 200:
                raise ValueError("Repository extraction exceeds the 200-symbol budget")
            is_class = isinstance(node, ast.ClassDef)
            signature = (f"class {symbol}({', '.join(ast.unparse(x) for x in node.bases)})"
                         if is_class else f"{symbol}({ast.unparse(node.args)})")
            returns = None if is_class or node.returns is None else ast.unparse(node.returns)
            description = (ast.get_docstring(node, clean=True) or "No docstring recorded.")[:4000]
            content = signature + "\n" + description
            identity = _hash(json.dumps([repository_url, path, symbol], ensure_ascii=False))[:24]
            source_id = "repo-src-" + _hash(identity + commit + file_hash)[:24]
            locator = {"relative_path": path, "symbol": symbol, "line_start": node.lineno,
                       "line_end": node.end_lineno, "signature": signature,
                       "imports": imports, "parse_mode": "git-blob-ast-only"}
            sources.append({
                "source_id": source_id, "source_key": f"repository:{path}:{symbol}",
                "uri": f"{repository_url}/blob/{commit}/{quote(path)}#L{node.lineno}",
                "revision": commit, "license": license_id, "content_sha256": file_hash,
                "excerpt_sha256": _hash(content), "locator": locator,
                "content": content, "kind": "python_ast",
            })
            cards.append({
                "capability_id": "repo_" + identity, "name": symbol,
                "summary": description, "task_types": sorted(set(task_types)),
                "source_ids": [source_id], "dependencies": imports,
                "input_schema": {"signature": signature, "kind": "python_signature"},
                "output_schema": {"annotation": returns, "runtime_verified": False},
                "preconditions": ["Task applicability and license are operator-declared.",
                                  "AST observations do not certify execution or algorithm quality."],
                "tags": ["repository", "ast-only"],
                "origin": "repository_ast", "status": "extracted",
                "extraction_method": "pinned-git-blob-ast",
            })
    return {"schema_version": "1.0", "repository_url": repository_url,
            "commit": commit, "license": license_id, "files": files,
            "sources": sources, "capabilities": cards, "issues": issues,
            "source_executed": False, "task_applicability": "operator_declared"}
