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

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting middleware."
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum number of requests per minute per client."
    )

    # JWT Authentication
    jwt_enabled: bool = Field(
        default=False,
        description="Enable JWT authentication middleware."
    )
    jwt_secret: str | None = Field(
        default=None,
        description="JWT secret key for token validation. Required if JWT is enabled."
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm for token validation."
    )

    # Job persistence
    job_persistence_enabled: bool = Field(
        default=False,
        description="Enable job persistence to disk. Jobs will survive server restarts."
    )
    job_persistence_path: str = Field(
        default="/tmp/datafusion-ml-jobs",
        description="Directory path for storing job data. Created if it doesn't exist."
    )

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
        # Validate JWT configuration
        if settings.jwt_enabled and not settings.jwt_secret:
            raise ValueError(
                "JWT authentication is enabled but jwt_secret is not set. "
                "Set DFML_JWT_SECRET environment variable."
            )
        return settings

