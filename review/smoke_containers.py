"""Build Docker homework apps, check HTTP, then remove only our test containers."""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime

from run_checks import RESULTS, ROOT, run


def main():
    checks = []
    apps = [
        ("task5-node", "task-5-docker/nodejs-app", 3000, "Hello"),
        ("task5-python", "task-5-docker/python-app", 5000, "Hello"),
        ("task5-java", "task-5-docker/java-app", 8080, "Hello"),
        ("task5-react", "task-5-docker/React-app", 80, "root"),
        ("task5-nginx", "task-5-docker/nginx-app", 80, "Hello"),
        ("task5-apache", "task-5-docker/Apache-app", 80, "Hello"),
        ("task6-multistage", "task-6-docker-multistage/multi-stage-app", 3000, "Hello"),
    ]
    for name, folder, port, expected in apps:
        tag = f"homework-review/{name}:local"
        build = run(f"{name}-build", ["docker", "build", "-t", tag, folder])
        checks.append(build)
        if build["exit_code"]:
            continue
        container = f"{name}-review-{uuid.uuid4().hex[:8]}"
        try:
            launch = run(f"{name}-start", ["docker", "run", "-d", "--name", container,
                                          "-p", f"127.0.0.1::{port}", tag])
            checks.append(launch)
            if launch["exit_code"]:
                continue
            address = subprocess.check_output(["docker", "port", container, f"{port}/tcp"], text=True).strip()
            last_error = "No HTTP response"
            for _ in range(40):
                try:
                    with urllib.request.urlopen(f"http://{address}/", timeout=3) as response:
                        body = response.read().decode()
                        assert response.status == 200 and expected.lower() in body.lower(), body
                    last_error = ""
                    (RESULTS / f"{name}-http.txt").write_text(f"HTTP 200\n{body}", encoding="utf-8")
                    break
                except (OSError, AssertionError) as error:
                    last_error = str(error)
                    time.sleep(1)
            checks.append({"check": f"{name}-http", "exit_code": int(bool(last_error)), "error": last_error})
            if name == "task6-multistage":
                checks.append(run(f"{name}-nonroot", ["docker", "exec", container, "sh", "-ec", 'test "$(id -u)" != 0; id']))
            checks.append(run(f"{name}-logs", ["docker", "logs", container]))
        finally:
            checks.append(run(f"{name}-cleanup", ["docker", "rm", "-f", container]))
    (RESULTS / "containers.json").write_text(json.dumps({
        "captured_at": datetime.now(UTC).isoformat(), "checks": checks,
        "scope": "Docker builds and HTTP smoke checks, not browser or security certification."
    }, indent=2) + "\n", encoding="utf-8")
    return int(any(check["exit_code"] for check in checks))


if __name__ == "__main__":
    sys.exit(main())
