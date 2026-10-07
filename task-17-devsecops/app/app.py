"""Small Flask API used as the target of the DevSecOps pipeline."""

import datetime
import os
import platform
import sys

from flask import Flask, jsonify, request

APP_VERSION = os.environ.get("APP_VERSION", "dev")

app = Flask(__name__)

_start_time = datetime.datetime.now(datetime.timezone.utc)
_request_count = 0


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


@app.before_request
def _count_request():
    global _request_count
    _request_count += 1


@app.route("/")
def home():
    return jsonify({
        "app": "devsecops-demo",
        "version": APP_VERSION,
        "endpoints": ["/health", "/api/status", "/api/greet/<name>", "/api/calculate"],
    })


@app.route("/health")
def health():
    uptime = (_now() - _start_time).total_seconds()
    return jsonify({"status": "healthy", "uptime_seconds": round(uptime, 2)})


@app.route("/api/status")
def status():
    return jsonify({
        "app": "devsecops-demo",
        "version": APP_VERSION,
        "status": "running",
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "total_requests": _request_count,
        "timestamp": _now().isoformat(),
    })


@app.route("/api/greet/<name>")
def greet(name):
    # jsonify escapes the value, so the name cannot inject HTML into a page.
    return jsonify({"message": f"Hello, {name}!", "name": name})


OPERATIONS = {
    "add": lambda a, b: a + b,
    "subtract": lambda a, b: a - b,
    "multiply": lambda a, b: a * b,
    "divide": lambda a, b: a / b,
}


@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    op = data.get("operation", "add")
    if op not in OPERATIONS:
        return jsonify({"error": f"unknown operation '{op}'", "valid": sorted(OPERATIONS)}), 400

    try:
        a = float(data["a"])
        b = float(data["b"])
    except KeyError:
        return jsonify({"error": "fields 'a' and 'b' are required"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "'a' and 'b' must be numbers"}), 400

    if op == "divide" and b == 0:
        return jsonify({"error": "division by zero"}), 400

    return jsonify({"a": a, "b": b, "operation": op, "result": OPERATIONS[op](a, b)})


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    # Local development only. In the container gunicorn serves the app.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
