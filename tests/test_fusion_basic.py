import pandas as pd

from datafusion_ml.fusion import fuse_datasets
from datafusion_ml.config import FusionConfig


def test_basic_fusion_runs():
    A = pd.DataFrame(
        {
            "age_group": ["18-29", "30-44", "45-59", "60+"],
            "income_bracket": ["low", "mid", "mid", "high"],
            "education": ["HS", "BA", "MA", "HS"],
            "target_only_in_A": [1, 0, 1, 0],
        }
    )
    B = pd.DataFrame(
        {
            "age_group": ["18-29", "30-44", "45-59", "60+"],
            "income_bracket": ["mid", "mid", "high", "low"],
            "education": ["HS", "BA", "HS", "PhD"],
            "numeric_only_in_B": [3.2, 1.5, 2.7, 4.1],
        }
    )

    cfg = FusionConfig(prefer_pycaret=False, use_sparse_onehot=True, cv_splits=2, n_estimators=50)
    result = fuse_datasets(df_a=A, df_b=B, prefer_pycaret=cfg.prefer_pycaret, random_state=cfg.random_state, config=cfg)

    assert result.fused.shape[0] == 8
    assert "target_only_in_A" in result.b_enriched.columns
    assert "numeric_only_in_B" in result.a_enriched.columns
    assert set(result.metrics_a_to_b.keys()) == {"target_only_in_A"}
    assert set(result.metrics_b_to_a.keys()) == {"numeric_only_in_B"}


def test_no_overlap_raises():
    A = pd.DataFrame({"a": [1, 2, 3], "y": [0, 1, 0]})
    B = pd.DataFrame({"b": [1, 2, 3], "x": [0.1, 0.2, 0.3]})
    try:
        fuse_datasets(df_a=A, df_b=B, prefer_pycaret=False)
        assert False, "Expected ValueError due to no overlap"
    except ValueError:
        pass


def test_cli_smoke(tmp_path):
    from subprocess import run
    import sys

    A = pd.DataFrame({
        "age": [1, 2, 3],
        "sex": ["m", "f", "m"],
        "y": [0, 1, 0],
    })
    B = pd.DataFrame({
        "age": [2, 3, 4],
        "sex": ["f", "m", "f"],
        "x": [0.2, 0.3, 0.1],
    })
    a_path = tmp_path / "a.csv"
    b_path = tmp_path / "b.csv"
    fused_path = tmp_path / "fused.csv"
    metrics_path = tmp_path / "metrics.json"
    A.to_csv(a_path, index=False)
    B.to_csv(b_path, index=False)

    # Invoke CLI via module entrypoint
    cmd = [sys.executable, "-m", "datafusion_ml.cli", "--a", str(a_path), "--b", str(b_path), "--out-fused", str(fused_path), "--no-pycaret", "--metrics-out", str(metrics_path), "--cv-splits", "2", "--n-estimators", "10", "--sparse-onehot"]
    res = run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert fused_path.exists()
    assert metrics_path.exists()

