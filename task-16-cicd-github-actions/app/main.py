"""HTTP layer for the calculator.

Endpoints:
    GET /                       service name and version
    GET /health                 liveness/readiness check
    GET /api/<op>?a=<n>&b=<n>   op is add, subtract, multiply or divide
"""
import os

from flask import Flask, jsonify, request

from app.calculator import OPERATIONS


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return jsonify(
            service="cicd-demo",
            version=os.environ.get("APP_VERSION", "dev"),
            environment=os.environ.get("APP_ENV", "local"),
            secret_configured=bool(os.environ.get("SECRET_KEY")),
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/<op>")
    def calculate(op):
        func = OPERATIONS.get(op)
        if func is None:
            return jsonify(error=f"unknown operation '{op}'"), 404
        try:
            a = float(request.args["a"])
            b = float(request.args["b"])
        except KeyError as exc:
            return jsonify(error=f"missing query parameter {exc.args[0]}"), 400
        except ValueError:
            return jsonify(error="a and b must be numbers"), 400
        try:
            result = func(a, b)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(operation=op, a=a, b=b, result=result)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
