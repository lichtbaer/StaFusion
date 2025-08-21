import json
from typing import Any, Dict

import pandas as pd
from fastapi.testclient import TestClient

from datafusion_ml.api import app


client = TestClient(app)


def _payload(return_parts=None, row_limit=None, columns_include=None, columns_exclude=None) -> Dict[str, Any]:
    A = pd.DataFrame({
        "age": [1, 2, 3],
        "sex": ["m", "f", "m"],
        "y": [0, 1, 0],
    })
    B = pd.DataFrame({
        "age": [2, 3, 4],
        "sex": ["f", "m", "f"],
        "x": [0.2, 0.3, 0.1],
    })
    body: Dict[str, Any] = {
        "df_a": A.to_dict(orient="records"),
        "df_b": B.to_dict(orient="records"),
        "prefer_pycaret": False,
    }
    if return_parts is not None:
        body["return_parts"] = return_parts
    if row_limit is not None:
        body["row_limit"] = row_limit
    if columns_include is not None:
        body["columns_include"] = columns_include
    if columns_exclude is not None:
        body["columns_exclude"] = columns_exclude
    return body


def test_health():
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_fuse_default():
    r = client.post("/v1/fuse", json=_payload())
    assert r.status_code == 200, r.text
    data = r.json()
    assert "fused" in data and isinstance(data["fused"], list)


def test_fuse_limits_and_parts():
    r = client.post("/v1/fuse", json=_payload(return_parts=["fused"], row_limit=2, columns_include=["age"]))
    assert r.status_code == 200
    data = r.json()
    # Only 'fused' present; other optional fields may exist but be null
    assert data.get("a_enriched") is None and data.get("b_enriched") is None
    assert data.get("metrics_a_to_b") is None and data.get("metrics_b_to_a") is None
    assert len(data["fused"]) == 2
    assert set(data["fused"][0].keys()) == {"age"}


def test_fuse_no_overlap_error():
    body = {
        "df_a": [{"a": 1, "y": 0}],
        "df_b": [{"b": 2, "x": 0.1}],
    }
    r = client.post("/v1/fuse", json=body)
    assert r.status_code == 400
