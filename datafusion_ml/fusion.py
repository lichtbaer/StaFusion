from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from .modeling import ProblemType, TrainedModel, detect_problem_type, predict, train_model


@dataclass
class FusionResult:
    fused: pd.DataFrame
    a_enriched: pd.DataFrame
    b_enriched: pd.DataFrame
    models_a_to_b: Dict[str, TrainedModel]
    models_b_to_a: Dict[str, TrainedModel]


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
) -> FusionResult:
    if overlap_features is None:
        exclude = set(targets_from_a or []) | set(targets_from_b or [])
        overlap_features = _infer_overlap_features(df_a, df_b, exclude=exclude)
    else:
        overlap_features = [c for c in overlap_features if c in df_a.columns and c in df_b.columns]

    if targets_from_a is None:
        targets_from_a = _exclusive_columns(df_a, df_b)
    if targets_from_b is None:
        targets_from_b = _exclusive_columns(df_b, df_a)

    # Align categorical levels across overlap features
    a_feat, b_feat = _coerce_categorical_alignment(
        df_a[overlap_features], df_b[overlap_features], overlap_features
    )

    # Train models A -> B
    models_a_to_b: Dict[str, TrainedModel] = {}
    b_pred = df_b.copy()
    for target in targets_from_a:
        y = df_a[target]
        problem = (problem_type_map or {}).get(target) or detect_problem_type(y)
        model = train_model(a_feat, y, problem_type=problem, random_state=random_state, prefer_pycaret=prefer_pycaret)
        models_a_to_b[target] = model
        preds = predict(model, b_feat)
        col_name = target if target not in b_pred.columns else f"{target}_pred"
        b_pred[col_name] = preds

    # Train models B -> A
    models_b_to_a: Dict[str, TrainedModel] = {}
    a_pred = df_a.copy()
    for target in targets_from_b:
        y = df_b[target]
        problem = (problem_type_map or {}).get(target) or detect_problem_type(y)
        model = train_model(b_feat, y, problem_type=problem, random_state=random_state, prefer_pycaret=prefer_pycaret)
        models_b_to_a[target] = model
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
    )

