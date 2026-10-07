# syntax=docker/dockerfile:1
# Build from the project root:  docker build -f docker/backend.Dockerfile -t taskboard-backend:local .

FROM python:3.12-slim AS build
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY application/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

FROM python:3.12-slim AS runtime
ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="taskboard-backend" \
      org.opencontainers.image.source="https://github.com/devops-student/final-devops-project" \
      org.opencontainers.image.version="${APP_VERSION}"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    APP_VERSION=${APP_VERSION}

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY application/backend/alembic.ini ./
COPY application/backend/alembic ./alembic
COPY application/backend/app ./app

USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]

# Run migrations (serialised by an advisory lock, see alembic/env.py), then
# replace the shell with uvicorn so it receives SIGTERM directly.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
