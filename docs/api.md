## API

### fuse_datasets(df_a, df_b, overlap_features=None, targets_from_a=None, targets_from_b=None, problem_type_map=None, prefer_pycaret=True, random_state=42)

Returns a `FusionResult` with:
- `fused`: fused DataFrame
- `a_enriched`: A enriched with predictions from B-only columns
- `b_enriched`: B enriched with predictions from A-only columns
- `models_a_to_b` and `models_b_to_a`: trained models
- `metrics_a_to_b` and `metrics_b_to_a`: cross-validated metrics

