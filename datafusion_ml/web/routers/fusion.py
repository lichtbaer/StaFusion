from __future__ import annotations

import io
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from ...service.fusion_service import perform_fusion
from ..config import APISettings
from ..schemas import FuseRequest, FuseResponse


router = APIRouter()


@router.post("/fuse", response_model=FuseResponse)
def fuse(req: FuseRequest) -> FuseResponse:
    settings = APISettings.from_env()
    # Enforce row limit from settings if provided
    if req.row_limit is not None and req.row_limit > settings.max_rows:
        raise HTTPException(status_code=413, detail="Row limit exceeds configured maximum")
    return perform_fusion(req)


_JOB_STORE: Dict[str, Dict[str, Any]] = {}


def _run_fusion_job(job_id: str, req: FuseRequest) -> None:
    try:
        result = perform_fusion(req)
        _JOB_STORE[job_id] = {"status": "done", "result": result.model_dump()}  # type: ignore[attr-defined]
    except Exception as e:  # noqa: BLE001
        _JOB_STORE[job_id] = {"status": "error", "error": str(e)}


@router.post("/fuse/async")
def fuse_async(req: FuseRequest, tasks: BackgroundTasks) -> Dict[str, str]:
    job_id = str(uuid.uuid4())
    _JOB_STORE[job_id] = {"status": "pending"}
    tasks.add_task(_run_fusion_job, job_id, req)
    return {"job_id": job_id}


@router.get("/fuse/async/{job_id}")
def fuse_async_status(job_id: str) -> Dict[str, Any]:
    data = _JOB_STORE.get(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return data


def _read_csv(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(file_bytes))


def _read_parquet(file_bytes: bytes) -> pd.DataFrame:
    table = pq.read_table(io.BytesIO(file_bytes))
    return table.to_pandas()


@router.post("/fuse/upload", response_model=FuseResponse)
async def fuse_upload(
    file_a: UploadFile = File(..., description="CSV or Parquet for dataset A"),
    file_b: UploadFile = File(..., description="CSV or Parquet for dataset B"),
    overlap_features: Optional[List[str]] = None,
    targets_from_a: Optional[List[str]] = None,
    targets_from_b: Optional[List[str]] = None,
    prefer_pycaret: Optional[bool] = True,
    random_state: Optional[int] = 42,
    return_parts: Optional[List[str]] = None,
    row_limit: Optional[int] = None,
    columns_include: Optional[List[str]] = None,
    columns_exclude: Optional[List[str]] = None,
) -> FuseResponse:
    # Determine types by filename
    content_a = await file_a.read()
    content_b = await file_b.read()

    if file_a.filename.endswith(".parquet"):
        df_a = _read_parquet(content_a)
    else:
        df_a = _read_csv(content_a)

    if file_b.filename.endswith(".parquet"):
        df_b = _read_parquet(content_b)
    else:
        df_b = _read_csv(content_b)

    # Convert to records for reuse of service logic
    req = FuseRequest(
        df_a=df_a.to_dict(orient="records"),
        df_b=df_b.to_dict(orient="records"),
        overlap_features=overlap_features,
        targets_from_a=targets_from_a,
        targets_from_b=targets_from_b,
        prefer_pycaret=prefer_pycaret,
        random_state=random_state,
        return_parts=return_parts,
        row_limit=row_limit,
        columns_include=columns_include,
        columns_exclude=columns_exclude,
    )
    return perform_fusion(req)

