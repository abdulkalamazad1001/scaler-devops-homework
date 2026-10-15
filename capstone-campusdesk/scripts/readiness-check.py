"""Demonstrate a real 404 readiness failure in a disposable Kind namespace."""

import json
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = f"campusdesk-probe-{uuid.uuid4().hex[:8]}"
BASE = ["kubectl", "--context", "kind-campusdesk", "-n", NAMESPACE]
TRANSCRIPT = [f"Captured: {datetime.now(UTC).isoformat()}\nNamespace: {NAMESPACE}\n"]


def run(*args, document=None):
    command = BASE + list(args)
    result = subprocess.run(command, input=json.dumps(document) if document else None,
                            capture_output=True, text=True, timeout=200, check=False)
    TRANSCRIPT.append(f"$ {' '.join(command)}\n{result.stdout}{result.stderr}\nExit code: {result.returncode}\n")
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def wait_for(check, description):
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(3)
    raise RuntimeError(f"Timed out: {description}")


def main():
    release = json.loads((ROOT / "helm/campusdesk/values-release.json").read_text())
    image = f"{release['backend']['repository']}:{release['backend']['tag']}"
    deployment = {
        "apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "probe-demo"},
        "spec": {"replicas": 1, "selector": {"matchLabels": {"app": "probe-demo"}},
                 "template": {"metadata": {"labels": {"app": "probe-demo"}}, "spec": {
                     "automountServiceAccountToken": False,
                     "containers": [{"name": "api", "image": image,
                                     "ports": [{"containerPort": 8000}],
                                     "resources": {"requests": {"cpu": "10m", "memory": "64Mi"},
                                                   "limits": {"cpu": "100m", "memory": "128Mi"}},
                                     "securityContext": {"runAsNonRoot": True, "runAsUser": 10001,
                                                         "allowPrivilegeEscalation": False,
                                                         "capabilities": {"drop": ["ALL"]}},
                                     "readinessProbe": {"httpGet": {"path": "/missing-probe", "port": 8000},
                                                        "periodSeconds": 2, "failureThreshold": 1}}]}}},
    }
    service = {"apiVersion": "v1", "kind": "Service", "metadata": {"name": "probe-demo"},
               "spec": {"selector": {"app": "probe-demo"}, "ports": [{"port": 8000, "targetPort": 8000}]}}
    created = False
    try:
        run("create", "namespace", NAMESPACE)
        created = True
        run("apply", "-f", "-", document=deployment)
        run("apply", "-f", "-", document=service)

        def failed_probe():
            events = json.loads(run("get", "events", "-o", "json"))
            return any("Readiness probe failed" in event.get("message", "") and
                       "404" in event.get("message", "") for event in events["items"])

        wait_for(failed_probe, "HTTP 404 readiness event")
        pods = json.loads(run("get", "pods", "-l", "app=probe-demo", "-o", "json"))["items"]
        assert pods and pods[0]["status"]["phase"] == "Running"
        assert any(c["type"] == "Ready" and c["status"] == "False" for c in pods[0]["status"]["conditions"])
        run("describe", "pods", "-l", "app=probe-demo")
        run("logs", "deployment/probe-demo", "--tail=15")
        endpoints = json.loads(run("get", "endpointslices", "-l", "kubernetes.io/service-name=probe-demo", "-o", "json"))
        assert not any(e.get("conditions", {}).get("ready") for s in endpoints["items"] for e in s["endpoints"])
        run("exec", "deployment/probe-demo", "--", "python", "-c",
            "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())")
        deployment["spec"]["template"]["spec"]["containers"][0]["readinessProbe"]["httpGet"]["path"] = "/health"
        run("apply", "-f", "-", document=deployment)
        run("rollout", "status", "deployment/probe-demo", "--timeout=150s")

        def ready_endpoint():
            slices = json.loads(run("get", "endpointslices", "-l", "kubernetes.io/service-name=probe-demo", "-o", "json"))
            return any(e.get("conditions", {}).get("ready") for s in slices["items"] for e in s["endpoints"])

        wait_for(ready_endpoint, "ready Service endpoint")
        run("exec", "deployment/probe-demo", "--", "python", "-c",
            "import urllib.request; print(urllib.request.urlopen('http://probe-demo:8000/health').read().decode())")
        run("get", "pods,svc")
        TRANSCRIPT.append("PASS: observed Running/NotReady, 404 probe, healthy process, then repaired ready Service traffic.\n")
    finally:
        try:
            if created:
                run("delete", "namespace", NAMESPACE, "--wait=true", "--timeout=120s")
        finally:
            (ROOT / "evidence/readiness-troubleshooting.txt").write_text("\n".join(TRANSCRIPT), encoding="utf-8")


if __name__ == "__main__":
    main()
