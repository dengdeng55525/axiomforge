"""Check parsing and the two leakage controls used in feasibility preparation."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_data", ROOT / "scripts/verify_data.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_sms_preserves_tabs_and_quotes(tmp_path):
    path = tmp_path / "sms"
    path.write_text('ham\tHello\t"there"\nspam\tOffer\n', encoding="utf-8")
    assert MODULE.read_sms(path) == [("ham", 'Hello\t"there"'), ("spam", "Offer")]


def test_sms_rejects_invalid_labels(tmp_path):
    path = tmp_path / "sms"
    path.write_text("invalid\tmessage\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid SMS record"):
        MODULE.read_sms(path)


def test_equivalent_sms_share_split_group():
    assert MODULE.text_group("Hello   WORLD") == MODULE.text_group("hello world")


def test_modified_cache_is_rejected_without_network(tmp_path):
    archive = tmp_path / "cached.zip"
    archive.write_bytes(b"modified payload")
    with pytest.raises(ValueError, match="checksum mismatch"):
        MODULE.download("https://example.invalid/never-requested", archive, "0" * 64)


def test_bank_precontact_policy():
    config = json.loads((ROOT / "configs/bank_task.json").read_text())
    assert not set(config["allowed_features"]) & set(config["forbidden_features"])
    assert {"duration", "campaign"} <= set(config["forbidden_features"])
    assert "y" not in config["allowed_features"]
    assert sum(
        config["split"][key] for key in ["train_fraction", "validation_fraction", "test_fraction"]
    ) == pytest.approx(1.0)
