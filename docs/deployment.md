# Deployment Guide

Dieser Guide beschreibt verschiedene Deployment-Optionen für datafusion-ml.

## Backend (FastAPI)

### Docker

Das Projekt enthält ein `Dockerfile` für die API:

```bash
# Image bauen
docker build -t datafusion-ml-api .

# Container starten
docker run --rm -p 8000:8000 \
  -e DFML_LOG_LEVEL=INFO \
  -e DFML_LOG_FORMAT=json \
  -e DFML_CORS_ENABLED=true \
  -e DFML_MAX_BODY_MB=50 \
  -e DFML_MAX_ROWS=200000 \
  datafusion-ml-api
```

### Mit Nginx als Reverse Proxy

**nginx.conf Beispiel:**

```nginx
upstream datafusion_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.example.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Request size limit
    client_max_body_size 50M;

    location / {
        proxy_pass http://datafusion_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts für große Requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### Mit TLS/HTTPS

**Nginx mit Let's Encrypt:**

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://datafusion_api;
        # ... (wie oben)
    }
}
```

### Environment-Variablen

Wichtige Konfigurationsoptionen:

```bash
# CORS
DFML_CORS_ENABLED=true
DFML_CORS_ORIGINS=https://example.com,https://www.example.com
DFML_CORS_ALLOW_CREDENTIALS=false

# Authentifizierung
DFML_JWT_ENABLED=true
DFML_JWT_SECRET=your-secret-key-here
DFML_JWT_ALGORITHM=HS256

# Rate Limiting
DFML_RATE_LIMIT_ENABLED=true
DFML_RATE_LIMIT_PER_MINUTE=60

# Job Persistenz
DFML_JOB_PERSISTENCE_ENABLED=true
DFML_JOB_PERSISTENCE_PATH=/var/lib/datafusion-ml/jobs

# Limits
DFML_MAX_BODY_MB=50
DFML_MAX_ROWS=200000

# Logging
DFML_LOG_LEVEL=INFO
DFML_LOG_FORMAT=json
```

## Frontend

### Standalone SPA

Das Frontend kann als statische SPA bereitgestellt werden:

```bash
cd frontend/packages/datafusion-mfe
npm install
npm run build
```

Die gebauten Dateien befinden sich in `dist/` und können mit einem Webserver (Nginx, Apache) bereitgestellt werden.

### Nginx-Konfiguration für Frontend

```nginx
server {
    listen 80;
    server_name app.example.com;
    root /var/www/datafusion-mfe/dist;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Web Component

Das Frontend kann auch als Web Component eingebettet werden:

```bash
npm run build:wc
```

Die Web Component wird in `dist-wc/` gebaut und kann in andere HTML-Seiten eingebunden werden:

```html
<!DOCTYPE html>
<html>
<head>
    <script type="module" src="https://example.com/datafusion-mfe.js"></script>
</head>
<body>
    <datafusion-mfe
        api-base="https://api.example.com"
        auth-enabled="true"
        jwt-token="your-token"
        lang="de"
    ></datafusion-mfe>
</body>
</html>
```

### Docker für Frontend

Das Projekt enthält ein Frontend-Dockerfile:

```bash
cd frontend/docker
docker build -t datafusion-mfe .
docker run --rm -p 80:80 datafusion-mfe
```

## Docker Compose (Full Stack)

**docker-compose.yml Beispiel:**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DFML_CORS_ENABLED=true
      - DFML_CORS_ORIGINS=http://localhost:5173
      - DFML_LOG_LEVEL=INFO
      - DFML_MAX_BODY_MB=50
    volumes:
      - ./jobs:/tmp/datafusion-ml-jobs

  frontend:
    build:
      context: ./frontend/docker
    ports:
      - "80:80"
    environment:
      - API_BASE=http://api:8000
    depends_on:
      - api
```

## Kubernetes

### Backend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datafusion-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: datafusion-api
  template:
    metadata:
      labels:
        app: datafusion-api
    spec:
      containers:
      - name: api
        image: datafusion-ml-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DFML_LOG_LEVEL
          value: "INFO"
        - name: DFML_CORS_ENABLED
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: datafusion-api
spec:
  selector:
    app: datafusion-api
  ports:
  - port: 80
    targetPort: 8000
```

## Monitoring

### Prometheus

Die API stellt Metriken unter `/metrics` bereit:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'datafusion-api'
    static_configs:
      - targets: ['api:8000']
```

### Health Checks

Health-Endpoint: `GET /v1/health`

```bash
curl http://localhost:8000/v1/health
# {"status":"ok"}
```

## Sicherheit

### Empfohlene Einstellungen für Produktion

1. **CORS:** Explizite Origins statt `*`
2. **JWT:** Starke Secrets, regelmäßige Rotation
3. **Rate Limiting:** Aktiviert mit angemessenen Limits
4. **TLS:** HTTPS erzwingen (HSTS)
5. **Security Headers:** CSP, X-Frame-Options, etc.
6. **Logging:** Keine sensiblen Daten in Logs

### Content Security Policy

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

## Troubleshooting

### API startet nicht

- Prüfe Logs: `docker logs <container-id>`
- Prüfe Environment-Variablen
- Prüfe Port-Konflikte

### CORS-Fehler

- Stelle sicher, dass `DFML_CORS_ORIGINS` die korrekten Origins enthält
- Prüfe, ob `DFML_CORS_ENABLED=true` gesetzt ist

### Rate Limiting zu strikt

- Erhöhe `DFML_RATE_LIMIT_PER_MINUTE`
- Oder deaktiviere mit `DFML_RATE_LIMIT_ENABLED=false`

### Jobs gehen nach Neustart verloren

- Aktiviere Persistenz: `DFML_JOB_PERSISTENCE_ENABLED=true`
- Stelle sicher, dass `DFML_JOB_PERSISTENCE_PATH` auf persistenten Storage zeigt
