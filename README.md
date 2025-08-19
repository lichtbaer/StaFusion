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

## Quickstart

```python
import pandas as pd
from datafusion_ml.fusion import fuse_datasets

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

result = fuse_datasets(
    df_a=A,
    df_b=B,
)

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

- Release auf PyPI: Tag pushen (z. B. `v0.1.0`) und `PYPI_API_TOKEN` als Repo Secret setzen. Workflow `.github/workflows/release.yml` baut und veröffentlicht.