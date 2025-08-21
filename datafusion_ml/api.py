from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import FusionConfig
from .fusion import fuse_datasets


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


class FuseResponse(BaseModel):
    fused: List[Dict[str, Any]]
    a_enriched: List[Dict[str, Any]]
    b_enriched: List[Dict[str, Any]]
    metrics_a_to_b: Dict[str, Dict[str, float]]
    metrics_b_to_a: Dict[str, Dict[str, float]]


app = FastAPI(title="datafusion-ml API", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/fuse", response_model=FuseResponse)
def fuse(req: FuseRequest) -> FuseResponse:
    try:
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

        return FuseResponse(
            fused=result.fused.to_dict(orient="records"),
            a_enriched=result.a_enriched.to_dict(orient="records"),
            b_enriched=result.b_enriched.to_dict(orient="records"),
            metrics_a_to_b={k: dict(v) for k, v in result.metrics_a_to_b.items()},
            metrics_b_to_a={k: dict(v) for k, v in result.metrics_b_to_a.items()},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


def main() -> None:
    import uvicorn

    uvicorn.run("datafusion_ml.api:app", host="0.0.0.0", port=8000, reload=False)

