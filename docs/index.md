## datafusion-ml

Statistical fusion of two datasets using overlapping features and machine learning.

Features:
- Overlap-based feature selection between dataset A and B
- Bidirectional prediction (A->B and B->A) using PyCaret or scikit-learn
- Cross-validated metrics summary
- Simple CLI and clean Python API

Install:
```bash
pip install datafusion-ml  # when published
# or for development
pip install -r requirements.txt
```

### Optional: FastAPI Microservice

```bash
pip install -e .[api]
datafusion-ml-api
# -> verfügbar unter http://localhost:8000
```

POST /fuse akzeptiert zwei Datensätze als Listen von Records (JSON) und liefert
angereicherte DataFrames sowie Metriken zurück. Beispiel-Body:

```json
{
  "df_a": [{"age_group": "18-29", "x_only_in_a": 1}],
  "df_b": [{"age_group": "18-29", "y_only_in_b": 3.2}],
  "prefer_pycaret": false
}
```

