# Usage Guide

This guide covers how to use datafusion-ml via the Python API, CLI, and REST API.

## Python API

### Basic Usage

```python
import pandas as pd
from datafusion_ml.fusion import fuse_datasets
from datafusion_ml.config import FusionConfig

# Prepare datasets
A = pd.DataFrame({
    "age_group": ["18-29", "30-44", "45-59", "60+"],
    "income_bracket": ["low", "mid", "mid", "high"],
    "education": ["HS", "BA", "MA", "HS"],
    "target_only_in_A": [1, 0, 1, 0],
})

B = pd.DataFrame({
    "age_group": ["18-29", "30-44", "45-59", "60+"],
    "income_bracket": ["mid", "mid", "high", "low"],
    "education": ["HS", "BA", "HS", "PhD"],
    "numeric_only_in_B": [3.2, 1.5, 2.7, 4.1],
})

# Configure fusion
cfg = FusionConfig(
    use_sparse_onehot=True,
    cv_splits=3,
    n_estimators=200,
    prefer_pycaret=True,
    random_state=42,
)

# Fuse datasets
result = fuse_datasets(df_a=A, df_b=B, config=cfg)

# Access results
print(f"Fused dataset shape: {result.fused.shape}")
print(f"A enriched columns: {result.a_enriched.columns.tolist()}")
print(f"B enriched columns: {result.b_enriched.columns.tolist()}")
print(f"Metrics A->B: {result.metrics_a_to_b}")
print(f"Metrics B->A: {result.metrics_b_to_a}")
```

### Advanced Configuration

```python
# Explicit overlap features and targets
result = fuse_datasets(
    df_a=A,
    df_b=B,
    overlap_features=["age_group", "income_bracket", "education"],
    targets_from_a=["target_only_in_A"],
    targets_from_b=["numeric_only_in_B"],
    config=cfg,
)

# Manual problem type specification
from datafusion_ml.modeling import ProblemType

result = fuse_datasets(
    df_a=A,
    df_b=B,
    problem_type_map={
        "target_only_in_A": ProblemType.CLASSIFICATION,
        "numeric_only_in_B": ProblemType.REGRESSION,
    },
    config=cfg,
)
```

## Command Line Interface (CLI)

### Basic Usage

```bash
datafusion-ml \
  --a path/to/a.csv \
  --b path/to/b.csv \
  --out-fused fused.csv \
  --out-a a_enriched.csv \
  --out-b b_enriched.csv
```

### Advanced Options

```bash
datafusion-ml \
  --a path/to/a.csv \
  --b path/to/b.csv \
  --out-fused fused.csv \
  --out-a a_enriched.csv \
  --out-b b_enriched.csv \
  --no-pycaret \
  --sparse-onehot \
  --cv-splits 3 \
  --n-estimators 200 \
  --metrics-out metrics.json \
  --random-state 42
```

### CLI Options

- `--a`, `--b`: Input CSV files for datasets A and B
- `--out-fused`: Output path for fused dataset
- `--out-a`, `--out-b`: Output paths for enriched datasets
- `--no-pycaret`: Use scikit-learn instead of PyCaret
- `--sparse-onehot`: Use sparse one-hot encoding for categorical features
- `--cv-splits`: Number of cross-validation splits (default: 3)
- `--n-estimators`: Number of estimators for ensemble models (default: 300)
- `--metrics-out`: Output path for metrics JSON file
- `--random-state`: Random seed for reproducibility

## REST API

### Synchronous Fusion

```bash
curl -X POST http://localhost:8000/v1/fuse \
  -H 'Content-Type: application/json' \
  -d '{
    "df_a": [{"age_group": "18-29", "x_only_in_a": 1}],
    "df_b": [{"age_group": "18-29", "y_only_in_b": 3.2}],
    "prefer_pycaret": false,
    "return_parts": ["fused"],
    "row_limit": 1000
  }'
```

### File Upload

```bash
curl -X POST http://localhost:8000/v1/fuse/upload \
  -F file_a=@A.csv \
  -F file_b=@B.parquet
```

### Asynchronous Fusion

```bash
# Start async job
JOB_ID=$(curl -s -X POST http://localhost:8000/v1/fuse/async \
  -H 'Content-Type: application/json' \
  -d @payload.json | jq -r .job_id)

# Poll for status
curl http://localhost:8000/v1/fuse/async/$JOB_ID
```

See the [API Reference](api.md) for complete API documentation.

## Troubleshooting

### High-Cardinality Categorical Features

High-cardinality categorical features can cause memory issues with dense encodings. Use sparse encoding:

```python
config = FusionConfig(use_sparse_onehot=True)
```

Or via CLI:
```bash
datafusion-ml --sparse-onehot ...
```

### No Overlapping Features

If datasets have no overlapping features, explicitly specify them:

```python
result = fuse_datasets(
    df_a=A,
    df_b=B,
    overlap_features=["shared_column_1", "shared_column_2"],
)
```

Otherwise, a `OverlapError` will be raised.

### Performance Tuning

Control runtime and accuracy trade-offs:

- **Faster but less stable**: Lower `n_estimators` (e.g., 100) and `cv_splits` (e.g., 2)
- **Slower but more stable**: Higher `n_estimators` (e.g., 500) and `cv_splits` (e.g., 5)
- **Memory optimization**: Use `use_sparse_onehot=True` for high-cardinality features

### Insufficient Data for Cross-Validation

If there are too few samples for cross-validation, metrics may be empty. Ensure sufficient data (recommended: at least 30-50 samples per target).

## Best Practices

1. **Data Quality**: Ensure overlapping features are consistent between datasets (same encoding, no missing values in overlap)
2. **Target Selection**: Let the library auto-detect targets unless you need explicit control
3. **Configuration**: Start with defaults and tune `n_estimators` and `cv_splits` based on your data size
4. **Memory**: Use sparse encoding for datasets with many categorical features
5. **Reproducibility**: Always set `random_state` for reproducible results

