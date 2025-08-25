from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FuseRequest(BaseModel):
    df_a: List[Dict[str, Any]] = Field(..., description="Rows for dataset A as list of records")
    df_b: List[Dict[str, Any]] = Field(..., description="Rows for dataset B as list of records")
    overlap_features: Optional[List[str]] = Field(
        default=None, description="Optional explicit overlap feature names"
    )
    targets_from_a: Optional[List[str]] = Field(
        default=None, description="Optional explicit target names sourced from A"
    )
    targets_from_b: Optional[List[str]] = Field(
        default=None, description="Optional explicit target names sourced from B"
    )
    prefer_pycaret: Optional[bool] = Field(default=True)
    random_state: Optional[int] = Field(default=42)
    # Advanced config
    cv_splits: Optional[int] = Field(default=3)
    n_estimators: Optional[int] = Field(default=300)
    use_sparse_onehot: Optional[bool] = Field(default=True)
    max_category_cardinality: Optional[int] = Field(default=100)
    warn_on_high_cardinality: Optional[bool] = Field(default=True)
    # API shaping
    return_parts: Optional[List[str]] = Field(
        default=None, description="Which parts to return: fused, a_enriched, b_enriched, metrics"
    )
    row_limit: Optional[int] = Field(default=None, ge=0)
    columns_include: Optional[List[str]] = Field(default=None)
    columns_exclude: Optional[List[str]] = Field(default=None)


class FuseResponse(BaseModel):
    fused: Optional[List[Dict[str, Any]]] = None
    a_enriched: Optional[List[Dict[str, Any]]] = None
    b_enriched: Optional[List[Dict[str, Any]]] = None
    metrics_a_to_b: Optional[Dict[str, Dict[str, float]]] = None
    metrics_b_to_a: Optional[Dict[str, Dict[str, float]]] = None

