## Breast Cancer (sklearn) Example

This tutorial uses the built-in `sklearn.datasets.load_breast_cancer` dataset. We derive two datasets:
- A: overlapping features + classification target `diagnosis`
- B: same overlapping features + synthetic regression target `risk_score`

```python
from sklearn.datasets import load_breast_cancer
import numpy as np
import pandas as pd
from datafusion_ml import fuse_datasets

data = load_breast_cancer(as_frame=True)
df = data.frame.rename(columns={"target": "diagnosis"})
overlap = [
    "mean radius", "mean texture", "mean perimeter", "mean smoothness"
]
A = df[overlap + ["diagnosis"]].copy()

rng = np.random.default_rng(42)
weights = np.array([0.5, 0.2, 0.2, 0.1])
base = A[overlap].to_numpy() @ weights
noise = rng.normal(0.0, 0.5, size=base.shape[0])
B = df[overlap].copy()
B["risk_score"] = base + noise

res = fuse_datasets(A, B)
res.fused.head()
```

CLI usage with prepared CSVs:
```bash
python examples/prepare_sklearn_breast_cancer.py
python -m datafusion_ml.cli \
  --a examples/data/A_bc.csv \
  --b examples/data/B_bc.csv \
  --out-fused examples/data/fused_bc.csv \
  --out-a examples/data/A_bc_enriched.csv \
  --out-b examples/data/B_bc_enriched.csv
```

