"""Run isolated failure exercises and preserve real diagnostic output."""
import json
import subprocess
import time
from datetime import datetime, UTC
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = ["kubectl", "--context", "kind-campusdesk", "-n", "campusdesk"]
transcript = [f"Captured {datetime.now(UTC).isoformat()}\n"]


def run(*args):
    result = subprocess.run(base + list(args), cwd=root, capture_output=True, text=True, timeout=180)
    transcript.append(f"$ {' '.join(base + list(args))}\n{result.stdout}{result.stderr}\nExit code: {result.returncode}\n")
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


try:
    run("apply", "-f", "troubleshooting/broken-service.yaml")
    run("get", "service", "broken-backend-demo", "-o", "yaml")
    run("get", "endpointslices", "-l", "kubernetes.io/service-name=broken-backend-demo", "-o", "json")
    run("set", "selector", "service/broken-backend-demo", "app=backend")
    time.sleep(2)
    fixed = json.loads(run("get", "endpointslices", "-l", "kubernetes.io/service-name=broken-backend-demo", "-o", "json"))
    assert any(item.get("endpoints") for item in fixed["items"])
    run("apply", "-f", "troubleshooting/broken-image.yaml")
    deadline = time.monotonic() + 150
    observed = False
    while time.monotonic() < deadline:
        pods = json.loads(subprocess.check_output(base + ["get", "pods", "-l", "app=broken-image-demo", "-o", "json"]))
        for pod in pods["items"]:
            for status in pod["status"].get("containerStatuses", []):
                if status.get("state", {}).get("waiting", {}).get("reason") in ("ErrImagePull", "ImagePullBackOff"):
                    observed = True
        if observed:
            break
        time.sleep(2)
    assert observed, "Image failure did not appear within the timeout"
    run("get", "pods", "-l", "app=broken-image-demo")
    run("describe", "pods", "-l", "app=broken-image-demo")
    run("set", "image", "deployment/broken-image-demo", "demo=campusdesk-frontend:local")
    run("rollout", "status", "deployment/broken-image-demo", "--timeout=120s")
    run("get", "pods", "-l", "app=broken-image-demo")
finally:
    for kind, name in [("service", "broken-backend-demo"), ("deployment", "broken-image-demo")]:
        run("delete", kind, name, "--ignore-not-found")
    (root / "evidence/troubleshooting.txt").write_text("\n".join(transcript), encoding="utf-8")
print("Observed and fixed missing endpoints and ImagePullBackOff; removed both demo objects.")
