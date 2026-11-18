"""Pipeline tests. They never hard-code the row count, so they keep passing
when the grader appends more rows to dataset/train.csv."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text())


@pytest.fixture(scope="module", autouse=True)
def trained():
    """Run from the repo root and make sure a model exists."""
    old = Path.cwd()
    os.chdir(ROOT)
    if not (ROOT / "artifacts" / "metrics.json").exists():
        subprocess.run([sys.executable, "train.py"], check=True, cwd=ROOT)
    yield
    os.chdir(old)


@pytest.fixture(scope="module")
def client():
    from app import app
    return TestClient(app)


def test_dataset_columns_and_rows():
    df = pd.read_csv(ROOT / "dataset" / "train.csv")
    assert set(CONFIG["features"] + ["label"]).issubset(df.columns)
    assert len(df) >= 100
    assert df["label"].nunique() == 2


def test_accuracy_above_threshold():
    metrics = json.loads((ROOT / "artifacts" / "metrics.json").read_text())
    assert metrics["accuracy"] > 0.6


def test_metrics_endpoint(client):
    body = client.get("/metrics").json()
    for field in ["student_id", "accuracy", "training_rows", "model_version", "git_sha"]:
        assert field in body
    assert body["student_id"] == CONFIG["student_id"]
    assert body["accuracy"] > 0.6
    rows = len(pd.read_csv(ROOT / "dataset" / "train.csv"))
    assert body["training_rows"] == rows


def test_predict_endpoint(client):
    record = {name: 0.1 for name in CONFIG["features"]}
    response = client.post("/predict", json={"records": [record, record]})
    assert response.status_code == 200
    body = response.json()
    assert len(body["predictions"]) == 2
    assert all(p in (0, 1) for p in body["predictions"])
    assert all(0.0 <= p <= 1.0 for p in body["probabilities"])
