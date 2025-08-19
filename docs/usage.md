## Usage

### Python API

```python
import pandas as pd
from datafusion_ml import fuse_datasets

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

res = fuse_datasets(A, B)
print(res.fused.shape)
```

### CLI

```bash
datafusion-ml \
  --a path/to/a.csv \
  --b path/to/b.csv \
  --out-fused fused.csv \
  --out-a a_enriched.csv \
  --out-b b_enriched.csv
```

