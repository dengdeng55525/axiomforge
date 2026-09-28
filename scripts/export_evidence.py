"""Export a small, credential-screened evidence bundle without reading settings.

Only report.json and allowlisted candidate code/verification/metadata files are
read. No dataset, prediction, raw LLM payload, log, or .env is copied. This is a
portable historical record; the original real/mock/replay mode is unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from capability_factory.reporting import write_report  # noqa: E402

MAX_SOURCE_BYTES = 32 * 1024 * 1024
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}"),
]
SECRET_FIELDS = {"api_key", "apikey", "access_token", "secret_key", "authorization", "password"}
EXPORT_NOTE = (
    "Portable historical evidence export. Original mode, statuses, failed attempts, "
    "metrics, usage records, and content hashes are preserved. Project-root absolute "
    "paths in JSON are made repository-relative. Datasets, predictions, raw LLM "
    "requests/responses, worker logs, credentials, and the private database are omitted. "
    "This is not a new execution or a replay-mode relabel."
)


class EvidenceExportError(ValueError):
    """A source cannot be safely or faithfully exported."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _scan(value, context: str) -> None:
    """Fail without echoing credential-like values into the exception or CLI."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SECRET_FIELDS and isinstance(item, str) and item.strip():
                if item.strip() not in {"[REDACTED]", "<redacted>"}:
                    raise EvidenceExportError(f"Credential-like field detected in {context}")
            _scan(str(key), context)
            _scan(item, context)
    elif isinstance(value, list):
        for item in value:
            _scan(item, context)
    elif isinstance(value, str) and any(pattern.search(value) for pattern in SECRET_PATTERNS):
        raise EvidenceExportError(f"Credential-like content detected in {context}")


def _portable(value, project: Path):
    if isinstance(value, dict):
        return {str(key): _portable(item, project) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable(item, project) for item in value]
    if isinstance(value, str):
        prefix = str(project)
        if value == prefix:
            return "."
        return value.replace(prefix + "/", "")
    return value


def _inside(path: Path, boundary: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(boundary):
        raise EvidenceExportError(f"Unsafe path outside allowed project area: {label}")
    return resolved


def _read(path: Path, boundary: Path, allowed_names: set[str]) -> bytes:
    if path.name not in allowed_names:
        raise EvidenceExportError("Source filename is not allowlisted")
    source = _inside(path, boundary, path.name)
    if not source.is_file() or source.stat().st_size > MAX_SOURCE_BYTES:
        raise EvidenceExportError(f"Source missing or oversized: {path.name}")
    data = source.read_bytes()
    text = data.decode("utf-8")
    _scan(text, path.name)
    return data


def _object(data: bytes, label: str) -> dict:
    try:
        value = json.loads(data)
    except (UnicodeError, ValueError) as error:
        raise EvidenceExportError(f"Invalid JSON in {label}") from error
    if not isinstance(value, dict):
        raise EvidenceExportError(f"Expected a JSON object in {label}")
    _scan(value, label)
    return value


def _json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def export_run(project_root: Path, run_id: str, name: str, note: str = "") -> dict:
    """Export one immutable named bundle after validating every selected source.

    Existing destinations are deliberately refused. Choose a new slug for a
    changed export instead of silently replacing a previously shared artifact.
    """
    if not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise EvidenceExportError("run-id must be a 32-character lowercase UUID hex")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", name):
        raise EvidenceExportError("name must contain only lowercase ASCII letters, digits, _ or -")
    project = Path(project_root).resolve(strict=True)
    runs = _inside(project / "artifacts" / "runs", project, "runs directory")
    run_directory = _inside(runs / run_id, runs, "run directory")
    public_base = _inside(project / "examples" / "evidence", project, "public evidence directory")
    destination = _inside(public_base / name, public_base, "export destination")
    if destination.exists():
        raise EvidenceExportError("Export destination already exists; choose a new name")
    _scan(note, "export note")
    raw_report = _read(run_directory / "report.json", run_directory, {"report.json"})
    report = _object(raw_report, "report.json")
    if report.get("run_id") != run_id:
        raise EvidenceExportError("Report run_id disagrees with source directory")
    source_hash = _sha(raw_report)
    additions = {
        "schema_version": "1.0",
        "source_report": (run_directory / "report.json").relative_to(project).as_posix(),
        "source_report_sha256": source_hash,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "note": EXPORT_NOTE + (" " + note if note else ""),
        "omitted": ["datasets", "predictions", "raw_llm_payloads", "worker_logs", "credentials", "database"],
    }
    public_report = _portable(report, project)
    public_report["evidence_export"] = _portable(additions, project)
    # Put the label in a prominent report section as well as the raw metadata.
    warnings = public_report.get("warnings")
    if not isinstance(warnings, list):
        warnings = [] if warnings is None else [warnings]
    public_report["warnings"] = [*warnings, _portable(additions["note"], project)]
    pending: dict[Path, bytes] = {}
    candidates = report.get("candidates", [])
    if not isinstance(candidates, list):
        raise EvidenceExportError("Report candidates must be a list")
    candidate_ids = set()
    attempt_count = 0

    def collect(source_record: dict, output_dir: Path) -> dict:
        raw_path = source_record.get("code_path")
        if not isinstance(raw_path, str) or ".." in Path(raw_path).parts:
            raise EvidenceExportError("Candidate code_path is missing or unsafe")
        code_path = Path(raw_path)
        if not code_path.is_absolute():
            code_path = run_directory / code_path
        code_path = _inside(code_path, run_directory, "candidate code")
        code = _read(code_path, run_directory, {"model.py"})
        if str(project) in code.decode():
            raise EvidenceExportError("Model source contains absolute project paths; refusing to alter its hash")
        expected = source_record.get("code_sha256")
        if not isinstance(expected, str) or _sha(code) != expected:
            raise EvidenceExportError("Candidate source SHA256 disagrees with recorded evidence")
        verification_path = code_path.parent / "verification.json"
        verification_raw = _read(verification_path, run_directory, {"verification.json"})
        verification = _object(verification_raw, "verification.json")
        verification_hash = verification.get("source_sha256")
        if verification_hash is not None and verification_hash != expected:
            raise EvidenceExportError("Verification source SHA256 disagrees with candidate")
        model_metadata = None
        model_metadata_path = code_path.parent / "model_metadata.json"
        if model_metadata_path.exists():
            model_metadata = _object(
                _read(model_metadata_path, run_directory, {"model_metadata.json"}),
                "model_metadata.json",
            )
        metadata = _portable({
            "record": source_record,
            "source_code": code_path.relative_to(project).as_posix(),
            "source_code_sha256": expected,
            "source_verification": verification_path.relative_to(project).as_posix(),
            "source_verification_sha256": _sha(verification_raw),
            "model_metadata": model_metadata,
        }, project)
        pending[output_dir / "model.py"] = code
        pending[output_dir / "verification.json"] = _json_bytes(_portable(verification, project))
        pending[output_dir / "metadata.json"] = _json_bytes(metadata)
        return metadata

    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise EvidenceExportError("Candidate record must be an object")
        identity = candidate.get("candidate_id")
        if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", identity):
            raise EvidenceExportError("Unsafe candidate_id")
        if identity in candidate_ids:
            raise EvidenceExportError("Duplicate candidate_id")
        candidate_ids.add(identity)
        candidate_dir = Path("candidates") / identity
        attempts = candidate.get("attempts", [])
        if not isinstance(attempts, list):
            raise EvidenceExportError("Candidate attempts must be a list")
        numbers = set()
        for attempt in attempts:
            if not isinstance(attempt, dict):
                raise EvidenceExportError("Attempt record must be an object")
            number = attempt.get("attempt")
            if type(number) is not int or number < 0 or number in numbers:
                raise EvidenceExportError("Attempt indexes must be unique nonnegative integers")
            numbers.add(number)
            collect(attempt, candidate_dir / f"attempt_{number}")
            attempt_count += 1
        if candidate.get("code_path"):
            collect(candidate, candidate_dir)
        else:
            # Generation may fail before any code exists. Preserve that fact.
            pending[candidate_dir / "metadata.json"] = _json_bytes(_portable({
                "record": candidate, "code_available": False,
                "note": "No generated code path was recorded; no model or validation is invented.",
            }, project))

    # Every input has passed policy checks before creating any public files.
    public_base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=public_base) as staging:
        stage = Path(staging) / "bundle"
        stage.mkdir()
        for relative, content in pending.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        write_report(public_report, stage)
        files = []
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                data = path.read_bytes()
                _scan(data.decode("utf-8"), "rendered export")
                if str(project) in data.decode("utf-8"):
                    raise EvidenceExportError("Absolute project path remained in exported content")
                files.append({"path": path.relative_to(stage).as_posix(), "sha256": _sha(data), "bytes": len(data)})
        manifest = {
            **_portable(additions, project), "run_id": run_id, "name": name,
            "mode": report.get("mode"), "status": report.get("status"),
            "candidate_count": len(candidates), "attempt_count": attempt_count, "files": files,
        }
        (stage / "manifest.json").write_bytes(_json_bytes(manifest))
        stage.rename(destination)
    return {"directory": destination.relative_to(project).as_posix(), "run_id": run_id,
            "source_report_sha256": source_hash, "candidates": len(candidates),
            "attempts": attempt_count, "files": len(files) + 1}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--root", type=Path, default=ROOT, help="Project root, for isolated fixtures or another checkout")
    parser.add_argument("--note", default="", help="Explicit historical limitations; does not relabel mode")
    arguments = parser.parse_args(argv)
    try:
        result = export_run(arguments.root, arguments.run_id, arguments.name, arguments.note)
    except (EvidenceExportError, OSError, UnicodeError, ValueError) as error:
        # Error strings never include matched credential values or report bodies.
        parser.exit(1, f"Evidence export failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
