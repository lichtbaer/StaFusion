from __future__ import annotations

import argparse
from typing import List, Optional

import pandas as pd

from .fusion import fuse_datasets


def _split_columns(arg: Optional[str]) -> Optional[List[str]]:
    if arg is None or arg.strip() == "":
        return None
    return [c.strip() for c in arg.split(",") if c.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fuse two datasets statistically using overlapping features and ML models."
    )
    parser.add_argument("--a", dest="a_path", required=True, help="CSV path to dataset A")
    parser.add_argument("--b", dest="b_path", required=True, help="CSV path to dataset B")
    parser.add_argument("--out-fused", dest="out_fused", required=True, help="Output CSV for fused dataset")
    parser.add_argument("--out-a", dest="out_a", required=False, help="Output CSV for enriched A")
    parser.add_argument("--out-b", dest="out_b", required=False, help="Output CSV for enriched B")
    parser.add_argument("--overlap", dest="overlap", required=False, help="Comma-separated overlap feature names")
    parser.add_argument("--targets-a", dest="targets_a", required=False, help="Comma-separated targets from A")
    parser.add_argument("--targets-b", dest="targets_b", required=False, help="Comma-separated targets from B")
    parser.add_argument("--no-pycaret", dest="no_pycaret", action="store_true", help="Disable PyCaret even if installed")
    args = parser.parse_args()

    df_a = pd.read_csv(args.a_path)
    df_b = pd.read_csv(args.b_path)

    result = fuse_datasets(
        df_a=df_a,
        df_b=df_b,
        overlap_features=_split_columns(args.overlap),
        targets_from_a=_split_columns(args.targets_a),
        targets_from_b=_split_columns(args.targets_b),
        prefer_pycaret=not args.no_pycaret,
    )

    result.fused.to_csv(args.out_fused, index=False)
    if args.out_a:
        result.a_enriched.to_csv(args.out_a, index=False)
    if args.out_b:
        result.b_enriched.to_csv(args.out_b, index=False)

    # Print a concise metrics summary to stdout
    print("A->B metrics:")
    for target, metrics in result.metrics_a_to_b.items():
        print(target, {k: round(v, 4) for k, v in metrics.items()})
    print("B->A metrics:")
    for target, metrics in result.metrics_b_to_a.items():
        print(target, {k: round(v, 4) for k, v in metrics.items()})


if __name__ == "__main__":
    main()

