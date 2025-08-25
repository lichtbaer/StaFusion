from __future__ import annotations

import uvicorn

from .app import create_app


app = create_app()


def main() -> None:
    uvicorn.run("datafusion_ml.web.main:app", host="0.0.0.0", port=8000, reload=False)

