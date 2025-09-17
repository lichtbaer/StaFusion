#!/usr/bin/env bash
set -euo pipefail

TEMPLATE=/etc/nginx/templates/config.template.js
OUT=/usr/share/nginx/html/config.js

envsubst '\n$API_BASE\n$AUTH_ENABLED\n$JWT_TOKEN\n$PERSISTENCE_ENABLED\n$MAX_UPLOAD_MB\n$DEFAULT_LANG\n' < "$TEMPLATE" > "$OUT"

echo "Rendered config.js:" && cat "$OUT" | sed 's/JWT_TOKEN=.*/JWT_TOKEN=***redacted***/'

exec nginx -g 'daemon off;'

