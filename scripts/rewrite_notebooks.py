import json
from pathlib import Path


def write_notebook(path: Path, title: str, code_source_lines: list[str]) -> None:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# {title}\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": code_source_lines,
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(notebook, f, ensure_ascii=False, indent=2)


def to_lines(block: str) -> list[str]:
    return [line + "\n" for line in block.strip("\n").split("\n")]


def main() -> None:
    examples_dir = Path("/workspace/examples")

    write_notebook(
        examples_dir / "intro.ipynb",
        "datafusion-ml Intro",
        to_lines(
            """
import pandas as pd
from datafusion_ml import fuse_datasets

A = pd.DataFrame({
    'age_group': ['18-29','30-44','45-59','60+'],
    'income_bracket': ['low','mid','mid','high'],
    'education': ['HS','BA','MA','HS'],
    'target_only_in_A': [1,0,1,0],
})
B = pd.DataFrame({
    'age_group': ['18-29','30-44','45-59','60+'],
    'income_bracket': ['mid','mid','high','low'],
    'education': ['HS','BA','HS','PhD'],
    'numeric_only_in_B': [3.2,1.5,2.7,4.1],
})

res = fuse_datasets(A, B, prefer_pycaret=False)
res.fused.head()
            """
        ),
    )

    write_notebook(
        examples_dir / "breast_cancer.ipynb",
        "Breast Cancer fusion example",
        to_lines(
            """
from sklearn.datasets import load_breast_cancer
import numpy as np
import pandas as pd
from datafusion_ml import fuse_datasets

# Prepare A and B
data = load_breast_cancer(as_frame=True)
df = data.frame.rename(columns={"target": "diagnosis"})
overlap = ["mean radius", "mean texture", "mean perimeter", "mean smoothness"]
A = df[overlap + ["diagnosis"]].copy()

rng = np.random.default_rng(42)
weights = np.array([0.5, 0.2, 0.2, 0.1])
base = A[overlap].to_numpy() @ weights
noise = rng.normal(0.0, 0.5, size=base.shape[0])
B = df[overlap].copy()
B["risk_score"] = base + noise

# Fuse
a2b = fuse_datasets(A, B)
a2b.fused.head()
            """
        ),
    )

    write_notebook(
        examples_dir / "diabetes.ipynb",
        "Diabetes fusion example",
        to_lines(
            """
from sklearn.datasets import load_diabetes
import numpy as np
import pandas as pd
from datafusion_ml import fuse_datasets

# Prepare A and B
data = load_diabetes()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target, name="disease_progression")

# Pick overlap features
overlap = ["bmi", "bp", "s1", "s2"]
A = X[overlap].copy()
A["disease_progression"] = y

# Synthetic classification target in B
rng = np.random.default_rng(7)
score = (X[overlap].to_numpy() @ np.array([0.6, 0.2, 0.1, 0.1])) + rng.normal(0, 0.3, size=X.shape[0])
threshold = np.median(score)
B = X[overlap].copy()
B["high_risk"] = (score > threshold).astype(int)

# Fuse
res = fuse_datasets(A, B, prefer_pycaret=False)
res.fused.head()
            """
        ),
    )

    write_notebook(
        examples_dir / "advanced_custom.ipynb",
        "Advanced: custom overlaps and targets",
        to_lines(
            """
import pandas as pd
from datafusion_ml import fuse_datasets

A = pd.DataFrame({
    "age_group": ["18-29","30-44","45-59","60+"],
    "education": ["HS","BA","MA","HS"],
    "income_bracket": ["low","mid","mid","high"],
    "loyalty_segment": ["bronze","silver","gold","silver"],
})

B = pd.DataFrame({
    "age_group": ["18-29","30-44","45-59","60+"],
    "education": ["HS","BA","HS","PhD"],
    "income_bracket": ["mid","mid","high","low"],
    "spend_score": [3.2, 1.5, 2.7, 4.1],
})

overlap = ["age_group","education","income_bracket"]

res = fuse_datasets(
    df_a=A,
    df_b=B,
    overlap_features=overlap,
    targets_from_a=["loyalty_segment"],
    targets_from_b=["spend_score"],
    prefer_pycaret=False,
)

res.a_enriched, res.b_enriched
            """
        ),
    )


if __name__ == "__main__":
    main()