from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, Field

from .config import FusionConfig
from .fusion import fuse_datasets
from .errors import OverlapError, TargetsError, ConfigurationError


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


app = FastAPI(title="datafusion-ml API", version="0.1.0")
router = APIRouter(prefix="/v1")


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/fuse", response_model=FuseResponse)
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
        # Select parts
        wanted = set(req.return_parts or ["fused", "a_enriched", "b_enriched", "metrics"])

        def maybe_filter(df: pd.DataFrame) -> pd.DataFrame:
            out = df
            if req.columns_include:
                cols = [c for c in req.columns_include if c in out.columns]
                if cols:
                    out = out[cols]
            if req.columns_exclude:
                drop_cols = [c for c in req.columns_exclude if c in out.columns]
                if drop_cols:
                    out = out.drop(columns=drop_cols)
            if req.row_limit is not None:
                out = out.head(req.row_limit)
            return out

        response = FuseResponse()
        if "fused" in wanted:
            response.fused = maybe_filter(result.fused).to_dict(orient="records")
        if "a_enriched" in wanted:
            response.a_enriched = maybe_filter(result.a_enriched).to_dict(orient="records")
        if "b_enriched" in wanted:
            response.b_enriched = maybe_filter(result.b_enriched).to_dict(orient="records")
        if "metrics" in wanted:
            def _clean(d: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
                out: Dict[str, Dict[str, float]] = {}
                for k, sub in d.items():
                    out[k] = {mk: float(mv) for mk, mv in sub.items() if mv == mv}
                return out
            response.metrics_a_to_b = _clean({k: dict(v) for k, v in result.metrics_a_to_b.items()})
            response.metrics_b_to_a = _clean({k: dict(v) for k, v in result.metrics_b_to_a.items()})
        return response
    except OverlapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TargetsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConfigurationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


app.include_router(router)


# Backwards-compatible unversioned routes
app.get("/health")(health)
app.post("/fuse")(fuse)


def main() -> None:
    import uvicorn

    uvicorn.run("datafusion_ml.api:app", host="0.0.0.0", port=8000, reload=False)

