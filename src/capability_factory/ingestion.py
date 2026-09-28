"""Bounded, provenance-preserving ingestion of documentation and Python ASTs.

Ingestion never imports or executes the source being inspected. Installed package
locations come from distribution metadata; business records and secrets are never
included in the extraction corpus.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

TABULAR = "tabular_binary_classification"
TEXT = "text_binary_classification"

DOCUMENTS = [
    ("bank-duration", "data/raw/bank-additional-names.txt", "duration:",
     "https://archive.ics.uci.edu/dataset/222/bank+marketing", "CC-BY-4.0"),
    ("bank-pdays", "data/raw/bank-additional-names.txt", "pdays:",
     "https://archive.ics.uci.edu/dataset/222/bank+marketing", "CC-BY-4.0"),
    ("bank-target", "data/raw/bank-additional-names.txt", "21 - y",
     "https://archive.ics.uci.edu/dataset/222/bank+marketing", "CC-BY-4.0"),
    ("bank-unknown", "data/raw/bank-additional-names.txt", "8. Missing",
     "https://archive.ics.uci.edu/dataset/222/bank+marketing", "CC-BY-4.0"),
    ("sms-format", "data/raw/sms-readme.txt", "1.3. Format",
     "https://archive.ics.uci.edu/dataset/228/sms+spam+collection", "CC-BY-4.0"),
    ("project-bank-policy", "docs/02_数据与知识来源.md", "## 2.",
     None, "original-project-notes"),
    ("project-bank-split", "docs/02_数据与知识来源.md", "## 3.",
     None, "original-project-notes"),
    ("project-sms-split", "docs/02_数据与知识来源.md", "## 4.",
     None, "original-project-notes"),
    ("project-evidence", "docs/02_数据与知识来源.md", "## 6.",
     None, "original-project-notes"),
]

PYTHON_SYMBOLS = [
    ("sklearn-pipeline", "sklearn/pipeline.py", "Pipeline"),
    ("sklearn-columns", "sklearn/compose/_column_transformer.py", "ColumnTransformer"),
    ("sklearn-onehot", "sklearn/preprocessing/_encoders.py", "OneHotEncoder"),
    ("sklearn-scaler", "sklearn/preprocessing/_data.py", "StandardScaler"),
    ("sklearn-imputer", "sklearn/impute/_base.py", "SimpleImputer"),
    ("sklearn-logistic", "sklearn/linear_model/_logistic.py", "LogisticRegression"),
    ("sklearn-forest", "sklearn/ensemble/_forest.py", "RandomForestClassifier"),
    ("sklearn-histgb", "sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py",
     "HistGradientBoostingClassifier"),
    ("sklearn-tfidf", "sklearn/feature_extraction/text.py", "TfidfVectorizer"),
    ("sklearn-complementnb", "sklearn/naive_bayes.py", "ComplementNB"),
    ("sklearn-multinomialnb", "sklearn/naive_bayes.py", "MultinomialNB"),
    ("sklearn-ap", "sklearn/metrics/_ranking.py", "average_precision_score"),
    ("sklearn-rocauc", "sklearn/metrics/_ranking.py", "roc_auc_score"),
]


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source(*, key: str, path: Path, uri: str, revision: str, license_: str,
            start: int, end: int, content: str, kind: str,
            extra: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = path.read_bytes()
    locator = {"path": str(path.resolve()), "line_start": start, "line_end": end}
    if extra:
        locator.update(extra)
    digest = _sha(raw)
    identity = json.dumps([uri, digest, locator], sort_keys=True, ensure_ascii=False)
    return {
        "source_id": "src-" + _sha(identity.encode())[:24],
        "source_key": key, "uri": uri, "revision": revision, "license": license_,
        "content_sha256": digest, "excerpt_sha256": _sha(content.encode()),
        "locator": locator, "content": content, "kind": kind,
    }


def read_document(path: Path, *, key: str, marker: str, uri: str | None = None,
                  license_: str = "original-project-notes") -> dict[str, Any]:
    """Extract a marked section with exact source line numbers and content hashes."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    matches = [i for i, line in enumerate(lines) if marker in line]
    if not matches:
        raise ValueError(f"Source marker {marker!r} absent from {path.name}")
    start = matches[0]
    if marker.startswith("## "):
        end = next((i for i in range(start + 1, len(lines))
                    if lines[i].startswith("## ")), len(lines))
    elif key == "sms-format":
        # The format explanation is enough; no raw SMS examples enter the LLM context.
        end = min(start + 4, len(lines))
    else:
        end = min(start + 3, len(lines))
    content = "\n".join(lines[start:end])
    return _source(key=key, path=path, uri=uri or path.resolve().as_uri(),
                   revision="sha256:" + _sha(path.read_bytes()), license_=license_,
                   start=start + 1, end=end, content=content, kind="document")


def parse_python_source(path: Path, *, key: str, symbol: str,
                        relative_path: str | None = None, revision: str = "local") -> dict[str, Any]:
    """Extract a top-level symbol and its imports through AST, without execution."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    node = next((n for n in tree.body
                 if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == symbol), None)
    if node is None:
        raise ValueError(f"Top-level symbol {symbol!r} absent from {path.name}")
    imports = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    docstring = ast.get_docstring(node, clean=True) or ""
    methods = [n.name for n in getattr(node, "body", [])
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if isinstance(node, ast.ClassDef):
        signature = f"class {symbol}({', '.join(ast.unparse(b) for b in node.bases)}):"
        init = next((n for n in node.body if isinstance(n, ast.FunctionDef)
                     and n.name == "__init__"), None)
        if init:
            signature += f"\n    def __init__({ast.unparse(init.args)})"
    else:
        signature = f"def {symbol}({ast.unparse(node.args)})"
    # Preserve relevant parameters even if a long class docstring is abbreviated.
    keywords = ("handle_unknown", "sparse_output", "predict_proba", "with_mean",
                "non-negative", "nonnegative", "binary", "probability", "probabilities")
    detail_lines = [line for line in docstring.splitlines()
                    if any(word in line for word in keywords)]
    content = signature + "\n\n" + docstring[:4200]
    content += "\n\nSelected parameter notes:\n" + "\n".join(detail_lines[:16])
    relative = relative_path or path.name
    uri = (f"https://github.com/scikit-learn/scikit-learn/blob/{revision}/{relative}"
           if relative.startswith("sklearn/") else path.resolve().as_uri())
    return _source(key=key, path=path, uri=uri, revision=revision,
                   license_="BSD-3-Clause" if relative.startswith("sklearn/") else "unspecified",
                   start=node.lineno, end=node.end_lineno or node.lineno,
                   content=content, kind="python_ast",
                   extra={"symbol": symbol, "relative_path": relative,
                          "imports": imports, "methods": methods,
                          "signature": signature, "parse_mode": "ast-only"})


def collect_sources(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Load only approved documentation and sklearn symbols, reporting missing inputs."""
    root = Path(root).resolve()
    sources: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for key, relative, marker, uri, license_ in DOCUMENTS:
        path = root / relative
        try:
            if not path.resolve().is_relative_to(root):
                raise ValueError("Source path escapes project root")
            sources.append(read_document(path, key=key, marker=marker, uri=uri, license_=license_))
        except (OSError, ValueError) as exc:
            issues.append({"source_key": key, "error": str(exc)})
    try:
        distribution = importlib.metadata.distribution("scikit-learn")
    except importlib.metadata.PackageNotFoundError:
        issues.append({"source_key": "sklearn", "error": "scikit-learn is not installed"})
        return sources, issues
    for key, relative, symbol in PYTHON_SYMBOLS:
        try:
            sources.append(parse_python_source(
                Path(distribution.locate_file(relative)), key=key, symbol=symbol,
                relative_path=relative, revision=distribution.version,
            ))
        except (OSError, SyntaxError, ValueError) as exc:
            issues.append({"source_key": key, "error": str(exc)})
    return sources, issues


def evaluate_assertions(predictions: list[dict[str, Any]], references: list[dict[str, Any]],
                        known_source_keys: set[str] | None = None) -> dict[str, Any]:
    """Measure exact normalized triple agreement against independently curated labels.

    These are extraction-agreement metrics, not semantic truth judgments. Missing
    predictions have undefined precision (None), never a manufactured perfect score.
    The caller must keep reference assertions out of the extractor prompt.
    """
    def normalized(item: dict[str, Any]) -> tuple[str, str, str, str]:
        fields = ("subject", "predicate", "object", "source_key")
        if not all(isinstance(item.get(field), str) and item[field].strip() for field in fields):
            raise ValueError("Each assertion requires subject, predicate, object, source_key strings")
        return tuple(" ".join(item[field].casefold().split()) for field in fields)

    gold = {normalized(item) for item in references}
    proposed, invalid = set(), []
    for index, item in enumerate(predictions):
        try:
            proposed.add(normalized(item))
        except (ValueError, AttributeError) as exc:
            invalid.append({"index": index, "error": str(exc)})
    matched = proposed & gold
    precision = len(matched) / len(proposed) if proposed else None
    recall = len(matched) / len(gold) if gold else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision is not None and recall is not None and precision + recall else 0.0)
    source_rate = None
    if known_source_keys is not None and proposed:
        known = {key.casefold() for key in known_source_keys}
        source_rate = sum(item[3] in known for item in proposed) / len(proposed)
    return {"metric_definition": "exact normalized subject/predicate/object/source_key agreement",
            "reference_assertions": len(gold), "predicted_assertions": len(proposed),
            "matched_assertions": len(matched), "precision": precision, "recall": recall,
            "f1": f1, "source_key_valid_rate": source_rate, "invalid_assertions": invalid,
            "false_positives": [list(item) for item in sorted(proposed - gold)],
            "false_negatives": [list(item) for item in sorted(gold - proposed)]}
