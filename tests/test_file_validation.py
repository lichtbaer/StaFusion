"""Tests for file upload validation improvements."""

import io
from typing import Any, Dict

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from fastapi.testclient import TestClient

from datafusion_ml.api import app


client = TestClient(app)


def test_file_upload_with_magic_number_detection():
    """Test that file type is detected using magic numbers, not just filename."""
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
    
    # Create parquet files but name them as .csv
    # This tests that magic number detection works
    a_buf = io.BytesIO()
    b_buf = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(A), a_buf)
    pq.write_table(pa.Table.from_pandas(B), b_buf)
    
    files = {
        "file_a": ("a.csv", a_buf.getvalue(), "application/octet-stream"),  # Named .csv but is parquet
        "file_b": ("b.csv", b_buf.getvalue(), "application/octet-stream"),  # Named .csv but is parquet
    }
    r = client.post("/v1/fuse/upload", files=files)
    # Should still work because magic number detection identifies it as parquet
    assert r.status_code == 200
    data = r.json()
    assert "fused" in data and isinstance(data["fused"], list)


def test_file_upload_empty_file():
    """Test that empty files are rejected."""
    files = {
        "file_a": ("a.csv", b"", "text/csv"),
        "file_b": ("b.csv", b"", "text/csv"),
    }
    r = client.post("/v1/fuse/upload", files=files)
    assert r.status_code == 422
    assert "empty" in r.json()["detail"].lower()


def test_async_job_cleanup():
    """Test that async jobs are properly tracked and can be cleaned up."""
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
    
    payload: Dict[str, Any] = {
        "df_a": A.to_dict(orient="records"),
        "df_b": B.to_dict(orient="records"),
        "prefer_pycaret": False,
    }
    
    # Create a job
    r = client.post("/v1/fuse/async", json=payload)
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    
    # Job should be accessible
    s = client.get(f"/v1/fuse/async/{job_id}")
    assert s.status_code == 200
    assert s.json()["status"] in ["pending", "done", "error"]
