import io
import os
import time
from typing import Any, Dict

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from fastapi.testclient import TestClient

from datafusion_ml.api import app


client = TestClient(app)


def _payload_small() -> Dict[str, Any]:
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
    return {
        "df_a": A.to_dict(orient="records"),
        "df_b": B.to_dict(orient="records"),
        "prefer_pycaret": False,
    }


def test_metrics_endpoint():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")


def test_file_upload_csv():
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
    a_buf = io.BytesIO()
    b_buf = io.BytesIO()
    A.to_csv(a_buf, index=False)
    B.to_csv(b_buf, index=False)
    files = {
        "file_a": ("a.csv", a_buf.getvalue(), "text/csv"),
        "file_b": ("b.csv", b_buf.getvalue(), "text/csv"),
    }
    r = client.post("/v1/fuse/upload", files=files)
    assert r.status_code == 200
    data = r.json()
    assert "fused" in data and isinstance(data["fused"], list)


def test_file_upload_parquet():
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
    a_buf = io.BytesIO()
    b_buf = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(A), a_buf)
    pq.write_table(pa.Table.from_pandas(B), b_buf)
    files = {
        "file_a": ("a.parquet", a_buf.getvalue(), "application/octet-stream"),
        "file_b": ("b.parquet", b_buf.getvalue(), "application/octet-stream"),
    }
    r = client.post("/v1/fuse/upload", files=files)
    assert r.status_code == 200
    data = r.json()
    assert "fused" in data and isinstance(data["fused"], list)


def test_async_processing():
    r = client.post("/v1/fuse/async", json=_payload_small())
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    # Poll for completion
    for _ in range(50):
        s = client.get(f"/v1/fuse/async/{job_id}")
        assert s.status_code == 200
        body = s.json()
        if body.get("status") == "done":
            assert "result" in body
            assert "fused" in body["result"]
            break
        time.sleep(0.05)
    else:
        assert False, "async job did not complete in time"


def test_row_limit_exceeds_max(monkeypatch):
    monkeypatch.setenv("DFML_MAX_ROWS", "1")
    body = _payload_small()
    body["row_limit"] = 10
    r = client.post("/v1/fuse", json=body)
    assert r.status_code == 413
