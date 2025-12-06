# Nächste Schritte - datafusion-ml

**Erstellt:** Nach Projekt-Inspektion  
**Status:** Planung für kommende Entwicklung

---

## ✅ Erledigt

1. **Request-ID-Middleware implementiert und getestet**
   - Funktion `request_id_middleware` in `middleware.py` hinzugefügt
   - UUID-Generierung, Request-State, Response-Header
   - Logger-Adapter für Korrelation
   - Tests hinzugefügt (`tests/test_middleware.py`)

2. **Frontend-Tests eingerichtet**
   - Vitest konfiguriert
   - Test-Setup erstellt
   - Unit-Tests für State-Management und API-Client

3. **CI/CD Pipeline erweitert**
   - Frontend-Job in CI
   - Frontend-Tests und Build integriert
   - Build-Artefakte werden hochgeladen

4. **README aktualisiert**
   - Badge-Platzhalter entfernt
   - Deployment-Guide erstellt (`docs/deployment.md`)
   - Konfigurationsdokumentation erweitert

---

## 🟡 Hohe Priorität (Nächste 2 Wochen)

### 1. Frontend-Tests erweitern
**Aufwand:** 2-3 Tage  
**Ziel:** Test-Abdeckung für Frontend erhöhen

**Schritte:**
1. Komponententests
   - [ ] `FileDrop.tsx` testen
   - [ ] `UploadPage.tsx` testen
   - [ ] `ResultsPage.tsx` testen
   - [ ] Wizard-Navigation testen

2. E2E-Tests (optional)
   - [ ] Playwright-Setup
   - [ ] Docker Compose für lokales Backend
   - [ ] E2E-Test-Job in CI

**Dateien:**
- `frontend/packages/datafusion-mfe/src/**/*.test.tsx` (erweitern)
- `tests/e2e/` (neu, optional)

---

## 🟢 Mittlere Priorität (Nächster Monat)

### 5. Code-Qualität verbessern
**Aufwand:** 2-3 Tage

**Schritte:**
1. Code-Duplikation reduzieren
   - [ ] PyCaret-Trainer refactoren (Classification/Regression)
   - [ ] Gemeinsame Logik extrahieren

2. Performance-Optimierungen
   - [ ] DataFrame-Operationen optimieren (`fusion.py:155-159`)
   - [ ] Memory-Profiling durchführen
   - [ ] Bottlenecks identifizieren

3. Edge-Case-Tests
   - [ ] Leere DataFrames
   - [ ] Sehr große DataFrames
   - [ ] Korrupte Dateien
   - [ ] Memory-Limits

**Dateien:**
- `datafusion_ml/modeling.py` (refactoren)
- `datafusion_ml/fusion.py` (optimieren)
- `tests/test_edge_cases.py` (neu)

---

### 6. Dokumentation erweitern
**Aufwand:** 1-2 Tage

**Schritte:**
1. OpenAPI-Schema verbessern
   - [ ] Beispiele für alle Endpoints hinzufügen
   - [ ] Response-Schemas vollständig dokumentieren

2. Error-Handling-Guide
   - [ ] Alle Custom Exceptions dokumentieren
   - [ ] HTTP-Status-Codes erklären
   - [ ] Beispiele für Error-Handling

3. Deployment-Guides
   - [ ] Nginx-Konfiguration
   - [ ] Docker Compose Setup
   - [ ] Kubernetes-Beispiele (optional)

**Dateien:**
- `datafusion_ml/web/schemas.py` (erweitern)
- `docs/deployment.md` (neu)
- `docs/error-handling.md` (neu)

---

### 7. Frontend-Features finalisieren
**Aufwand:** 3-5 Tage

**Schritte:**
1. Wizard-Validierung verbessern
   - [ ] Overlap-Features-Validierung
   - [ ] Targets-Validierung
   - [ ] Tooltips hinzufügen

2. Metriken-Tab implementieren
   - [ ] `metrics_a_to_b` darstellen
   - [ ] `metrics_b_to_a` darstellen
   - [ ] Visualisierung (optional)

3. Persistenz (IndexedDB) optional
   - [ ] Feature-Flag implementieren
   - [ ] Letzte Konfiguration speichern
   - [ ] Ergebnisse speichern (optional)

**Dateien:**
- `frontend/packages/datafusion-mfe/src/pages/*.tsx` (erweitern)
- `frontend/packages/datafusion-mfe/src/state/AppState.tsx` (erweitern)

---

## 🔵 Langfristig (Nächster Monat+)

### 8. Performance & Monitoring
**Aufwand:** 2-3 Tage

- [ ] Memory-Monitoring im Backend
- [ ] Web Vitals im Frontend
- [ ] Sentry-Integration (optional)
- [ ] Prometheus-Metriken erweitern

### 9. Sicherheit
**Aufwand:** 1-2 Tage

- [ ] CSP-Header implementieren
- [ ] Security-Headers (HSTS, etc.)
- [ ] Dependency-Audits automatisieren
- [ ] Bandit-Scan in CI

### 10. Release-Vorbereitung
**Aufwand:** 1 Tag

- [ ] Release-Checkliste abarbeiten (TODO.md)
- [ ] Changelog erstellen
- [ ] Version-Tagging
- [ ] PyPI-Release testen

---

## 📋 Offene TODOs (aus TODO.md)

### Frontend
- [ ] Wizard-Feinschliff (Validierung, Tooltips)
- [ ] Metriken-Tab: `metrics_a_to_b`/`metrics_b_to_a` darstellen
- [ ] Persistenz (IndexedDB) per Feature-Flag
- [ ] Web Component: Custom Events verdrahten
- [ ] A11y: Tastaturnavigation, ARIA
- [ ] Tests: Unit, Komponenten, E2E

### Backend
- [ ] Optional: Cancel-Endpoint für Async-Jobs (`DELETE /v1/fuse/async/{job_id}`)
- [ ] Prometheus-Metriken erweitern (Job-Zahlen, Dauer, Fehlerquoten)
- [ ] OpenAPI: Beispiele hinzufügen
- [ ] Betrieb: Nginx-Beispiele, Rate Limiting, TLS

### Sicherheit & DSGVO
- [ ] CSP ohne `unsafe-inline`
- [ ] Security-Headers (HSTS, etc.)
- [ ] Protokollierung: PII-Redaktion
- [ ] Löschkonzept: TTL für Jobs (bereits implementiert, dokumentieren)

---

## 🎯 Sprint-Planung (Vorschlag)

### Sprint 1 (Diese Woche)
1. ✅ Request-ID-Middleware implementiert
2. Request-ID-Middleware testen
3. README aktualisieren

### Sprint 2 (Nächste Woche)
1. Frontend-Tests einrichten (Vitest)
2. Unit-Tests für State-Management
3. CI/CD erweitern (Frontend-Build)

### Sprint 3 (Woche 3-4)
1. Komponententests
2. Code-Qualität verbessern
3. Dokumentation erweitern

### Sprint 4 (Woche 5-6)
1. Frontend-Features finalisieren
2. E2E-Tests (optional)
3. Performance-Optimierungen

---

## 📊 Metriken & Ziele

### Code-Qualität
- **Aktuell:** Backend-Tests vorhanden, Frontend-Tests fehlen
- **Ziel:** >80% Test-Abdeckung (Backend + Frontend)

### CI/CD
- **Aktuell:** Nur Backend-Tests
- **Ziel:** Vollständige Pipeline (Backend + Frontend + E2E)

### Dokumentation
- **Aktuell:** README vorhanden, Deployment-Guide fehlt
- **Ziel:** Vollständige Dokumentation (API, Deployment, Error-Handling)

---

## 🔗 Verwandte Dokumente

- `PROJECT_STATUS.md` - Detaillierter Projekt-Status
- `TECHNICAL_DEBT_STATUS.md` - Status technischer Schulden
- `TODO.md` - Offene Anforderungen
- `INSPECTION_REPORT.md` - Detaillierte Code-Inspektion
