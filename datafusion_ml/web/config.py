from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DFML_", extra="ignore")

    cors_enabled: bool = Field(default=True)
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = Field(default=False)
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])

    enable_metrics: bool = Field(default=True)
    enable_unversioned_routes: bool = Field(default=True)

    max_body_mb: int = Field(default=50, ge=1)
    max_rows: int = Field(default=200_000, ge=1)

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json|plain

    @staticmethod
    def from_env() -> "APISettings":
        settings = APISettings()
        # Normalize CORS origins if provided as comma-separated string via env
        if isinstance(settings.cors_origins, str):  # type: ignore[unreachable]
            settings.cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
        return settings

