import json
from pathlib import Path

import pytest

from capability_factory.datasets import BANK_FEATURES, prepare_dataset, public_task_spec

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "dataset_id,counts", [("bank", (24712, 8238, 8238)), ("sms", (3095, 1032, 1032))]
)
def test_public_dataset_split_and_label_sealing(dataset_id, counts, tmp_path):
    file_name = "bank-additional-full.csv" if dataset_id == "bank" else "SMSSpamCollection"
    if not (ROOT / "data/raw" / file_name).is_file():
        pytest.skip("Download public datasets using scripts/verify_data.py first")
    result = prepare_dataset(dataset_id, ROOT, tmp_path)
    assert (
        result["train_rows"],
        result["validation_rows"],
        result["manifest"]["sealed_test_rows"],
    ) == counts
    train = json.loads(Path(result["train_path"]).read_text())
    features = json.loads(Path(result["validation_features_path"]).read_text())
    labels = json.loads(Path(result["validation_labels_path"]).read_text())
    assert "y" in train and "y" not in features
    assert labels["row_ids"] == features["row_ids"]
    assert not set(train["row_ids"]) & set(features["row_ids"])
    assert not list(tmp_path.glob("**/*test*.json"))
    assert result["manifest"]["sealed_test_exported"] is False
    assert result["manifest"]["sealed_test_scored"] is False
    assert "path" not in json.dumps(public_task_spec(result))
    if dataset_id == "bank":
        assert result["feature_names"] == BANK_FEATURES
        assert "duration" not in result["feature_names"]
        assert set(train["X"][0]) == set(BANK_FEATURES)
    repeated = prepare_dataset(dataset_id, ROOT, tmp_path / "repeat")
    assert repeated["manifest"] == result["manifest"]


def test_corrupted_source_is_rejected(tmp_path):
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    (raw / "bank-additional-full.csv").write_text("modified source")
    with pytest.raises(ValueError, match="checksum mismatch"):
        prepare_dataset("bank", tmp_path, tmp_path / "prepared")


def test_unknown_dataset_is_explicit_error(tmp_path):
    with pytest.raises(ValueError, match="Unsupported public dataset"):
        prepare_dataset("private-unavailable-data", tmp_path, tmp_path / "prepared")
