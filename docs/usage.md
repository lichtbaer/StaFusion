## Usage

### Python API

```python
import pandas as pd
from datafusion_ml.fusion import fuse_datasets
from datafusion_ml.config import FusionConfig

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

cfg = FusionConfig(use_sparse_onehot=True, cv_splits=3, n_estimators=200)
res = fuse_datasets(A, B, config=cfg)
print(res.fused.shape)
```

### CLI

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
  --metrics-out metrics.json
```

### Troubleshooting & Performance

- High-cardinality categorical features can explode memory with dense encodings. Use `FusionConfig(use_sparse_onehot=True)` or the CLI flag `--sparse-onehot`.
- If there are no overlapping features between A and B, specify them via `overlap_features` or ensure datasets share columns. Otherwise a `ValueError` is raised.
- Control runtime via `n_estimators` and `cv_splits`. Lower values speed up at the cost of stability.

