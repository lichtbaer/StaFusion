FROM node:20-alpine AS build
WORKDIR /app
COPY ../packages/datafusion-mfe/package.json ./packages/datafusion-mfe/package.json
WORKDIR /app/packages/datafusion-mfe
RUN npm install --legacy-peer-deps
COPY ../.. /app
WORKDIR /app/packages/datafusion-mfe
RUN npm run build && npm run build:wc

FROM nginx:1.27-alpine AS run
RUN apk add --no-cache bash curl jq gettext
WORKDIR /usr/share/nginx/html
COPY --from=build /app/packages/datafusion-mfe/dist/ ./
COPY --from=build /app/packages/datafusion-mfe/dist-wc/web-component.js ./web-component.js
COPY ../packages/datafusion-mfe/public/config.template.js /etc/nginx/templates/config.template.js
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV API_BASE=http://localhost:8000 \
    AUTH_ENABLED=false \
    JWT_TOKEN= \
    PERSISTENCE_ENABLED=false \
    MAX_UPLOAD_MB=20 \
    DEFAULT_LANG=en
EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]

