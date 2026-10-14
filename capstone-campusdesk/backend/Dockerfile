FROM python:3.13-alpine
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN apk upgrade --no-cache \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall --yes pip \
    && adduser -D -u 10001 app
COPY --chown=10001:10001 app ./app
COPY --chown=10001:10001 alembic ./alembic
COPY --chown=10001:10001 alembic.ini .
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
