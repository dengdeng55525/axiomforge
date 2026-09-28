"""Verified public data with evaluator-only validation labels and sealed test.

Generated programs receive only feature names, train data, and validation features.
The final test is never materialized or scored by this module.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

DATASETS = {
    "uci-bank-additional-full": {
        "file": "bank-additional-full.csv",
        "sha256": "74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8",
        "source": "https://archive.ics.uci.edu/dataset/222/bank+marketing",
    },
    "uci-sms-spam": {
        "file": "SMSSpamCollection",
        "sha256": "7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d",
        "source": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection",
    },
}
BANK_FEATURES = [
    "age",
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "pdays",
    "previous",
    "poutcome",
]
BANK_NUMERIC = ["age", "pdays", "previous"]
ALIASES = {
    "bank": "uci-bank-additional-full",
    "sms": "uci-sms-spam",
    "uci-sms-spam-collection": "uci-sms-spam",
    "uci-sms-spam-collection-228": "uci-sms-spam",
}


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()


def _write_json(path: Path, value: object, private: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _json_bytes(value)
    path.write_bytes(payload)
    path.chmod(0o600 if private else 0o644)
    return _digest(payload)


def normalized_text_id(text: str) -> str:
    return _digest(" ".join(text.casefold().split()).encode())


def prepare_dataset(dataset_id: str, root: Path, destination: Path) -> dict:
    """Prepare reproducible training/validation files; never export final test.

    ``validation_labels_path`` is for the trusted host evaluator only. Do not put
    the returned dictionary wholesale into a generated-code or LLM prompt.
    Use ``public_task_spec`` when building a prompt/worker constructor context.
    """
    dataset_id = ALIASES.get(dataset_id, dataset_id)
    if dataset_id not in DATASETS:
        raise ValueError(f"Unsupported public dataset: {dataset_id}")
    root, destination = Path(root).resolve(), Path(destination).resolve()
    source = DATASETS[dataset_id]
    source_path = root / "data" / "raw" / source["file"]
    if not source_path.is_file():
        raise FileNotFoundError(
            f"Missing {source_path.name}. Run scripts/verify_data.py to download public data."
        )
    raw = source_path.read_bytes()
    if _digest(raw) != source["sha256"]:
        raise ValueError(f"Raw dataset checksum mismatch: {source_path.name}")

    if dataset_id == "uci-bank-additional-full":
        records = list(csv.DictReader(raw.decode("utf-8").splitlines(), delimiter=";"))
        if len(records) != 41188:
            raise ValueError("Unexpected bank row count")
        config_path = root / "configs" / "bank_task.json"
        if config_path.exists():
            configured = json.loads(config_path.read_text())["allowed_features"]
            if configured != BANK_FEATURES:
                raise ValueError(
                    "Bank feature policy changed; review and version the data contract"
                )
        train_end, val_end = int(len(records) * 0.6), int(len(records) * 0.8)
        train_ids = [f"bank:{i:05d}" for i in range(train_end)]
        val_ids = [f"bank:{i:05d}" for i in range(train_end, val_end)]

        def features(rows):
            return [
                {key: int(row[key]) if key in BANK_NUMERIC else row[key] for key in BANK_FEATURES}
                for row in rows
            ]

        x_train, x_val = features(records[:train_end]), features(records[train_end:val_end])
        y_train = [int(row["y"] == "yes") for row in records[:train_end]]
        y_val = [int(row["y"] == "yes") for row in records[train_end:val_end]]
        feature_names, numeric = BANK_FEATURES.copy(), BANK_NUMERIC.copy()
        task_type, positive_label = "tabular_binary_classification", "yes"
        split = "original_order_60_20_20"
        sealed_rows = len(records) - val_end
        group_details = {}
    else:
        from sklearn.model_selection import train_test_split

        groups: dict[str, dict] = {}
        raw_count = 0
        for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            label, separator, message = line.partition("\t")
            if not separator or label not in {"ham", "spam"}:
                raise ValueError(f"Invalid SMS row {line_number}")
            raw_count += 1
            key = normalized_text_id(message)
            groups.setdefault(key, {"text": message, "labels": set()})["labels"].add(label)
        eligible = sorted(key for key, value in groups.items() if len(value["labels"]) == 1)
        labels = [int(next(iter(groups[key]["labels"])) == "spam") for key in eligible]
        train_ids, remainder = train_test_split(
            eligible, test_size=0.4, stratify=labels, random_state=42
        )
        remainder_labels = [int(next(iter(groups[key]["labels"])) == "spam") for key in remainder]
        val_ids, sealed_ids = train_test_split(
            remainder, test_size=0.5, stratify=remainder_labels, random_state=42
        )
        if set(train_ids) & set(val_ids) or set(train_ids + val_ids) & set(sealed_ids):
            raise ValueError("Normalized SMS groups overlap across splits")
        x_train = [groups[key]["text"] for key in train_ids]
        x_val = [groups[key]["text"] for key in val_ids]
        y_train = [int(next(iter(groups[key]["labels"])) == "spam") for key in train_ids]
        y_val = [int(next(iter(groups[key]["labels"])) == "spam") for key in val_ids]
        feature_names, numeric = ["text"], []
        task_type, positive_label = "text_binary_classification", "spam"
        split = "normalized_text_group_dedup_stratified_60_20_20"
        sealed_rows = len(sealed_ids)
        group_details = {
            "raw_rows": raw_count,
            "normalized_groups": len(groups),
            "conflicting_groups_excluded": len(groups) - len(eligible),
            "train_group_ids_sha256": _digest(_json_bytes(train_ids)),
            "validation_group_ids_sha256": _digest(_json_bytes(val_ids)),
            "sealed_group_ids_sha256": _digest(_json_bytes(sealed_ids)),
        }

    paths = {
        "train": destination / "worker" / "train.json",
        "validation_features": destination / "worker" / "validation_features.json",
        "validation_labels": destination / "evaluator" / "validation_labels.json",
        "manifest": destination / "manifest.json",
    }
    hashes = {
        "train": _write_json(paths["train"], {"row_ids": train_ids, "X": x_train, "y": y_train}),
        "validation_features": _write_json(
            paths["validation_features"], {"row_ids": val_ids, "X": x_val}
        ),
        "validation_labels": _write_json(
            paths["validation_labels"], {"row_ids": val_ids, "y": y_val}, private=True
        ),
    }
    manifest = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "source_url": source["source"],
        "license": "CC BY 4.0",
        "raw_sha256": source["sha256"],
        "split_policy": split,
        "split_seed": 42,
        "train_rows": len(train_ids),
        "validation_rows": len(val_ids),
        "sealed_test_rows": sealed_rows,
        "sealed_test_exported": False,
        "sealed_test_scored": False,
        "validation_labels_visible_to_generated_code": False,
        "preprocessing_fit_split": "train_only",
        "feature_policy": "precontact_conservative_v1" if numeric else "text_only_group_dedup_v1",
        "feature_names": feature_names,
        "numeric_features": numeric,
        "file_sha256": hashes,
        **group_details,
    }
    _write_json(paths["manifest"], manifest)
    return {
        "dataset_id": dataset_id,
        "task_type": task_type,
        "train_rows": len(train_ids),
        "validation_rows": len(val_ids),
        "feature_names": feature_names,
        "numeric_features": numeric,
        "categorical_features": [name for name in feature_names if name not in numeric],
        "positive_label": positive_label,
        "train_positive_rate": sum(y_train) / len(y_train),
        "manifest": manifest,
        "paths": {key: str(value) for key, value in paths.items()},
        "train_path": str(paths["train"]),
        "validation_features_path": str(paths["validation_features"]),
        "validation_labels_path": str(paths["validation_labels"]),
    }


def public_task_spec(dataset: dict, task_spec: dict | None = None) -> dict:
    """Only expose constructor context, never paths, labels, or test data."""
    task_spec = task_spec or {}
    return {
        "task_type": dataset["task_type"],
        "feature_names": list(dataset["feature_names"]),
        "numeric_features": list(dataset["numeric_features"]),
        "categorical_features": list(dataset["categorical_features"]),
        "positive_label": dataset["positive_label"],
        "seed": int(task_spec.get("seed", 42)),
    }
