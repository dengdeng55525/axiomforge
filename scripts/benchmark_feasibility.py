"""Measure trusted CPU baselines on validation data, without scoring final test.

This is a hand-written feasibility probe, NOT an Agent-generated-code demo.
Each model runs in a fresh process so peak RSS is interpretable per candidate.
"""

import argparse
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def worker(dataset, model_name):
    import numpy as np
    import pandas as pd
    import sklearn
    from sklearn.compose import ColumnTransformer
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, f1_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.naive_bayes import ComplementNB
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from verify_data import read_sms, text_group

    started = time.perf_counter()
    if dataset == "bank":
        config = json.loads((ROOT / "configs/bank_task.json").read_text())
        frame = pd.read_csv(ROOT / "data/raw/bank-additional-full.csv", sep=";")
        first, second = int(len(frame) * 0.6), int(len(frame) * 0.8)
        features = frame[config["allowed_features"]]
        labels = frame["y"].map({"no": 0, "yes": 1})
        x_train, x_val = features.iloc[:first], features.iloc[first:second]
        y_train, y_val = labels.iloc[:first], labels.iloc[first:second]
        numeric = list(features.select_dtypes(include="number").columns)
        categorical = [column for column in features if column not in numeric]
        transform = ColumnTransformer(
            [
                (
                    "numeric",
                    Pipeline(
                        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                    ),
                    numeric,
                ),
                ("category", OneHotEncoder(handle_unknown="ignore"), categorical),
            ]
        )
        estimators = {
            "dummy": DummyClassifier(strategy="prior"),
            "logistic": LogisticRegression(max_iter=1000, random_state=42),
            "forest": RandomForestClassifier(
                n_estimators=150, max_depth=12, min_samples_leaf=5, n_jobs=2, random_state=42
            ),
        }
        estimator = estimators[model_name]
        pipeline = Pipeline([("prepare", transform), ("model", estimator)])
        split_details = {
            "method": "original_order_60_20_20",
            "features": config["allowed_features"],
        }
    else:
        raw = read_sms(ROOT / "data/raw/SMSSpamCollection")
        groups = {}
        for label, message in raw:
            key = text_group(message)
            groups.setdefault(key, {"text": message, "labels": set()})["labels"].add(label)
        eligible = sorted(key for key, value in groups.items() if len(value["labels"]) == 1)
        group_labels = [int(next(iter(groups[key]["labels"])) == "spam") for key in eligible]
        train_ids, remainder = train_test_split(
            eligible, test_size=0.4, stratify=group_labels, random_state=42
        )
        remainder_labels = [int(next(iter(groups[key]["labels"])) == "spam") for key in remainder]
        val_ids, test_ids = train_test_split(
            remainder, test_size=0.5, stratify=remainder_labels, random_state=42
        )
        assert not set(train_ids) & set(val_ids) and not set(train_ids) & set(test_ids)
        x_train = [groups[key]["text"] for key in train_ids]
        x_val = [groups[key]["text"] for key in val_ids]
        y_train = np.array([int(next(iter(groups[key]["labels"])) == "spam") for key in train_ids])
        y_val = np.array([int(next(iter(groups[key]["labels"])) == "spam") for key in val_ids])
        estimators = {
            "dummy": DummyClassifier(strategy="prior"),
            "logistic": LogisticRegression(max_iter=1000, random_state=42),
            "nb": ComplementNB(),
        }
        pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=30000, min_df=2)),
                ("model", estimators[model_name]),
            ]
        )
        split_details = {
            "method": "normalized_text_group_dedup_stratified_60_20_20",
            "eligible_groups": len(eligible),
            "test_groups_unscored": len(test_ids),
        }
    fit_started = time.perf_counter()
    pipeline.fit(x_train, y_train)
    fit_s = time.perf_counter() - fit_started
    predict_started = time.perf_counter()
    positive_index = list(pipeline.classes_).index(1)
    scores = pipeline.predict_proba(x_val)[:, positive_index]
    predict_s = time.perf_counter() - predict_started
    result = {
        "dataset": dataset,
        "model": model_name,
        "run_kind": "trusted_manual_feasibility_baseline",
        "evaluation_split": "validation_only",
        "sealed_test_scored": False,
        "train_rows": len(y_train),
        "validation_rows": len(y_val),
        "validation_positive_rate": float(np.mean(y_val)),
        "average_precision": float(average_precision_score(y_val, scores)),
        "roc_auc": float(roc_auc_score(y_val, scores)),
        "f1_threshold_0_5": float(f1_score(y_val, scores >= 0.5, zero_division=0)),
        "fit_seconds": fit_s,
        "predict_seconds": predict_s,
        "total_seconds": time.perf_counter() - started,
        "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
        "split_details": split_details,
    }
    print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=2, metavar=("DATASET", "MODEL"))
    args = parser.parse_args()
    if args.worker:
        worker(*args.worker)
        return
    jobs = [("bank", name) for name in ["dummy", "logistic", "forest"]] + [
        ("sms", name) for name in ["dummy", "logistic", "nb"]
    ]
    reports = []
    environment = os.environ.copy()
    for variable in [
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ]:
        environment[variable] = "2"
    for dataset, name in jobs:
        result = subprocess.run(
            [sys.executable, __file__, "--worker", dataset, name],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=True,
        )
        reports.append(json.loads(result.stdout))
        print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    output = ROOT / "docs/research/baseline_results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
