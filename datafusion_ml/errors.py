class DataFusionError(ValueError):
    """Base class for domain-specific data fusion errors."""


class OverlapError(DataFusionError):
    """Raised when no valid overlapping features can be determined."""


class TargetsError(DataFusionError):
    """Raised when no target columns are available or configuration is inconsistent."""


class ConfigurationError(DataFusionError):
    """Raised for invalid configuration values or unsupported combinations."""

