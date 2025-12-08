# API Reference

## Python API

### `fuse_datasets`

Main function for fusing two datasets.

```python
from datafusion_ml.fusion import fuse_datasets
from datafusion_ml.config import FusionConfig

result = fuse_datasets(
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
) -> FusionResult
```

#### Parameters

- **df_a** (`pd.DataFrame`): First dataset
- **df_b** (`pd.DataFrame`): Second dataset
- **overlap_features** (`Optional[Sequence[str]]`): Explicit list of overlapping feature names. If `None`, automatically inferred as the intersection of columns in A and B (excluding targets)
- **targets_from_a** (`Optional[Sequence[str]]`): Explicit list of target column names from dataset A. If `None`, automatically inferred as columns exclusive to A
- **targets_from_b** (`Optional[Sequence[str]]`): Explicit list of target column names from dataset B. If `None`, automatically inferred as columns exclusive to B
- **problem_type_map** (`Optional[Dict[str, ProblemType]]`): Manual mapping of target names to problem types (`ProblemType.CLASSIFICATION` or `ProblemType.REGRESSION`). If `None`, automatically detected
- **prefer_pycaret** (`bool`): Whether to prefer PyCaret over scikit-learn (default: `True`). Ignored if `config` is provided
- **random_state** (`int`): Random seed for reproducibility (default: `42`). Ignored if `config` is provided
- **config** (`Optional[FusionConfig]`): Advanced configuration object. If provided, overrides `prefer_pycaret` and `random_state` parameters

#### Returns

`FusionResult` object with the following attributes:

- **fused** (`pd.DataFrame`): Combined dataset with all rows from A and B, including predicted values
- **a_enriched** (`pd.DataFrame`): Dataset A enriched with predictions from B-only columns
- **b_enriched** (`pd.DataFrame`): Dataset B enriched with predictions from A-only columns
- **models_a_to_b** (`Dict[str, TrainedModel]`): Trained models for predicting targets from A in B (keyed by target name)
- **models_b_to_a** (`Dict[str, TrainedModel]`): Trained models for predicting targets from B in A (keyed by target name)
- **metrics_a_to_b** (`Dict[str, ClassificationMetrics | RegressionMetrics]`): Cross-validation metrics for A->B predictions
- **metrics_b_to_a** (`Dict[str, ClassificationMetrics | RegressionMetrics]`): Cross-validation metrics for B->A predictions

#### Example

```python
import pandas as pd
from datafusion_ml.fusion import fuse_datasets
from datafusion_ml.config import FusionConfig

A = pd.DataFrame({
    "age_group": ["18-29", "30-44"],
    "income": ["low", "mid"],
    "target_a": [1, 0],
})

B = pd.DataFrame({
    "age_group": ["18-29", "30-44"],
    "income": ["mid", "high"],
    "target_b": [3.2, 1.5],
})

config = FusionConfig(
    prefer_pycaret=True,
    cv_splits=3,
    n_estimators=200,
    use_sparse_onehot=True,
)

result = fuse_datasets(df_a=A, df_b=B, config=config)
print(result.fused)
print(result.metrics_a_to_b)
```

### `FusionConfig`

Configuration class for advanced tuning.

```python
from datafusion_ml.config import FusionConfig

config = FusionConfig(
    prefer_pycaret: bool = True,
    random_state: int = 42,
    cv_splits: int = 3,
    n_estimators: int = 300,
    n_jobs: int = 1,
    use_sparse_onehot: bool = True,
    max_category_cardinality: int = 100,
    warn_on_high_cardinality: bool = True,
)
```

#### Parameters

- **prefer_pycaret** (`bool`): Use PyCaret if available, otherwise fall back to scikit-learn
- **random_state** (`int`): Random seed for reproducibility
- **cv_splits** (`int`): Number of cross-validation splits (default: `3`)
- **n_estimators** (`int`): Number of estimators for ensemble models (default: `300`)
- **n_jobs** (`int`): Number of parallel jobs (default: `1`)
- **use_sparse_onehot** (`bool`): Use sparse one-hot encoding for categorical features (default: `True`). Recommended for high-cardinality features
- **max_category_cardinality** (`int`): Maximum number of unique categories before warning (default: `100`)
- **warn_on_high_cardinality** (`bool`): Emit warnings for high-cardinality categorical features (default: `True`)

## REST API

### POST `/v1/fuse`

Synchronously fuse two datasets.

**Request Body:**

```json
{
  "df_a": [{"age_group": "18-29", "x_only_in_a": 1}],
  "df_b": [{"age_group": "18-29", "y_only_in_b": 3.2}],
  "overlap_features": null,
  "targets_from_a": null,
  "targets_from_b": null,
  "prefer_pycaret": true,
  "random_state": 42,
  "cv_splits": 3,
  "n_estimators": 300,
  "use_sparse_onehot": true,
  "max_category_cardinality": 100,
  "warn_on_high_cardinality": true,
  "return_parts": null,
  "row_limit": null,
  "columns_include": null,
  "columns_exclude": null
}
```

**Response:**

```json
{
  "fused": [{"age_group": "18-29", "x_only_in_a": 1, "y_only_in_b": 3.2}],
  "a_enriched": [{"age_group": "18-29", "x_only_in_a": 1, "y_only_in_b": 3.2}],
  "b_enriched": [{"age_group": "18-29", "x_only_in_a": 1, "y_only_in_b": 3.2}],
  "metrics_a_to_b": {
    "y_only_in_b": {"r2": 0.85, "rmse": 0.5, "mae": 0.3}
  },
  "metrics_b_to_a": {
    "x_only_in_a": {"accuracy": 0.9, "f1_macro": 0.88, "roc_auc_ovr": 0.92}
  }
}
```

### POST `/v1/fuse/async`

Asynchronously fuse two datasets (returns job ID).

### GET `/v1/fuse/async/{job_id}`

Get status and results of an async fusion job.

### POST `/v1/fuse/upload`

Upload CSV or Parquet files for fusion.

**Request:** `multipart/form-data` with `file_a` and `file_b`

### GET `/v1/health`

Health check endpoint.

### GET `/metrics`

Prometheus metrics endpoint.

See the [Deployment Guide](deployment.md) for API configuration and security options.

