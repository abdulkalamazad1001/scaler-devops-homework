"""Small web app used to demonstrate metrics, logs, alerts and health checks.

Endpoints
  GET /          normal request
  GET /health    liveness: the process is up
  GET /ready     readiness: the app is willing to take traffic
  GET /work      burns CPU for ?ms=<n> milliseconds (default 200)
  GET /alloc     keeps ?mb=<n> megabytes of memory alive (default 20)
  GET /free      releases the memory held by /alloc
  GET /error     always returns HTTP 500
  GET /metrics   Prometheus metrics
"""

import json
import logging
import os
import sys
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = Flask(__name__)

REQUESTS = Counter(
    "demo_http_requests_total",
    "Total HTTP requests handled by the demo app.",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "demo_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
HELD_MEMORY = Gauge("demo_held_memory_bytes", "Bytes currently held by /alloc.")
BUILD_INFO = Gauge("demo_build_info", "Build information.", ["version"])
BUILD_INFO.labels(version=APP_VERSION).set(1)

_held = []


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + "Z",
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
        }
        entry.update(getattr(record, "extra_fields", {}))
        return json.dumps(entry)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
log = logging.getLogger("metrics-demo")
log.addHandler(handler)
log.setLevel(os.getenv("LOG_LEVEL", "INFO"))
log.propagate = False


@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record(response):
    path = request.url_rule.rule if request.url_rule else "unmatched"
    if path == "/metrics":
        return response
    duration = time.perf_counter() - g.start
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    LATENCY.labels(path).observe(duration)
    level = logging.ERROR if response.status_code >= 500 else logging.INFO
    if path not in ("/health", "/ready") or response.status_code != 200:
        log.log(
            level,
            "request",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 1),
            }},
        )
    return response


@app.get("/")
def index():
    return jsonify(service="metrics-demo", version=APP_VERSION)


@app.get("/health")
def health():
    return jsonify(status="UP")


@app.get("/ready")
def ready():
    return jsonify(status="READY")


@app.get("/work")
def work():
    ms = min(int(request.args.get("ms", 200)), 5000)
    end = time.perf_counter() + ms / 1000
    n = 0
    while time.perf_counter() < end:
        n += 1
    return jsonify(burned_ms=ms, loops=n)


@app.get("/alloc")
def alloc():
    mb = min(int(request.args.get("mb", 20)), 200)
    _held.append(bytearray(mb * 1024 * 1024))
    total = sum(len(b) for b in _held)
    HELD_MEMORY.set(total)
    return jsonify(held_mb=total // (1024 * 1024))


@app.get("/free")
def free():
    _held.clear()
    HELD_MEMORY.set(0)
    return jsonify(held_mb=0)


@app.get("/error")
def error():
    return jsonify(error="simulated failure"), 500


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
