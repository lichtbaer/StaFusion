# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11-slim

FROM python:${PYTHON_VERSION} AS build
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md MANIFEST.in /app/
COPY datafusion_ml /app/datafusion_ml
RUN pip install --upgrade pip && pip install ".[api,ml]"

FROM python:${PYTHON_VERSION} AS run
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=build /usr/local /usr/local
COPY datafusion_ml /app/datafusion_ml
EXPOSE 8000
CMD ["uvicorn", "datafusion_ml.web.main:app", "--host", "0.0.0.0", "--port", "8000"]

