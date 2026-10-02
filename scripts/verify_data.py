"""Download public UCI archives and record reproducible, non-sensitive audits.

Uses only the standard library. Archive members are read by exact name, never
extracted as arbitrary filesystem paths. Raw datasets stay outside Git.
"""

import csv
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SOURCES = {
    "bank": "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip",
    "sms": "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
}
ARCHIVE_SHA256 = {
    "bank": "e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4",
    "sms": "1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3",
}
MAX_BYTES = 20 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def download(url, target, expected_sha256):
    if target.exists():
        payload = target.read_bytes()
        if sha256(payload) != expected_sha256:
            raise ValueError("Cached archive checksum mismatch; do not replace silently")
        return payload
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AxiomForge-Research/0.1"})
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                raise ValueError("Archive exceeds configured maximum size")
            if sha256(payload) != expected_sha256:
                raise ValueError("Downloaded archive checksum mismatch; investigate source version")
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                if sum(item.file_size for item in archive.infolist()) > MAX_BYTES:
                    raise ValueError("Expanded archive exceeds configured maximum size")
            temporary = target.with_suffix(".part")
            temporary.write_bytes(payload)
            temporary.replace(target)
            return payload
        except (OSError, ValueError, zipfile.BadZipFile):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Unreachable download state")


def read_sms(path):
    """Preserve raw text and split only on the first tab; no CSV quote guessing."""
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        label, separator, message = line.partition("\t")
        if not separator or label not in {"ham", "spam"}:
            raise ValueError(f"Invalid SMS record at line {number}")
        records.append((label, message))
    return records


def text_group(text):
    return sha256(" ".join(text.casefold().split()).encode("utf-8"))


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    result = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "datasets": {}}
    bank_zip = download(SOURCES["bank"], RAW / "bank-marketing.zip", ARCHIVE_SHA256["bank"])
    with zipfile.ZipFile(io.BytesIO(bank_zip)) as outer:
        additional = outer.read("bank-additional.zip")
    with zipfile.ZipFile(io.BytesIO(additional)) as inner:
        bank_bytes = inner.read("bank-additional/bank-additional-full.csv")
        bank_names = inner.read("bank-additional/bank-additional-names.txt")
    (RAW / "bank-additional-full.csv").write_bytes(bank_bytes)
    (RAW / "bank-additional-names.txt").write_bytes(bank_names)
    bank = list(csv.DictReader(io.StringIO(bank_bytes.decode("utf-8")), delimiter=";"))
    if len(bank) != 41188 or len(bank[0]) != 21:
        raise ValueError("Unexpected bank dataset shape; investigate source version")
    counts = Counter(row["y"] for row in bank)
    split_a, split_b = int(len(bank) * 0.6), int(len(bank) * 0.8)
    result["datasets"]["bank"] = {
        "download_url": SOURCES["bank"],
        "license_at_source": "CC BY 4.0",
        "archive_sha256": sha256(bank_zip),
        "csv_sha256": sha256(bank_bytes),
        "rows": len(bank),
        "columns_including_target": len(bank[0]),
        "columns": list(bank[0]),
        "target_counts": dict(counts),
        "positive_rate": counts["yes"] / len(bank),
        "exact_duplicate_rows": len(bank) - len({tuple(row.values()) for row in bank}),
        "raw_bytes": len(bank_bytes),
        "split_policy": "original order: first 60% train, next 20% validation, final 20% sealed test",
        "split_rows": {
            "train": split_a,
            "validation": split_b - split_a,
            "sealed_test": len(bank) - split_b,
        },
        "test_model_metrics_computed": False,
    }
    sms_zip = download(SOURCES["sms"], RAW / "sms-spam.zip", ARCHIVE_SHA256["sms"])
    with zipfile.ZipFile(io.BytesIO(sms_zip)) as archive:
        sms_bytes = archive.read("SMSSpamCollection")
        (RAW / "sms-readme.txt").write_bytes(archive.read("readme"))
    sms_path = RAW / "SMSSpamCollection"
    sms_path.write_bytes(sms_bytes)
    sms = read_sms(sms_path)
    groups = defaultdict(set)
    for label, message in sms:
        groups[text_group(message)].add(label)
    result["datasets"]["sms"] = {
        "download_url": SOURCES["sms"],
        "license_at_source": "CC BY 4.0",
        "archive_sha256": sha256(sms_zip),
        "text_sha256": sha256(sms_bytes),
        "parsed_rows": len(sms),
        "official_page_rows": 5574,
        "parser": "UTF-8 splitlines; first tab separates label from unchanged text",
        "target_counts": dict(Counter(label for label, _ in sms)),
        "normalized_text_groups": len(groups),
        "conflicting_label_groups": sum(len(labels) > 1 for labels in groups.values()),
        "exact_duplicate_rows": len(sms) - len(set(sms)),
        "raw_bytes": len(sms_bytes),
        "test_model_metrics_computed": False,
    }
    destination = ROOT / "docs" / "research" / "data_audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
