from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DFML_", extra="ignore")

    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS middleware. Set to False to disable CORS entirely."
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: [],
        description="List of allowed CORS origins. Empty list means no CORS. "
                   "Use ['*'] for development only (not recommended for production)."
    )
    cors_allow_credentials: bool = Field(
        default=False,
        description="Allow credentials in CORS requests. Cannot be True if origins contains '*'."
    )
    cors_allow_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "OPTIONS"],
        description="List of allowed HTTP methods for CORS. Default: GET, POST, OPTIONS."
    )
    cors_allow_headers: List[str] = Field(
        default_factory=lambda: ["Content-Type", "Accept"],
        description="List of allowed headers for CORS. Default: Content-Type, Accept."
    )

    enable_metrics: bool = Field(default=True)
    enable_unversioned_routes: bool = Field(default=True)

    max_body_mb: int = Field(default=50, ge=1)
    max_rows: int = Field(default=200_000, ge=1)

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json|plain

    @classmethod
    def from_env(cls) -> "APISettings":
        """Create settings from environment variables.
        
        Handles comma-separated string values for CORS settings from environment.
        Pydantic will parse these automatically, but this method provides
        additional normalization for edge cases.
        """
        settings = cls()
        # Normalize CORS origins if provided as comma-separated string via env
        # This can happen if env var is set as a string instead of JSON array
        if isinstance(settings.cors_origins, str):
            origins_list = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
            settings.cors_origins = origins_list
        # Validate CORS configuration
        if settings.cors_allow_credentials and "*" in settings.cors_origins:
            raise ValueError(
                "CORS allow_credentials cannot be True when origins contains '*'. "
                "Specify explicit origins for credential support."
            )
        return settings

