from __future__ import annotations

import io
import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow.parquet as pq
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from ...service.fusion_service import perform_fusion
from ..config import APISettings
from ..schemas import FuseRequest, FuseResponse


router = APIRouter()
logger = logging.getLogger(__name__)

# Job store with TTL (Time To Live) in seconds
# Jobs older than JOB_TTL_SECONDS will be automatically cleaned up
JOB_TTL_SECONDS = 3600  # 1 hour default
_JOB_STORE: Dict[str, Dict[str, Any]] = {}
_JOB_TIMESTAMPS: Dict[str, float] = {}
# Lock for thread-safe access to job store
_JOB_STORE_LOCK = threading.Lock()


def _cleanup_old_jobs() -> None:
    """Remove jobs older than JOB_TTL_SECONDS from the store.
    
    This function is thread-safe and should be called regularly to prevent
    memory leaks from accumulating old job data.
    """
    with _JOB_STORE_LOCK:
        current_time = time.time()
        expired_jobs = [
            job_id
            for job_id, timestamp in _JOB_TIMESTAMPS.items()
            if current_time - timestamp > JOB_TTL_SECONDS
        ]
        if expired_jobs:
            logger.info(f"Cleaning up {len(expired_jobs)} expired job(s)")
            for job_id in expired_jobs:
                _JOB_STORE.pop(job_id, None)
                _JOB_TIMESTAMPS.pop(job_id, None)


@router.post("/fuse", response_model=FuseResponse)
def fuse(req: FuseRequest) -> FuseResponse:
    settings = APISettings.from_env()
    # Enforce row limit from settings if provided
    if req.row_limit is not None and req.row_limit > settings.max_rows:
        raise HTTPException(status_code=413, detail="Row limit exceeds configured maximum")
    return perform_fusion(req)


def _run_fusion_job(job_id: str, req: FuseRequest) -> None:
    """Run fusion job in background and update job store."""
    try:
        result = perform_fusion(req)
        with _JOB_STORE_LOCK:
            _JOB_STORE[job_id] = {"status": "done", "result": result.model_dump()}  # type: ignore[attr-defined]
            _JOB_TIMESTAMPS[job_id] = time.time()
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:  # noqa: BLE001
        with _JOB_STORE_LOCK:
            _JOB_STORE[job_id] = {"status": "error", "error": str(e)}
            _JOB_TIMESTAMPS[job_id] = time.time()
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)


@router.post("/fuse/async")
def fuse_async(req: FuseRequest, tasks: BackgroundTasks) -> Dict[str, str]:
    """Create a new async fusion job."""
    # Cleanup old jobs before creating new one
    _cleanup_old_jobs()
    
    job_id = str(uuid.uuid4())
    with _JOB_STORE_LOCK:
        _JOB_STORE[job_id] = {"status": "pending"}
        _JOB_TIMESTAMPS[job_id] = time.time()
    tasks.add_task(_run_fusion_job, job_id, req)
    logger.info(f"Created async job {job_id}")
    return {"job_id": job_id}


@router.get("/fuse/async/{job_id}")
def fuse_async_status(job_id: str) -> Dict[str, Any]:
    """Get status of an async fusion job."""
    # Cleanup old jobs on access
    _cleanup_old_jobs()
    
    with _JOB_STORE_LOCK:
        data = _JOB_STORE.get(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return data


def _validate_file_size(file_bytes: bytes, max_size_mb: int) -> None:
    """Validate file size before processing."""
    max_bytes = max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({len(file_bytes) / 1024 / 1024:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
        )


def _detect_file_type(file_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Detect file type using magic numbers and filename.
    Returns 'parquet' or 'csv'.
    
    Magic numbers are checked first for security, filename is only used as fallback.
    """
    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="File is empty")
    
    # Parquet magic number: first 4 bytes are "PAR1" (0x50415231)
    if len(file_bytes) >= 4 and file_bytes[:4] == b"PAR1":
        return "parquet"
    
    # Check for other binary formats that should be rejected
    # Excel files (XLSX starts with PK\x03\x04 - ZIP signature)
    if len(file_bytes) >= 4 and file_bytes[:2] == b"PK":
        raise HTTPException(
            status_code=422,
            detail="Excel files (.xlsx, .xls) are not supported. Please convert to CSV or Parquet."
        )
    
    # Check filename as fallback (less secure, but helpful for user experience)
    if filename:
        filename_lower = filename.lower()
        if filename_lower.endswith(".parquet"):
            # If filename suggests parquet but magic number doesn't match, warn
            logger.warning(f"Filename suggests Parquet but magic number doesn't match: {filename}")
            return "parquet"
        if filename_lower.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=422,
                detail="Excel files are not supported. Please convert to CSV or Parquet."
            )
    
    # Default to CSV - basic validation will happen during read
    return "csv"


def _read_csv(file_bytes: bytes) -> pd.DataFrame:
    """Read CSV file with error handling and validation.
    
    Validates that the file is actually a CSV by attempting to parse it.
    """
    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="CSV file is empty")
    
    # Basic CSV validation: should contain at least one newline or comma
    # This helps catch cases where binary files are misidentified as CSV
    try:
        # Try to decode as UTF-8 first (most common encoding)
        text_preview = file_bytes[:1024].decode('utf-8', errors='ignore')
        if not any(c in text_preview for c in [',', ';', '\t', '\n', '\r']):
            raise HTTPException(
                status_code=422,
                detail="File does not appear to be a valid CSV (no delimiters found). "
                       "Please ensure the file is a CSV or Parquet file."
            )
    except UnicodeDecodeError:
        # If we can't decode as UTF-8, it's likely not a text file
        raise HTTPException(
            status_code=422,
            detail="File does not appear to be a valid CSV (not UTF-8 text). "
                   "Please ensure the file is a CSV or Parquet file."
        )
    
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        if df.empty:
            raise HTTPException(status_code=422, detail="CSV file contains no data rows")
        return df
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=422, detail="CSV file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid CSV format: {str(e)}. Please check the file format and encoding."
        )
    except MemoryError:
        raise HTTPException(
            status_code=413,
            detail="CSV file is too large to process. Please reduce file size or use Parquet format."
        )
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error reading CSV file: {str(e)}. Please verify the file is a valid CSV."
        )


def _read_parquet(file_bytes: bytes) -> pd.DataFrame:
    """Read Parquet file with error handling and validation.
    
    Validates that the file is actually a Parquet file by attempting to parse it.
    """
    if len(file_bytes) < 4:
        raise HTTPException(status_code=422, detail="Parquet file is too small or corrupted")
    
    # Verify magic number again (defense in depth)
    if file_bytes[:4] != b"PAR1":
        raise HTTPException(
            status_code=422,
            detail="File does not have Parquet magic number. Please ensure the file is a valid Parquet file."
        )
    
    try:
        table = pq.read_table(io.BytesIO(file_bytes))
        df = table.to_pandas()
        if df.empty:
            raise HTTPException(status_code=422, detail="Parquet file contains no data rows")
        return df
    except MemoryError:
        raise HTTPException(
            status_code=413,
            detail="Parquet file is too large to process. Please reduce file size."
        )
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error reading Parquet file: {str(e)}. Please verify the file is a valid Parquet file."
        )


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
    settings = APISettings.from_env()
    max_file_size_mb = settings.max_body_mb
    
    # Read and validate file A
    content_a = await file_a.read()
    if not content_a:
        raise HTTPException(status_code=422, detail="File A is empty")
    _validate_file_size(content_a, max_file_size_mb)
    
    # Read and validate file B
    content_b = await file_b.read()
    if not content_b:
        raise HTTPException(status_code=422, detail="File B is empty")
    _validate_file_size(content_b, max_file_size_mb)
    
    # Detect file types using magic numbers
    file_type_a = _detect_file_type(content_a, file_a.filename)
    file_type_b = _detect_file_type(content_b, file_b.filename)
    
    # Read files based on detected type
    if file_type_a == "parquet":
        df_a = _read_parquet(content_a)
    else:
        df_a = _read_csv(content_a)
    
    if file_type_b == "parquet":
        df_b = _read_parquet(content_b)
    else:
        df_b = _read_csv(content_b)
    
    # Validate DataFrames are not empty
    if df_a.empty:
        raise HTTPException(status_code=422, detail="Dataset A is empty after parsing")
    if df_b.empty:
        raise HTTPException(status_code=422, detail="Dataset B is empty after parsing")

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

