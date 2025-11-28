# Projekt-Inspektion: Fehler, Bugs und technische Schulden

## Zusammenfassung

Diese Inspektion wurde am Projekt `datafusion-ml` durchgeführt, einer Bibliothek für statistische Fusion von Datensätzen mit ML-Modellen. Die Analyse umfasst Code-Qualität, Sicherheit, Performance, Wartbarkeit und technische Schulden.

---

## Kritische Probleme

### 1. **Request Body wird zweimal gelesen (Performance/Sicherheit)**
**Datei:** `datafusion_ml/web/app.py:84`

**Problem:**
```python
@app.middleware("http")
async def limit_body_size(request, call_next):
    body = await request.body()  # Body wird hier gelesen
    if len(body) > max_bytes:
        return Response(status_code=413, content="Request entity too large")
    return await call_next(request)  # Body wird erneut gelesen
```

**Auswirkung:**
- Der Request-Body wird im Middleware gelesen, aber nicht an die nächste Middleware/Route weitergegeben
- FastAPI/Starlette kann den Body danach nicht mehr lesen, da der Stream bereits konsumiert wurde
- Dies führt zu Fehlern bei POST-Requests

**Lösung:**
- Body-Streaming mit `request.stream()` verwenden oder
- Body in einen neuen Request-Stream umwandeln

---

### 2. **In-Memory Job Store ohne Cleanup (Memory Leak)**
**Datei:** `datafusion_ml/web/routers/fusion.py:29`

**Problem:**
```python
_JOB_STORE: Dict[str, Dict[str, Any]] = {}
```

**Auswirkung:**
- Jobs werden nie gelöscht
- Bei vielen async Jobs wächst der Speicherverbrauch unbegrenzt
- Keine TTL oder Cleanup-Mechanismus
- In Produktion problematisch

**Lösung:**
- TTL-basiertes Cleanup implementieren
- Optional: Persistenz in Datenbank
- Job-Historie mit Maximalgröße

---

### 3. **Fehlende Validierung bei File-Upload**
**Datei:** `datafusion_ml/web/routers/fusion.py:83-91`

**Problem:**
- Dateityp wird nur anhand der Dateiendung bestimmt (`.parquet` vs. `.csv`)
- Keine Validierung des tatsächlichen Dateiinhalts
- Keine Größenprüfung vor dem Lesen
- Keine Fehlerbehandlung bei korrupten Dateien

**Auswirkung:**
- Sicherheitsrisiko: Dateien können als falscher Typ hochgeladen werden
- Memory-Probleme bei sehr großen Dateien
- Unklare Fehlermeldungen bei korrupten Dateien

**Lösung:**
- Magic-Number-Prüfung für Dateitypen
- Streaming-Validierung
- Explizite Fehlerbehandlung

---

## Wichtige Probleme

### 4. **Sehr lange Zeile (Code-Qualität)**
**Datei:** `datafusion_ml/fusion.py:58`

**Problem:**
```python
if pd.api.types.is_object_dtype(a_aligned[c]) or pd.api.types.is_categorical_dtype(a_aligned[c]) or pd.api.types.is_object_dtype(b_aligned[c]) or pd.api.types.is_categorical_dtype(b_aligned[c]):
```

**Auswirkung:**
- Schwer lesbar
- Verstößt gegen PEP 8 (max. 100 Zeichen laut `pyproject.toml`)
- Wartbarkeit leidet

**Lösung:**
- In Hilfsfunktion extrahieren
- Mehrzeilig formatieren

---

### 5. **Fehlende Type Hints in Middleware**
**Datei:** `datafusion_ml/web/app.py:82`

**Problem:**
```python
async def limit_body_size(request, call_next):  # type: ignore[no-untyped-def]
```

**Auswirkung:**
- Type-Checker können nicht validieren
- `# type: ignore` unterdrückt Warnungen statt sie zu beheben

**Lösung:**
- Korrekte Type Hints hinzufügen:
  ```python
  from starlette.requests import Request
  from starlette.responses import Response
  from typing import Callable, Awaitable
  
  async def limit_body_size(
      request: Request, 
      call_next: Callable[[Request], Awaitable[Response]]
  ) -> Response:
  ```

---

### 6. **Potenzielle KeyError bei PyCaret Models**
**Datei:** `datafusion_ml/modeling.py:249, 254`

**Problem:**
```python
exp = model.extra["experiment"]  # type: ignore[index]
```

**Auswirkung:**
- `model.extra` könnte `None` sein
- Key "experiment" könnte fehlen
- `# type: ignore` versteckt potentielle Laufzeitfehler

**Lösung:**
- Explizite Prüfung:
  ```python
  if model.extra is None or "experiment" not in model.extra:
      raise ValueError("PyCaret model missing experiment")
  exp = model.extra["experiment"]
  ```

---

### 7. **CORS Standard-Konfiguration zu permissiv**
**Datei:** `datafusion_ml/web/config.py:13-16`

**Problem:**
```python
cors_origins: List[str] = Field(default_factory=lambda: ["*"])
cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])
```

**Auswirkung:**
- Standardmäßig erlaubt von überall (`*`)
- Sicherheitsrisiko in Produktion
- Credentials können nicht mit `*` verwendet werden

**Lösung:**
- Standard restriktiver setzen
- Dokumentation für Produktionseinsatz

---

### 8. **Fehlende Validierung in `from_env()`**
**Datei:** `datafusion_ml/web/config.py:31-32`

**Problem:**
```python
if isinstance(settings.cors_origins, str):  # type: ignore[unreachable]
    settings.cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
```

**Auswirkung:**
- `# type: ignore[unreachable]` deutet auf Typfehler hin
- Pydantic sollte String automatisch parsen, aber Logik ist unklar
- Keine Validierung der resultierenden Liste

**Lösung:**
- Pydantic Field-Validatoren verwenden
- Type-Check entfernen oder korrigieren

---

## Code-Qualität und Wartbarkeit

### 9. **Doppelte Logik in PyCaret Trainer**
**Datei:** `datafusion_ml/modeling.py:163-220`

**Problem:**
- Classification und Regression haben fast identischen Code
- Code-Duplikation erhöht Wartungsaufwand

**Lösung:**
- Gemeinsame Logik extrahieren
- Nur problem-spezifische Teile unterscheiden

---

### 10. **Fehlende Error Handling bei File-Read**
**Datei:** `datafusion_ml/web/routers/fusion.py:56-62`

**Problem:**
```python
def _read_csv(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(file_bytes))

def _read_parquet(file_bytes: bytes) -> pd.DataFrame:
    table = pq.read_table(io.BytesIO(file_bytes))
    return table.to_pandas()
```

**Auswirkung:**
- Keine Behandlung von korrupten Dateien
- Unklare Fehlermeldungen für Benutzer
- Memory-Probleme bei sehr großen Dateien nicht abgefangen

**Lösung:**
- Try-Except mit spezifischen Fehlermeldungen
- Größenprüfung vor dem Lesen

---

### 11. **Unvollständige Metriken-Validierung**
**Datei:** `datafusion_ml/modeling.py:262-312`

**Problem:**
- `cross_validate_metrics` kann leeres Dict zurückgeben
- Keine Validierung ob Metriken sinnvoll sind
- Bei zu wenigen Samples werden Metriken übersprungen

**Auswirkung:**
- Unklare Ergebnisse für Benutzer
- Keine Warnung wenn CV nicht möglich ist

**Lösung:**
- Explizite Warnung/Logging wenn CV übersprungen wird
- Mindestanforderungen dokumentieren

---

### 12. **Fehlende Validierung von `row_limit`**
**Datei:** `datafusion_ml/web/routers/fusion.py:24`

**Problem:**
- `row_limit` wird nur gegen `max_rows` geprüft
- Keine Prüfung auf negative Werte (obwohl Schema `ge=0` hat)
- Keine Prüfung ob `row_limit` sinnvoll ist (z.B. > 0)

**Lösung:**
- Explizite Validierung
- Bessere Fehlermeldungen

---

## Technische Schulden

### 13. **Fehlende Authentifizierung**
**Datei:** `datafusion_ml/web/` (überall)

**Problem:**
- Keine JWT-Validierung implementiert
- Laut TODO.md geplant, aber nicht umgesetzt
- API ist öffentlich zugänglich

**Auswirkung:**
- Sicherheitsrisiko in Produktion
- Keine Rate-Limiting-Integration möglich

**Lösung:**
- JWT-Middleware implementieren (wie in TODO.md beschrieben)
- Optional per Env-Variable aktivierbar

---

### 14. **Fehlende Persistenz für Async Jobs**
**Datei:** `datafusion_ml/web/routers/fusion.py:29`

**Problem:**
- Jobs werden nur im Memory gespeichert
- Bei Server-Neustart gehen alle Jobs verloren
- Keine Job-Historie

**Auswirkung:**
- Unzuverlässig für Produktion
- Keine Nachvollziehbarkeit

**Lösung:**
- Optional: Datenbank-Persistenz
- Job-Historie mit TTL

---

### 15. **Unvollständige Metriken-Export**
**Datei:** `datafusion_ml/service/fusion_service.py:80-87`

**Problem:**
- Metriken werden bereinigt (`_clean`), aber NaN-Werte werden entfernt
- Keine Dokumentation welche Metriken wann verfügbar sind
- Keine Validierung ob Metriken vollständig sind

**Lösung:**
- Dokumentation der verfügbaren Metriken
- Explizite Behandlung von fehlenden Metriken

---

### 16. **Fehlende Rate Limiting**
**Datei:** `datafusion_ml/web/app.py`

**Problem:**
- Keine Rate-Limiting-Middleware
- API kann überlastet werden
- Kein Schutz vor Missbrauch

**Auswirkung:**
- DDoS-Anfälligkeit
- Ressourcenverbrauch nicht kontrolliert

**Lösung:**
- Rate-Limiting-Middleware hinzufügen
- Konfigurierbar per Env-Variable

---

### 17. **Unvollständige Logging-Korrelation**
**Datei:** `datafusion_ml/web/routers/fusion.py:32-37`

**Problem:**
- Async Jobs haben keine `job_id` in Logs
- Fehler werden nur im Job-Store gespeichert, nicht geloggt
- Keine Request-ID-Korrelation

**Auswirkung:**
- Debugging schwierig
- Keine Nachvollziehbarkeit

**Lösung:**
- Request-ID/Job-ID in Logs
- Strukturiertes Logging mit Kontext

---

### 18. **Fehlende Input-Validierung für DataFrame-Spalten**
**Datei:** `datafusion_ml/service/fusion_service.py:34-35`

**Problem:**
```python
df_a = pd.DataFrame.from_records(req.df_a)
df_b = pd.DataFrame.from_records(req.df_b)
```

**Auswirkung:**
- Keine Validierung ob Records konsistent sind
- Leere DataFrames werden nicht abgefangen
- Keine Prüfung auf erforderliche Spalten

**Lösung:**
- Validierung der Input-Daten
- Explizite Fehlermeldungen

---

## Konfiguration und Deployment

### 19. **Hardcoded Werte in README**
**Datei:** `README.md:3-5`

**Problem:**
```markdown
[![CI](https://img.shields.io/github/actions/workflow/status/ORG/REPO/ci.yml?branch=main)]
```

**Auswirkung:**
- Platzhalter `ORG/REPO` nicht ersetzt
- Badges funktionieren nicht

**Lösung:**
- Platzhalter durch echte Werte ersetzen

---

### 20. **Fehlende Dependency-Version-Pinning**
**Datei:** `requirements.txt`

**Problem:**
```txt
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
```

**Auswirkung:**
- Potenzielle Breaking Changes bei Updates
- Nicht reproduzierbare Builds
- CI/CD kann unterschiedliche Versionen verwenden

**Lösung:**
- Versions-Pinning für Produktion
- Separate `requirements-dev.txt` für Entwicklung

---

### 21. **Unvollständige CI/CD Pipeline**
**Datei:** `.github/workflows/ci.yml`

**Problem:**
- Keine Frontend-Tests
- Keine E2E-Tests
- Keine Security-Scans für Dependencies
- Keine Build-Artefakte für Frontend

**Auswirkung:**
- Frontend-Code nicht validiert
- Keine automatische Qualitätssicherung

**Lösung:**
- Frontend-Tests in CI integrieren
- E2E-Tests mit Playwright
- Dependency-Scans (z.B. `pip-audit`, `npm audit`)

---

## Dokumentation

### 22. **Unvollständige API-Dokumentation**
**Datei:** `datafusion_ml/web/schemas.py`

**Problem:**
- Nicht alle Felder haben Beschreibungen
- Keine Beispiele in OpenAPI-Schema
- Fehlende Validierungsregeln dokumentiert

**Lösung:**
- Vollständige Field-Descriptions
- OpenAPI-Beispiele hinzufügen
- Validierungsregeln dokumentieren

---

### 23. **Fehlende Error-Dokumentation**
**Datei:** `datafusion_ml/errors.py`

**Problem:**
- Custom Exceptions haben keine Docstrings
- Keine Dokumentation wann welche Exceptions geworfen werden
- Keine Beispiele für Error-Handling

**Lösung:**
- Docstrings für alle Exceptions
- Error-Handling-Guide in Dokumentation

---

## Performance

### 24. **Ineffiziente DataFrame-Operationen**
**Datei:** `datafusion_ml/fusion.py:155-159`

**Problem:**
```python
all_columns = sorted(list(set(a_pred.columns) | set(b_pred.columns)))
fused = pd.concat([
    a_pred.reindex(columns=all_columns),
    b_pred.reindex(columns=all_columns),
], ignore_index=True)
```

**Auswirkung:**
- `reindex` erstellt Kopien
- Bei großen DataFrames ineffizient

**Lösung:**
- Direkteres Concatenation ohne Reindex
- Oder: In-Place-Operationen wo möglich

---

### 25. **Fehlende Memory-Limits**
**Datei:** `datafusion_ml/web/config.py:21-22`

**Problem:**
- `max_body_mb` und `max_rows` sind konfigurierbar
- Aber keine Memory-Limits für Processing
- Große DataFrames können Server zum Absturz bringen

**Auswirkung:**
- OOM (Out of Memory) möglich
- Keine Kontrolle über Ressourcenverbrauch

**Lösung:**
- Memory-Monitoring
- Processing-Limits
- Graceful Degradation bei Memory-Problemen

---

## Test-Qualität

### 26. **Fehlende Edge-Case-Tests**
**Datei:** `tests/`

**Problem:**
- Keine Tests für leere DataFrames
- Keine Tests für sehr große DataFrames
- Keine Tests für korrupte Dateien
- Keine Tests für Memory-Limits

**Lösung:**
- Edge-Case-Tests hinzufügen
- Property-based Testing wo sinnvoll

---

### 27. **Fehlende Integration-Tests**
**Datei:** `tests/`

**Problem:**
- Keine Tests für vollständige Workflows
- Keine Tests für Error-Recovery
- Keine Tests für Async-Job-Failure

**Lösung:**
- Integration-Tests für kritische Pfade
- Failure-Szenarien testen

---

## Empfohlene Prioritäten

### Sofort (Kritisch):
1. Request Body wird zweimal gelesen (#1)
2. In-Memory Job Store ohne Cleanup (#2)
3. Fehlende File-Upload-Validierung (#3)

### Kurzfristig (Wichtig):
4. Type Hints in Middleware (#5)
5. PyCaret KeyError-Risiko (#6)
6. CORS-Konfiguration (#7)

### Mittelfristig (Technische Schulden):
7. Authentifizierung implementieren (#13)
8. Rate Limiting (#16)
9. Job-Persistenz (#14)

### Langfristig (Verbesserungen):
10. Code-Duplikation reduzieren (#9)
11. Performance-Optimierungen (#24, #25)
12. Test-Abdeckung erhöhen (#26, #27)

---

## Fazit

Das Projekt zeigt eine solide Grundstruktur, hat aber mehrere kritische Probleme, die vor einem Produktionseinsatz behoben werden müssen. Die wichtigsten Bereiche sind:

1. **Sicherheit**: Request-Handling, File-Upload-Validierung, Authentifizierung
2. **Zuverlässigkeit**: Memory-Leaks, Error-Handling, Job-Persistenz
3. **Code-Qualität**: Type Hints, Code-Duplikation, Validierung
4. **Performance**: Ineffiziente Operationen, Memory-Limits

Die meisten Probleme sind gut behebbar und sollten systematisch angegangen werden.
