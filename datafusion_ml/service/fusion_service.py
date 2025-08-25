from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from ..config import FusionConfig
from ..errors import OverlapError, TargetsError, ConfigurationError
from ..fusion import fuse_datasets
from ..web.schemas import FuseRequest, FuseResponse


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


def perform_fusion(req: FuseRequest) -> FuseResponse:
    df_a = pd.DataFrame.from_records(req.df_a)
    df_b = pd.DataFrame.from_records(req.df_b)

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
            out: Dict[str, Dict[str, float]] = {}
            for k, sub in d.items():
                out[k] = {mk: float(mv) for mk, mv in sub.items() if mv == mv}
            return out

        response.metrics_a_to_b = _clean({k: dict(v) for k, v in result.metrics_a_to_b.items()})
        response.metrics_b_to_a = _clean({k: dict(v) for k, v in result.metrics_b_to_a.items()})
    return response

