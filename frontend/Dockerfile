FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

# Generate config.js at startup so the React app can read the
# backend URL at runtime (no build-time env vars needed).
# BACKEND_URL must be set in Railway / Docker Compose.
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD BACKEND_URL="${BACKEND_URL:-http://backend:8000}" && \
    echo "window.__API_URL__ = '${BACKEND_URL}';" \
      > /usr/share/nginx/html/config.js && \
    nginx -g "daemon off;"
