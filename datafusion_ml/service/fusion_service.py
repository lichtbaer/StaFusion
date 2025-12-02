from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ..config import FusionConfig
from ..errors import OverlapError, TargetsError, ConfigurationError, ValidationError
from ..fusion import fuse_datasets
from ..web.schemas import FuseRequest, FuseResponse

logger = logging.getLogger(__name__)


def _maybe_filter_dataframe(
    df: pd.DataFrame,
    row_limit: Optional[int],
    columns_include: Optional[List[str]],
    columns_exclude: Optional[List[str]],
) -> pd.DataFrame:
    out = df
    if columns_include:
        cols = [c for c in columns_include if c in out.columns]
        if cols:
            out = out[cols]
    if columns_exclude:
        drop_cols = [c for c in columns_exclude if c in out.columns]
        if drop_cols:
            out = out.drop(columns=drop_cols)
    if row_limit is not None:
        out = out.head(row_limit)
    return out


def _validate_dataframe_input(
    records: List[Dict[str, Any]], dataset_name: str
) -> pd.DataFrame:
    """Validate and create DataFrame from records.
    
    Validates:
    - Records are not empty
    - All records have consistent keys (columns)
    - Resulting DataFrame is not empty
    
    Raises:
        ValidationError: If validation fails
    """
    if not records:
        raise ValidationError(f"{dataset_name} is empty. At least one record is required.")
    
    # Check that all records have the same keys (consistent schema)
    if len(records) > 1:
        first_keys = set(records[0].keys())
        for i, record in enumerate(records[1:], start=1):
            record_keys = set(record.keys())
            if record_keys != first_keys:
                missing = first_keys - record_keys
                extra = record_keys - first_keys
                error_msg = f"{dataset_name} has inconsistent columns at record {i}."
                if missing:
                    error_msg += f" Missing columns: {sorted(missing)}."
                if extra:
                    error_msg += f" Extra columns: {sorted(extra)}."
                raise ValidationError(error_msg)
    
    # Create DataFrame
    try:
        df = pd.DataFrame.from_records(records)
    except Exception as e:
        raise ValidationError(
            f"Failed to create DataFrame from {dataset_name}: {str(e)}"
        ) from e
    
    # Validate DataFrame is not empty
    if df.empty:
        raise ValidationError(
            f"{dataset_name} resulted in an empty DataFrame. "
            "Please ensure records contain valid data."
        )
    
    return df


def perform_fusion(req: FuseRequest) -> FuseResponse:
    # Validate input data
    df_a = _validate_dataframe_input(req.df_a, "Dataset A")
    df_b = _validate_dataframe_input(req.df_b, "Dataset B")

    config = FusionConfig(
        prefer_pycaret=req.prefer_pycaret if req.prefer_pycaret is not None else True,
        random_state=req.random_state if req.random_state is not None else 42,
    )
    # Apply advanced fields
    if req.cv_splits is not None:
        config.cv_splits = req.cv_splits
    if req.n_estimators is not None:
        config.n_estimators = req.n_estimators
    if req.use_sparse_onehot is not None:
        config.use_sparse_onehot = req.use_sparse_onehot
    if req.max_category_cardinality is not None:
        config.max_category_cardinality = req.max_category_cardinality
    if req.warn_on_high_cardinality is not None:
        config.warn_on_high_cardinality = req.warn_on_high_cardinality

    result = fuse_datasets(
        df_a=df_a,
        df_b=df_b,
        overlap_features=req.overlap_features,
        targets_from_a=req.targets_from_a,
        targets_from_b=req.targets_from_b,
        prefer_pycaret=req.prefer_pycaret if req.prefer_pycaret is not None else True,
        random_state=req.random_state if req.random_state is not None else 42,
        config=config,
    )

    wanted = set(req.return_parts or ["fused", "a_enriched", "b_enriched", "metrics"])

    response = FuseResponse()
    if "fused" in wanted:
        response.fused = _maybe_filter_dataframe(
            result.fused, req.row_limit, req.columns_include, req.columns_exclude
        ).to_dict(orient="records")
    if "a_enriched" in wanted:
        response.a_enriched = _maybe_filter_dataframe(
            result.a_enriched, req.row_limit, req.columns_include, req.columns_exclude
        ).to_dict(orient="records")
    if "b_enriched" in wanted:
        response.b_enriched = _maybe_filter_dataframe(
            result.b_enriched, req.row_limit, req.columns_include, req.columns_exclude
        ).to_dict(orient="records")
    if "metrics" in wanted:
        def _clean(d: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
            """Clean metrics dictionary by removing NaN values and converting to float.
            
            Returns empty dict if all metrics are NaN or missing.
            """
            out: Dict[str, Dict[str, float]] = {}
            for k, sub in d.items():
                cleaned = {mk: float(mv) for mk, mv in sub.items() if mv == mv}
                if cleaned:  # Only include if at least one metric is valid
                    out[k] = cleaned
            return out

        metrics_a_to_b = _clean({k: dict(v) for k, v in result.metrics_a_to_b.items()})
        metrics_b_to_a = _clean({k: dict(v) for k, v in result.metrics_b_to_a.items()})
        
        # Log warning if metrics are empty (e.g., due to insufficient data)
        if not metrics_a_to_b and result.metrics_a_to_b:
            logger.warning(
                "Metrics A->B are empty. This may indicate insufficient data for cross-validation. "
                "Consider using more data or reducing cv_splits."
            )
        if not metrics_b_to_a and result.metrics_b_to_a:
            logger.warning(
                "Metrics B->A are empty. This may indicate insufficient data for cross-validation. "
                "Consider using more data or reducing cv_splits."
            )
        
        response.metrics_a_to_b = metrics_a_to_b if metrics_a_to_b else None
        response.metrics_b_to_a = metrics_b_to_a if metrics_b_to_a else None
    return response

