# TODO / Anforderungen

Dieses Dokument hält die noch offenen Schritte und Anforderungen für Frontend und Backend fest.

## Frontend (datafusion-mfe)
- Authentifizierung
  - JWT aus Runtime-Config lesen (erledigt); sichere Bereitstellung dokumentieren.
  - Optionales Token-Eingabefeld im Standalone-Modus (per Env togglebar).
- Wizard-Feinschliff
  - Überlappung: Schnittmenge der Spalten aus Previews erkennen; manuelle Auswahl/Entfernung.
  - Ziele: Exklusive Spalten als Vorschlag; Multi-Select mit Suche.
  - Einstellungen: Vollständige Abbildung der Backend-Optionen, Tooltips, Validierung.
- Upload- & JSON-Flows
  - Upload via `/v1/fuse/upload` (erledigt); Fehlermeldungen (413/422) verbessern.
  - Async-JSON-Flow (erledigt); Cancel einbauen, sobald Endpoint verfügbar.
- Ergebnisse
  - MUI Data Grid mit Spaltenauswahl + CSV/JSON-Download (erledigt).
  - Optional: Parquet-Download clientseitig (Arrow) hinter leichtgewichtiger Dep.
  - Metriken-Tab: `metrics_a_to_b`/`metrics_b_to_a` lesbar darstellen.
- Persistenz (per Feature-Flag)
  - Lokale Persistenz (IndexedDB) für letzte Konfiguration/Ergebnisse; per Env deaktivierbar.
  - Perspektivisch: Integration einer Backend-Job-Historie (falls vorhanden).
- Web Component
  - Attribute: `api-base`, `auth-enabled`, `jwt-token`, `lang`, `max-upload-mb`, `persistence-enabled` (erledigt).
  - Custom Events: `fusion:completed`, `fusion:error`, `fusion:job-status` verdrahten.
- Internationalisierung & A11y
  - Übersetzungen ausbauen (EN Standard, DE gepflegt); Language-Switcher (erledigt).
  - Tastaturnavigation, Landmarken, ARIA für Wizard-Steuerungen.
- Observability
  - Optional Sentry; PII-Redaktion; via Env konfigurierbar.
- Qualitätssicherung
  - Unit-Tests (Vitest) für Helpers/State.
  - Komponententests (Testing Library) für Seiten.
  - E2E (Playwright): Upload-Flow, Async-Flow, Downloads.
- CI/CD
  - GitHub Actions: Lint, Typecheck, Tests, Build, Artefakt.
  - Nginx-Image bauen und veröffentlichen (env-injected `config.js`).
- Doku
  - Nutzung Standalone & als Web Component; Env-Matrix; Deployment-Guides.

## Backend (FastAPI)
- Auth
  - JWT-Validierungsmiddleware (per Env aktivier-/deaktivierbar für Standalone).
  - CORS pro Umgebung einschränken; erlaubte Header dokumentieren.
- Async Jobs
  - Optional: Cancel-Endpoint (z. B. `DELETE /v1/fuse/async/{job_id}`), wenn umsetzbar.
  - Optional: Persistenz (DB) mit TTL; Endpunkte zum Listen/Abrufen.
- Upload-Limits & Validierung
  - 20 MB Body-Limit per Config (vorhanden); präzisere Fehlermeldungen ausgeben.
  - CSV/Parquet-Schema-Prüfung; optionale Spalten-Whitelist/Blacklist per Env.
- Metriken/Health
  - Prometheus erweitern (Job-Zahlen, Dauer, Fehlerquoten).
- OpenAPI/SDK
  - `/openapi.json` vollständig/aktuell halten; Stabilität v1; Schemas für Metriken prüfen.
- Betrieb
  - Nginx/Reverse Proxy Beispiele; Rate Limiting; Request Size; TLS.
  - Logging mit `job_id`-Korrelation; strukturiert (json) (vorhanden).

## Sicherheit & DSGVO
- Datenminimierung: Keine personenbezogenen Daten unnötig im FE persistieren; optionaler Persistenz-Flag standardmäßig aus.
- Transportverschlüsselung: HTTPS erzwingen (HSTS über Nginx), keine gemischten Inhalte.
- Content Security Policy: strenge CSP ohne `unsafe-inline`; Nonces/Hashes verwenden.
- Headers: `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `X-Frame-Options` (oder `frame-ancestors` via CSP).
- Protokollierung: Keine sensiblen Nutzdaten in Logs; Job-IDs zulassen.
- Auftragsverarbeitung: Falls externe Dienste (Sentry/CDN) genutzt werden, AVV sicherstellen.
- Löschkonzept: TTL für persistente Jobs; Export/Deletion-Routen spezifizieren, wenn Datenhaltung aktiviert wird.

## Performance-Ziele
- FE LCP < 2.5s bei 3G/Low-End Desktop (Lazy-Load, Code-Splitting, leichte Fonts).
- Tabellen: Virtualisierung, Pagination; initial < 1k Zeilen rendern.
- Upload: Clientseitige 20 MB Validierung; keine unkomprimierten großen JSON-Körper.
- Caching: HTTP Caching für statische Assets (immutable), Runtime `config.js` no-store.
- Monitoring: Web Vitals in Sentry/Analytics optional erfassen.

## CI/CD Pipeline (Vorschlag)
- Jobs
  - lint: Ruff (Backend), ESLint (FE)
  - typecheck: mypy (Backend), tsc (FE)
  - test: pytest (Backend), Vitest (FE)
  - e2e: Playwright (FE) gegen lokalem FastAPI (Docker Compose)
  - build: wheel (Backend optional), FE SPA + WC, Nginx-Image
  - security: Bandit (Backend), `npm audit` (FE), `pip-audit` optional
- Artefakte & Releases
  - FE: Upload der `dist/`, `dist-wc/` und Nginx-Image in Registry
  - Versionierung: semver; Changelog; Release Notes
- Gates
  - PR: alle Checks grün (lint/type/test/build)
  - Main: Protected Branch; required reviews; dependabot aktivieren

## Release-Checkliste
- [ ] Frontend: Wizard finalisieren inkl. Validierung
- [ ] Frontend: E2E-Tests grün in CI
- [ ] Frontend: Nginx-Image gebaut und veröffentlicht
- [ ] Backend: JWT optionale Auth live
- [ ] Backend: Entscheidung/Umsetzung Cancel/Persistenz
- [ ] Doku aktualisiert (Embedding, Konfiguration, Deployment)