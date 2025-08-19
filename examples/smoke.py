import pandas as pd

from datafusion_ml.fusion import fuse_datasets


def main() -> None:
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

    print("Fused shape:", result.fused.shape)
    print("A enriched columns:", list(result.a_enriched.columns))
    print("B enriched columns:", list(result.b_enriched.columns))


if __name__ == "__main__":
    main()

