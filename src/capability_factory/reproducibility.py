"""Bounded, read-only integrity manifests for recorded workflow artifacts.

Only fixed input/report paths and constrained candidate paths are opened.
Directory descriptors and O_NOFOLLOW keep path resolution inside the selected
run.  Manifests expose hashes and safe identifiers, never artifact contents.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
DEFAULT_MAX_FILES = 512
DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 256 * 1024 * 1024
_JSON_BUFFER_BYTES = 256 * 1024
_MAX_RECORDS = 1024
_REPORT_FILES = ("progress.json", "report.html", "report.json", "report.md")
_INPUT_PATHS = {
    "train": "dataset/worker/train.json",
    "validation_features": "dataset/worker/validation_features.json",
    "validation_labels": "dataset/evaluator/validation_labels.json",
}
_OPTIONAL_FILES = ("constructor_plan.json", "model_metadata.json", "predictions.json", "validation_result.json")
_CODE_PATH = re.compile(r"candidates/[A-Za-z0-9_-]{1,48}/attempt_[0-9]{1,3}/model[.]py\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,31}\Z")
_SECRET = re.compile(r"(?:sk-|ghp_|github_pat_|Bearer|password|token|secret)", re.IGNORECASE)


def _safe_schema(value: Any) -> str | None:
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        text = str(value)
        if _SCHEMA.fullmatch(text) and not _SECRET.search(text):
            return text
    return None


def _safe_code_path(value: Any) -> str | None:
    return value if isinstance(value, str) and _CODE_PATH.fullmatch(value) and not _SECRET.search(value) else None


def _error(error: OSError) -> str:
    if error.errno == errno.ENOENT:
        return "missing"
    if error.errno == errno.ELOOP:
        return "symlink_ancestor"
    if error.errno == errno.ENOTDIR:
        return "unsafe_path"
    return "read_error"


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _open_directory(path: Path) -> tuple[int | None, str | None]:
    """Walk every absolute ancestor by descriptor; no symlink is followed."""
    path = path.absolute()
    if ".." in path.parts:
        return None, "unsafe_path"
    descriptor = None
    try:
        descriptor = os.open(path.anchor, _directory_flags())
        for part in path.parts[1:]:
            info = os.stat(part, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise OSError(errno.ELOOP, "symlink ancestor")
            if not stat.S_ISDIR(info.st_mode):
                raise OSError(errno.ENOTDIR, "path component is not a directory")
            child = os.open(part, _directory_flags(), dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor, None
    except OSError as error:
        if descriptor is not None:
            os.close(descriptor)
        return None, _error(error)


def _read_file(
    root_fd: int, relative: str, per_file: int, remaining: int, *, capture_limit: int = 0,
) -> tuple[str | None, int, str | None, int, bytes | None]:
    """Read a regular file through a descriptor under byte and growth limits."""
    parent_fd = os.dup(root_fd)
    file_fd = None
    consumed = 0
    size = 0
    try:
        parts = Path(relative).parts
        for part in parts[:-1]:
            info = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise OSError(errno.ELOOP, "symlink ancestor")
            if not stat.S_ISDIR(info.st_mode):
                raise OSError(errno.ENOTDIR, "path component is not a directory")
            child = os.open(part, _directory_flags(), dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child
        target_info = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(target_info.st_mode):
            raise OSError(errno.ELOOP, "symlink artifact")
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                          dir_fd=parent_fd)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            return None, 0, "not_regular_file", 0, None
        size = before.st_size
        if size > per_file:
            return None, size, "file_size_limit", 0, None
        if size > remaining:
            return None, size, "total_size_limit", 0, None
        digest = hashlib.sha256()
        chunks = [] if capture_limit and size <= capture_limit else None
        # Read at most the size observed at open; growth never increases the
        # read allowance. fstat below rejects mutations during the snapshot.
        while consumed < size:
            block = os.read(file_fd, min(65536, size - consumed, per_file - consumed, remaining - consumed))
            if not block:
                return None, size, "changed_during_read", consumed, None
            consumed += len(block)
            digest.update(block)
            if chunks is not None:
                chunks.append(block)
        after = os.fstat(file_fd)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            return None, size, "changed_during_read", consumed, None
        return digest.hexdigest(), size, None, consumed, b"".join(chunks) if chunks is not None else None
    except OSError as error:
        return None, size, _error(error), consumed, None
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(parent_fd)


def _object(payload: bytes | None) -> dict | None:
    try:
        value = json.loads(payload) if payload is not None else None
    except (ValueError, UnicodeError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def load_run_report(run_dir: Path | str, max_bytes: int = 4 * 1024 * 1024) -> dict:
    """Read report.json safely without settings, database access, or side effects."""
    descriptor, error = _open_directory(Path(run_dir))
    if descriptor is None:
        raise ValueError("Run report cannot be read safely")
    try:
        _, _, error, _, payload = _read_file(descriptor, "report.json", max_bytes, max_bytes,
                                              capture_limit=max_bytes)
    finally:
        os.close(descriptor)
    report = _object(payload)
    if error or report is None:
        raise ValueError("Run report is missing, invalid, or exceeds the read limit")
    return report


def _inventory(report: Mapping[str, Any]) -> tuple[dict, dict, int, bool]:
    entries = {path: ("input", True) for path in (*_INPUT_PATHS.values(), "dataset/manifest.json")}
    entries.update({path: ("report", True) for path in _REPORT_FILES})
    hashes: dict[str, set[str]] = {}
    invalid = 0
    limited = False

    def digest(path, value):
        nonlocal invalid
        if value is None:
            return
        if isinstance(value, str) and _DIGEST.fullmatch(value):
            hashes.setdefault(path, set()).add(value)
        else:
            invalid += 1

    candidates = report.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
        invalid += 1
    records = []
    for candidate in candidates[:_MAX_RECORDS]:
        if not isinstance(candidate, Mapping):
            invalid += 1
            continue
        records.append(candidate)
        attempts = candidate.get("attempts", [])
        if not isinstance(attempts, list):
            invalid += 1
            continue
        if len(records) + len(attempts) > _MAX_RECORDS:
            limited = True
        records.extend(attempts[:max(0, _MAX_RECORDS - len(records))])
        if len(records) >= _MAX_RECORDS:
            limited = True
            break
    limited = limited or len(candidates) > _MAX_RECORDS
    for record in records:
        if not isinstance(record, Mapping):
            invalid += 1
            continue
        raw = record.get("code_path")
        if raw is None:
            if record.get("code_sha256") is not None or "attempt" in record:
                invalid += 1
            continue
        path = _safe_code_path(raw)
        if path is None:
            invalid += 1
            continue
        entries[path] = ("code", True)
        parent = path.rsplit("/", 1)[0]
        entries[parent + "/verification.json"] = ("validation", True)
        entries.update({parent + "/" + filename: ("validation", False) for filename in _OPTIONAL_FILES})
        digest(path, record.get("code_sha256"))
    provenance = report.get("provenance")
    dataset = provenance.get("dataset") if isinstance(provenance, Mapping) else None
    declared = dataset.get("file_sha256") if isinstance(dataset, Mapping) else None
    if isinstance(declared, Mapping):
        for key, path in _INPUT_PATHS.items():
            digest(path, declared.get(key))
    return entries, hashes, invalid, limited


def build_reproducibility(
    report: Mapping[str, Any], run_dir: Path | str, *, max_files: int = DEFAULT_MAX_FILES,
    max_bytes: int = DEFAULT_MAX_BYTES, max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    """Fingerprint artifacts; missing optional worker outputs are permitted.

    A complete manifest records an AST-rejected attempt with model.py and
    verification.json, even when no worker outputs were produced. Completeness
    describes evidence integrity and does not change the algorithm run status.
    """
    max_files = max(1, int(max_files))
    max_bytes = max(1, int(max_bytes))
    max_total_bytes = max(1, int(max_total_bytes))
    entries, expected_hashes, invalid, limited = _inventory(report)
    descriptor, root_error = _open_directory(Path(run_dir))
    records = []
    total_bytes = 0
    try:
        for path in sorted(entries)[:max_files]:
            kind, required = entries[path]
            digest, size, error, consumed, payload = (None, 0, root_error, 0, None)
            if descriptor is not None:
                digest, size, error, consumed, payload = _read_file(
                    descriptor, path, max_bytes, max_total_bytes - total_bytes,
                    capture_limit=_JSON_BUFFER_BYTES if path.endswith(".json") else 0,
                )
            total_bytes += consumed
            parsed = _object(payload)
            declared = sorted(expected_hashes.get(path, []))
            records.append({
                "path": path, "kind": kind, "required": required,
                "available": digest is not None, "size_bytes": size, "sha256": digest,
                "schema_version": _safe_schema(parsed.get("schema_version")) if parsed else None,
                "recorded_sha256": declared[0] if declared else None,
                "matches_recorded": all(digest == item for item in declared) if digest and declared else None,
                **({"error": error} if error else {}),
            })
    finally:
        if descriptor is not None:
            os.close(descriptor)
    missing = [item["path"] for item in records if item.get("error") == "missing" and item["required"]]
    optional_missing = [item["path"] for item in records if item.get("error") == "missing" and not item["required"]]
    errors = [item["path"] for item in records if item.get("error") not in {None, "missing"}]
    mismatched = [item["path"] for item in records if item["matches_recorded"] is False]
    conflicts = [path for path, values in expected_hashes.items() if len(values) > 1]
    truncated = len(entries) > max_files or limited
    status = ("failed" if mismatched or conflicts else "missing" if root_error == "missing"
              else "partial" if root_error or truncated or missing or errors or invalid else "complete")
    raw_id = report.get("run_id")
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": raw_id if isinstance(raw_id, str) and re.fullmatch(r"[0-9a-f]{32}", raw_id) else None,
        "status": status, "hash_algorithm": "sha256",
        "source_report_schema_version": _safe_schema(report.get("schema_version")),
        "artifact_count": len(records), "expected_artifact_count": sum(required for _, required in entries.values()),
        "available_artifact_count": sum(item["available"] for item in records),
        "total_bytes_hashed": total_bytes, "max_files": max_files,
        "max_bytes_per_file": max_bytes, "max_total_bytes": max_total_bytes,
        "truncated": truncated, "invalid_reference_count": invalid,
        "missing_paths": missing, "missing_expected_paths": missing,
        "optional_missing_paths": optional_missing, "error_paths": errors,
        "mismatched_paths": mismatched, "conflicting_hash_paths": conflicts,
        "artifacts": records,
        "by_kind": {kind: [item for item in records if item["kind"] == kind]
                    for kind in ("input", "code", "validation", "report")},
    }
