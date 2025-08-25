from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from ..errors import OverlapError, TargetsError, ConfigurationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(OverlapError)
    async def _overlap_handler(_, exc: OverlapError):  # type: ignore[no-untyped-def]
        return _json_exc(400, str(exc))

    @app.exception_handler(TargetsError)
    async def _targets_handler(_, exc: TargetsError):  # type: ignore[no-untyped-def]
        return _json_exc(400, str(exc))

    @app.exception_handler(ConfigurationError)
    async def _config_handler(_, exc: ConfigurationError):  # type: ignore[no-untyped-def]
        return _json_exc(422, str(exc))


def _json_exc(status: int, detail: str):  # type: ignore[no-untyped-def]
    return JSONResponse(status_code=status, content={"detail": detail})

