from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FusionConfig:
    """Configuration options for dataset fusion and modeling.

    This object allows advanced users to tune performance, memory usage and
    evaluation behavior without changing the public function signatures.
    """

    # General
    prefer_pycaret: bool = True
    random_state: int = 42

    # Modeling
    cv_splits: int = 3
    n_estimators: int = 300
    use_sparse_onehot: bool = True

    # Safety/performance
    max_category_cardinality: int = 100
    warn_on_high_cardinality: bool = True

