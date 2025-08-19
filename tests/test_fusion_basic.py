import pandas as pd

from datafusion_ml.fusion import fuse_datasets


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

    result = fuse_datasets(df_a=A, df_b=B, prefer_pycaret=False)

    assert result.fused.shape[0] == 8
    assert "target_only_in_A" in result.b_enriched.columns
    assert "numeric_only_in_B" in result.a_enriched.columns
    assert set(result.metrics_a_to_b.keys()) == {"target_only_in_A"}
    assert set(result.metrics_b_to_a.keys()) == {"numeric_only_in_B"}

