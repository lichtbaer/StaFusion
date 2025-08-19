from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, cast
import logging

import pandas as pd

from .modeling import (
    ProblemType,
    TrainedModel,
    detect_problem_type,
    predict,
    train_model,
    cross_validate_metrics,
    ClassificationMetrics,
    RegressionMetrics,
)
from .config import FusionConfig


@dataclass
class FusionResult:
    fused: pd.DataFrame
    a_enriched: pd.DataFrame
    b_enriched: pd.DataFrame
    models_a_to_b: Dict[str, TrainedModel]
    models_b_to_a: Dict[str, TrainedModel]
    metrics_a_to_b: Dict[str, ClassificationMetrics | RegressionMetrics]
    metrics_b_to_a: Dict[str, ClassificationMetrics | RegressionMetrics]


logger = logging.getLogger(__name__)


def _infer_overlap_features(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    exclude: Optional[Iterable[str]] = None,
) -> List[str]:
    exclude_set = set(exclude or [])
    overlap = sorted((set(df_a.columns) & set(df_b.columns)) - exclude_set)
    return overlap


def _exclusive_columns(df_left: pd.DataFrame, df_right: pd.DataFrame) -> List[str]:
    return sorted(list(set(df_left.columns) - set(df_right.columns)))


def _coerce_categorical_alignment(
    a: pd.DataFrame, b: pd.DataFrame, columns: Sequence[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    a_aligned = a.copy()
    b_aligned = b.copy()
    for c in columns:
        if pd.api.types.is_object_dtype(a_aligned[c]) or pd.api.types.is_categorical_dtype(a_aligned[c]) or pd.api.types.is_object_dtype(b_aligned[c]) or pd.api.types.is_categorical_dtype(b_aligned[c]):
            cats = pd.Index(sorted(pd.unique(pd.concat([a_aligned[c], b_aligned[c]], ignore_index=True).dropna())))
            a_aligned[c] = a_aligned[c].astype(pd.CategoricalDtype(categories=cats))
            b_aligned[c] = b_aligned[c].astype(pd.CategoricalDtype(categories=cats))
    return a_aligned, b_aligned


def fuse_datasets(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    overlap_features: Optional[Sequence[str]] = None,
    targets_from_a: Optional[Sequence[str]] = None,
    targets_from_b: Optional[Sequence[str]] = None,
    problem_type_map: Optional[Dict[str, ProblemType]] = None,
    prefer_pycaret: bool = True,
    random_state: int = 42,
    *,
    config: Optional[FusionConfig] = None,
) -> FusionResult:
    # Build merged config with backward-compatibility to existing args
    if config is None:
        config = FusionConfig(
            prefer_pycaret=prefer_pycaret,
            random_state=random_state,
        )

    if overlap_features is None:
        exclude = set(targets_from_a or []) | set(targets_from_b or [])
        overlap_features = _infer_overlap_features(df_a, df_b, exclude=exclude)
    else:
        overlap_features = [c for c in overlap_features if c in df_a.columns and c in df_b.columns]

    if len(overlap_features) == 0:
        raise ValueError("No overlapping features between A and B (after exclusions). Provide overlap_features explicitly or ensure datasets share columns.")

    if targets_from_a is None:
        targets_from_a = _exclusive_columns(df_a, df_b)
    if targets_from_b is None:
        targets_from_b = _exclusive_columns(df_b, df_a)

    if not targets_from_a and not targets_from_b:
        raise ValueError("No exclusive target columns detected in either dataset. Specify targets_from_a/targets_from_b.")

    # Align categorical levels across overlap features
    a_feat, b_feat = _coerce_categorical_alignment(
        df_a[overlap_features], df_b[overlap_features], overlap_features
    )

    # Cardinality checks
    if config.warn_on_high_cardinality:
        for col in overlap_features:
            if not pd.api.types.is_numeric_dtype(a_feat[col]):
                cardinality = int(pd.Index(pd.concat([a_feat[col], b_feat[col]], ignore_index=True).dropna().unique()).size)
                if cardinality > config.max_category_cardinality:
                    logger.warning(
                        "High cardinality detected for column '%s': %d categories (threshold=%d). Consider enabling sparse one-hot or reducing categories.",
                        col,
                        cardinality,
                        config.max_category_cardinality,
                    )

    # Train models A -> B
    models_a_to_b: Dict[str, TrainedModel] = {}
    metrics_a_to_b: Dict[str, ClassificationMetrics | RegressionMetrics] = {}
    b_pred = df_b.copy()
    for target in targets_from_a:
        y = df_a[target]
        problem = (problem_type_map or {}).get(target) or detect_problem_type(y)
        model = train_model(a_feat, y, problem_type=problem, config=config)
        models_a_to_b[target] = model
        # Evaluate via sklearn CV for consistency
        metrics_a_to_b[target] = cast(ClassificationMetrics | RegressionMetrics, cross_validate_metrics(a_feat, y, problem, config=config))
        preds = predict(model, b_feat)
        col_name = target if target not in b_pred.columns else f"{target}_pred"
        b_pred[col_name] = preds

    # Train models B -> A
    models_b_to_a: Dict[str, TrainedModel] = {}
    metrics_b_to_a: Dict[str, ClassificationMetrics | RegressionMetrics] = {}
    a_pred = df_a.copy()
    for target in targets_from_b:
        y = df_b[target]
        problem = (problem_type_map or {}).get(target) or detect_problem_type(y)
        model = train_model(b_feat, y, problem_type=problem, config=config)
        models_b_to_a[target] = model
        metrics_b_to_a[target] = cast(ClassificationMetrics | RegressionMetrics, cross_validate_metrics(b_feat, y, problem, config=config))
        preds = predict(model, a_feat)
        col_name = target if target not in a_pred.columns else f"{target}_pred"
        a_pred[col_name] = preds

    # Create fused dataset: union of columns and vertical concat
    all_columns = sorted(list(set(a_pred.columns) | set(b_pred.columns)))
    fused = pd.concat([
        a_pred.reindex(columns=all_columns),
        b_pred.reindex(columns=all_columns),
    ], ignore_index=True)

    return FusionResult(
        fused=fused,
        a_enriched=a_pred,
        b_enriched=b_pred,
        models_a_to_b=models_a_to_b,
        models_b_to_a=models_b_to_a,
        metrics_a_to_b=metrics_a_to_b,
        metrics_b_to_a=metrics_b_to_a,
    )

