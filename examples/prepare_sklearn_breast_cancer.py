from pathlib import Path

import numpy as np
from sklearn.datasets import load_breast_cancer


def main() -> None:
    data = load_breast_cancer(as_frame=True)
    df = data.frame.copy()
    # Rename target for readability
    df = df.rename(columns={"target": "diagnosis"})

    # Choose a small set of overlap features
    overlap = [
        "mean radius",
        "mean texture",
        "mean perimeter",
        "mean smoothness",
    ]

    # Dataset A: overlap + classification target
    A = df[overlap + ["diagnosis"]].copy()

    # Dataset B: overlap + synthetic regression target (risk_score)
    rng = np.random.default_rng(42)
    weights = np.array([0.5, 0.2, 0.2, 0.1])
    base = A[overlap].to_numpy() @ weights
    noise = rng.normal(0.0, 0.5, size=base.shape[0])
    risk_score = base + noise
    B = df[overlap].copy()
    B["risk_score"] = risk_score

    out_dir = Path(__file__).parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    A.to_csv(out_dir / "A_bc.csv", index=False)
    B.to_csv(out_dir / "B_bc.csv", index=False)
    print("Saved:", out_dir / "A_bc.csv", out_dir / "B_bc.csv")


if __name__ == "__main__":
    main()