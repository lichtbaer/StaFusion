# datafusion-ml

Statistical fusion of two datasets using overlapping features and machine learning.

## Overview

`datafusion-ml` is a Python library for statistically fusing two datasets based on overlapping features. The library uses PyCaret or scikit-learn for modeling (classification/regression) to predict missing variables from dataset A in B (and vice versa) and merge the datasets into a unified, enriched dataset.

## Features

- **Overlap-based feature selection**: Automatically detects or manually specifies overlapping features between datasets A and B
- **Bidirectional prediction**: Predicts variables from A in B and from B in A using machine learning models
- **Multiple model backends**: Supports PyCaret (default) or scikit-learn
- **Cross-validated metrics**: Provides comprehensive evaluation metrics for classification and regression tasks
- **Flexible API**: Python API, CLI, and REST API (FastAPI) available
- **Production-ready**: Optional authentication, rate limiting, job persistence, and monitoring

## Installation

```bash
# Basic installation
pip install datafusion-ml

# Or for development
pip install -r requirements.txt

# Optional: Install PyCaret for advanced modeling
pip install pycaret==3.3.2
```

## Quick Start

```python
import pandas as pd
from datafusion_ml.fusion import fuse_datasets
from datafusion_ml.config import FusionConfig

# Example datasets
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
cfg = FusionConfig(use_sparse_onehot=True, cv_splits=3, n_estimators=200)

# Fuse datasets
result = fuse_datasets(df_a=A, df_b=B, config=cfg)

print(result.fused.shape)
print(result.a_enriched.columns)
print(result.b_enriched.columns)
```

## FastAPI Microservice

The library includes an optional FastAPI-based REST API:

```bash
# Install with API extras
pip install -e .[api]

# Start the API server
datafusion-ml-api
# Available at http://localhost:8000 (versioned under /v1)
```

### API Example

```bash
curl -X POST http://localhost:8000/v1/fuse \
  -H 'Content-Type: application/json' \
  -d '{
    "df_a": [{"age_group": "18-29", "x_only_in_a": 1}],
    "df_b": [{"age_group": "18-29", "y_only_in_b": 3.2}],
    "prefer_pycaret": false
  }'
```

See the [API documentation](api.md) and [Deployment Guide](deployment.md) for more details.

## Documentation

- [Usage Guide](usage.md) - Python API and CLI usage
- [API Reference](api.md) - Complete API documentation
- [Tutorials](tutorials/quickstart.md) - Step-by-step tutorials
- [Deployment Guide](deployment.md) - Production deployment instructions

