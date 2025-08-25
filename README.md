# datafusion-ml

[![CI](https://img.shields.io/github/actions/workflow/status/ORG/REPO/ci.yml?branch=main)](https://github.com/ORG/REPO/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://ORG.github.io/REPO/)
[![PyPI](https://img.shields.io/pypi/v/datafusion-ml.svg)](https://pypi.org/project/datafusion-ml/)

Bibliothek für statistische Fusion zweier Datensätze auf Basis überlappender Merkmale. Die Bibliothek nutzt PyCaret zur Modellierung (Klassifikation/Regression), um fehlende Variablen aus Datensatz A in B (und umgekehrt) vorherzusagen und die Datensätze zu einem gemeinsamen, angereicherten Datensatz zu vereinen.

## Installation

```bash
python -m pip install -r requirements.txt
# Optional (empfohlen für echte Modellierung):
python -m pip install pycaret==3.3.2
```

### Option: Microservice-API mit FastAPI

```bash
# Optionales Extra installieren (Entwicklung):
pip install -e .[api]

# oder direkt die Laufzeit-Dependencies:
pip install fastapi uvicorn[standard]

# Server starten
datafusion-ml-api  # läuft standardmäßig auf http://0.0.0.0:8000
```

Beispielanfrage:

```bash
curl -s -X POST http://localhost:8000/v1/fuse \
  -H 'Content-Type: application/json' \
  -d '{
        "df_a": [{"age_group": "18-29", "x_only_in_a": 1}],
        "df_b": [{"age_group": "18-29", "y_only_in_b": 3.2}],
        "prefer_pycaret": false,
        "return_parts": ["fused"],
        "row_limit": 10
      }' | jq '.fused | length'
```

#### Datei-Upload

```bash
# CSV oder Parquet möglich (multipart/form-data)
curl -s -X POST http://localhost:8000/v1/fuse/upload \
  -F file_a=@A.csv \
  -F file_b=@B.parquet | jq '.fused | length'
```

#### Asynchrone Verarbeitung

```bash
JOB=$(curl -s -X POST http://localhost:8000/v1/fuse/async -H 'Content-Type: application/json' -d @payload.json | jq -r .job_id)
# Status pollen
curl -s http://localhost:8000/v1/fuse/async/$JOB | jq
```

#### Metriken & Health

- Health: `GET /v1/health`
- Prometheus: `GET /metrics`

### Docker (PyCaret standardmäßig enthalten)

```bash
# Image bauen
docker build -t datafusion-ml-api .

# Starten
docker run --rm -p 8000:8000 \
  -e DFML_LOG_LEVEL=INFO \
  -e DFML_LOG_FORMAT=json \
  -e DFML_CORS_ENABLED=true \
  -e DFML_MAX_BODY_MB=50 \
  -e DFML_MAX_ROWS=200000 \
  datafusion-ml-api
```

### Konfiguration (Environment-Variablen, Prefix `DFML_`)

- `CORS_ENABLED` (bool, Default: `true`)
- `CORS_ORIGINS` (CSV-Liste, Default: `*`)
- `CORS_ALLOW_CREDENTIALS` (bool, Default: `false`)
- `CORS_ALLOW_METHODS` (CSV-Liste, Default: `*`)
- `CORS_ALLOW_HEADERS` (CSV-Liste, Default: `*`)
- `ENABLE_METRICS` (bool, Default: `true`)
- `ENABLE_UNVERSIONED_ROUTES` (bool, Default: `true`)
- `MAX_BODY_MB` (int, Default: `50`)
- `MAX_ROWS` (int, Default: `200000`)
- `LOG_LEVEL` (`DEBUG|INFO|...`, Default: `INFO`)
- `LOG_FORMAT` (`json|plain`, Default: `json`)

## Quickstart

```python
import pandas as pd
from datafusion_ml.fusion import fuse_datasets
from datafusion_ml.config import FusionConfig

# Beispiel-Daten
A = pd.DataFrame({
    "age_group": ["18-29", "30-44", "45-59", "60+"],
    "income_bracket": ["low", "mid", "mid", "high"],
    "education": ["HS", "BA", "MA", "HS"],
    "target_only_in_A": [1, 0, 1, 0],  # z. B. Klassifikation
})

B = pd.DataFrame({
    "age_group": ["18-29", "30-44", "45-59", "60+"],
    "income_bracket": ["mid", "mid", "high", "low"],
    "education": ["HS", "BA", "HS", "PhD"],
    "numeric_only_in_B": [3.2, 1.5, 2.7, 4.1],  # z. B. Regression
})

cfg = FusionConfig(use_sparse_onehot=True, cv_splits=3, n_estimators=200)
result = fuse_datasets(df_a=A, df_b=B, config=cfg)

print(result.fused.shape)
print(result.a_enriched.columns)
print(result.b_enriched.columns)
```

## Konfiguration
- Überlappende Merkmale können manuell vorgegeben oder automatisch als Schnittmenge der Spalten bestimmt werden.
- Zielvariablen können manuell angegeben werden. Standard: Spalten, die exklusiv in A (bzw. B) vorhanden sind, werden jeweils im anderen Datensatz vorhergesagt.

## Lizenz
MIT

## Development

- Tests lokal:
```bash
PYTHONPATH=. pytest -q
```

- Docs lokal:
```bash
pip install -e .[docs]
mkdocs serve
```

## Type Checking

- Lokaler Lauf:
```bash
pip install -e .[dev]
mypy datafusion_ml
```
- Hinweis: Für optionale Third-Party-Typen werden Stubs via `dev`-Extras installiert (z. B. `pandas-stubs`). In CI wird `mypy` automatisch ausgeführt.

## Hinweise & Limitierungen
- Bei sehr vielen Kategorien in überlappenden Merkmalen empfiehlt sich `use_sparse_onehot=True` (Standard), um Speicher zu sparen.
- Ohne gemeinsame Merkmale schlägt die Fusion mit `ValueError` fehl. In diesem Fall `overlap_features` explizit angeben.

- Release auf PyPI: Tag pushen (z. B. `v0.1.0`) und `PYPI_API_TOKEN` als Repo Secret setzen. Workflow `.github/workflows/release.yml` baut und veröffentlicht.

## Pre-commit Hooks

- Setup einmalig:
```bash
pip install -e .[dev]
pre-commit install
```
- Manuell ausführen:
```bash
pre-commit run --all-files
```