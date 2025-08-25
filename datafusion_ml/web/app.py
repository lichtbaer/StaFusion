from __future__ import annotations

import logging
import math
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from .config import APISettings
from .errors import register_exception_handlers
from .routers.fusion import router as fusion_router


def _setup_logging(settings: APISettings) -> None:
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)
    handler: logging.Handler
    handler = logging.StreamHandler()
    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)


def create_app() -> FastAPI:
    settings = APISettings.from_env()
    _setup_logging(settings)

    app = FastAPI(title="datafusion-ml API", version="0.1.0")

    if settings.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        )

    register_exception_handlers(app)

    # Metrics endpoint (Prometheus)
    if settings.enable_metrics:
        registry = CollectorRegistry()  # default aggregates global REGISTRY, override if needed

        @app.get("/metrics")
        def metrics() -> Response:  # type: ignore[no-untyped-def]
            output = generate_latest()  # from default REGISTRY
            return Response(content=output, media_type=CONTENT_TYPE_LATEST)

    # Health endpoint
    @app.get("/v1/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    # Routers
    app.include_router(fusion_router, prefix="/v1")

    if settings.enable_unversioned_routes:
        # Backwards-compatible unversioned routes
        app.get("/health")(health)
        for r in list(fusion_router.routes):
            if hasattr(r, "path") and hasattr(r, "methods"):
                # We only recreate /fuse for backward compat
                # Avoid duplicating multiple routes if added later
                if getattr(r, "path", "").endswith("/fuse"):
                    app.add_api_route("/fuse", r.endpoint, methods=list(r.methods))  # type: ignore[arg-type]

    # Body size limit via middleware (approximate)
    max_bytes = settings.max_body_mb * 1024 * 1024

    @app.middleware("http")
    async def limit_body_size(request, call_next):  # type: ignore[no-untyped-def]
        # Note: Starlette receives body streamed; we read and check length
        body = await request.body()
        if len(body) > max_bytes:
            return Response(status_code=413, content="Request entity too large")
        return await call_next(request)

    return app

