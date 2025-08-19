from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_validate, StratifiedKFold, KFold

from .config import FusionConfig


ProblemType = Literal["classification", "regression"]


def is_pycaret_available() -> bool:
    try:
        import pycaret  # noqa: F401
        return True
    except Exception:
        return False


def detect_problem_type(target_series: pd.Series) -> ProblemType:
    # Float-Ziele sind i.d.R. Regression
    if pd.api.types.is_float_dtype(target_series):
        return "regression"
    # Integer-Ziele: wenige eindeutige Klassen -> Klassifikation
    if pd.api.types.is_integer_dtype(target_series):
        n_unique = target_series.dropna().nunique()
        n_obs = target_series.dropna().shape[0]
        if n_unique <= 20 and n_unique <= max(2, int(0.2 * n_obs)):
            return "classification"
        return "regression"
    # String/Objekt -> Klassifikation
    return "classification"


def build_sklearn_pipeline(
    X: pd.DataFrame,
    problem_type: ProblemType,
    *,
    config: Optional[FusionConfig] = None,
) -> Pipeline:
    if config is None:
        config = FusionConfig()
    categorical_cols = [c for c in X.columns if not pd.api.types.is_numeric_dtype(X[c])]
    numeric_cols = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=config.use_sparse_onehot,
                ),
            ),
        ]
    )

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_transformer, categorical_cols),
            ("numeric", numeric_transformer, numeric_cols),
        ]
    )

    if problem_type == "classification":
        model = RandomForestClassifier(
            n_estimators=config.n_estimators, random_state=config.random_state
        )
    else:
        model = RandomForestRegressor(
            n_estimators=config.n_estimators, random_state=config.random_state
        )

    pipeline: Pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )
    return pipeline


@dataclass
class TrainedModel:
    problem_type: ProblemType
    model: Any
    backend: Literal["pycaret", "sklearn"]
    target: str
    features: Tuple[str, ...]
    extra: Optional[Dict[str, Any]] = None


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    problem_type: Optional[ProblemType] = None,
    *,
    config: Optional[FusionConfig] = None,
) -> TrainedModel:
    if config is None:
        config = FusionConfig()
    if problem_type is None:
        problem_type = detect_problem_type(y)

    features = tuple(X.columns.tolist())

    if config.prefer_pycaret and is_pycaret_available():
        if problem_type == "classification":
            from pycaret.classification import ClassificationExperiment

            exp = ClassificationExperiment()
            data = X.copy()
            data[y.name] = y
            exp.setup(
                data=data,
                target=y.name,
                session_id=config.random_state,
                fold=config.cv_splits,
                verbose=False,
                html=False,
            )
            best = exp.compare_models(sort="AUC")
            final_model = exp.finalize_model(best)
            return TrainedModel(
                problem_type=problem_type,
                model=final_model,
                backend="pycaret",
                target=y.name,
                features=features,
                extra={"experiment": exp},
            )
        else:
            from pycaret.regression import RegressionExperiment

            exp = RegressionExperiment()
            data = X.copy()
            data[y.name] = y
            exp.setup(
                data=data,
                target=y.name,
                session_id=config.random_state,
                fold=config.cv_splits,
                verbose=False,
                html=False,
            )
            best = exp.compare_models(sort="R2")
            final_model = exp.finalize_model(best)
            return TrainedModel(
                problem_type=problem_type,
                model=final_model,
                backend="pycaret",
                target=y.name,
                features=features,
                extra={"experiment": exp},
            )

    # sklearn fallback
    pipeline = build_sklearn_pipeline(X, problem_type, config=config)
    pipeline.fit(X, y)
    return TrainedModel(
        problem_type=problem_type,
        model=pipeline,
        backend="sklearn",
        target=y.name,
        features=features,
    )


def predict(model: TrainedModel, X: pd.DataFrame) -> np.ndarray:
    # Ensure proper list-based column selection (tuple would be a single key)
    X = X[list(model.features)]
    if model.backend == "pycaret":
        if model.problem_type == "classification":
            exp = model.extra["experiment"]  # type: ignore[index]
            preds = exp.predict_model(model.model, data=X)
            # Prediction column name in PyCaret output is 'prediction_label'
            return preds["prediction_label"].to_numpy()
        else:
            exp = model.extra["experiment"]  # type: ignore[index]
            preds = exp.predict_model(model.model, data=X)
            return preds["prediction_label"].to_numpy()
    # sklearn
    if model.problem_type == "classification":
        return model.model.predict(X)  # type: ignore[no-any-return]
    else:
        return model.model.predict(X)  # type: ignore[no-any-return]


def cross_validate_metrics(
    X: pd.DataFrame,
    y: pd.Series,
    problem_type: ProblemType,
    *,
    config: Optional[FusionConfig] = None,
) -> Dict[str, float]:
    if config is None:
        config = FusionConfig()
    pipeline = build_sklearn_pipeline(X, problem_type, config=config)
    if problem_type == "classification":
        y_non_null = y.dropna()
        # Ensure sufficient members per class for StratifiedKFold
        class_counts = y_non_null.value_counts()
        min_per_class = int(class_counts.min()) if not class_counts.empty else 0
        splits = min(config.cv_splits, max(2, min_per_class))
        if splits < 2:
            return {}
        cv = StratifiedKFold(
            n_splits=splits, shuffle=True, random_state=config.random_state
        )
        scoring = {
            "accuracy": "accuracy",
            "f1_macro": "f1_macro",
            "roc_auc_ovr": "roc_auc_ovr",
        }
    else:
        n_obs = int(y.dropna().shape[0])
        splits = min(config.cv_splits, max(2, n_obs))
        if splits < 2:
            return {}
        cv = KFold(n_splits=splits, shuffle=True, random_state=config.random_state)
        scoring = {
            "r2": "r2",
            "neg_rmse": "neg_root_mean_squared_error",
            "mae": "neg_mean_absolute_error",
        }
    out = cross_validate(pipeline, X, y, cv=cv, scoring=scoring, error_score=np.nan)
    metrics: Dict[str, float] = {}
    for key, values in out.items():
        if key.startswith("test_"):
            name = key[len("test_"):]
            mean_val = float(np.nanmean(values))
            if name.startswith("neg_"):
                # flip sign for readability
                metrics[name[4:]] = -mean_val
            else:
                metrics[name] = mean_val
    return metrics

