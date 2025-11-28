from __future__ import annotations

import logging
from typing import Dict, Callable, Awaitable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
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

    # Body size limit via middleware
    max_bytes = settings.max_body_mb * 1024 * 1024

    @app.middleware("http")
    async def limit_body_size(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip body size check for multipart/form-data (file uploads handled separately)
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            return await call_next(request)
        
        # Read body to check size, then recreate request with body for downstream handlers
        body = await request.body()
        if len(body) > max_bytes:
            return Response(status_code=413, content="Request entity too large")
        
        # Recreate request with body so downstream handlers can read it
        # This is necessary because request.body() consumes the stream
        async def receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}
        
        request._receive = receive  # type: ignore[attr-defined]
        return await call_next(request)

    return app

