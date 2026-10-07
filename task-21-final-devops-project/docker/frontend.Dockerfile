# syntax=docker/dockerfile:1
# Build from the project root:  docker build -f docker/frontend.Dockerfile -t taskboard-frontend:local .

FROM node:22-alpine AS build
WORKDIR /app
COPY application/frontend/package.json application/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY application/frontend/ ./
RUN npm run build

# nginx-unprivileged runs as uid 101 and listens on 8080 instead of 80.
FROM nginxinc/nginx-unprivileged:1.28-alpine AS runtime
ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="taskboard-frontend" \
      org.opencontainers.image.source="https://github.com/devops-student/final-devops-project" \
      org.opencontainers.image.version="${APP_VERSION}"
# Where nginx forwards /api/. Docker Compose uses the service name "backend";
# Kubernetes overrides it with the backend Service name.
ENV BACKEND_URL=http://backend:8000
COPY docker/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
# Already the default in this base image; stated here so scanners and readers can see it.
USER 101
EXPOSE 8080
