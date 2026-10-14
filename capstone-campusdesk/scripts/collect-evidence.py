"""Capture actual command output with timestamps and exit codes; never synthesize results."""
import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path

root = Path(__file__).resolve().parents[1]
repo = root.parent
evidence = root / "evidence"
evidence.mkdir(exist_ok=True)
kubectl = ["kubectl", "--context", "kind-campusdesk"]
helm = str(repo / "tools/helm/windows-amd64/helm.exe")
terraform = str(repo / "tools/terraform/terraform.exe")
python = str(root / ".venv/Scripts/python.exe")
checks = [
    ("pytest", [python, "-m", "pytest", "-v"], root / "backend"),
    ("ruff", [python, "-m", "ruff", "check", "."], root / "backend"),
    ("compose", ["docker", "compose", "ps"], root),
    ("non-root", ["docker", "image", "inspect", "campusdesk-backend:local", "campusdesk-frontend:local", "--format", "{{.RepoTags}} user={{.Config.User}}"], root),
    ("kubernetes", kubectl + ["-n", "campusdesk", "get", "pods,svc,ingress,hpa"], root),
    ("helm", [helm, "--kube-context", "kind-campusdesk", "list", "-n", "campusdesk"], root),
    ("terraform-validate", [terraform, "-chdir=terraform", "validate", "-no-color"], root),
    ("argocd", kubectl + ["-n", "argocd", "get", "application", "campusdesk", "-o", "json"], root),
    ("metrics", ["curl.exe", "-fsS", "http://localhost:8000/metrics"], root),
    ("commit-history", ["git", "log", "-15", "--format=%h %s"], repo),
]
summary = []
if "--compose-build" in sys.argv:
    checks.insert(0, ("compose-build", ["docker", "compose", "up", "--build", "-d"], root))
for name, command, cwd in checks:
    captured = datetime.now(UTC).isoformat()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900 if name == "compose-build" else 180)
    record = {"name": name, "capturedAt": captured, "command": command, "exitCode": result.returncode,
              "stdout": result.stdout, "stderr": result.stderr}
    (evidence / f"{name}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (evidence / f"{name}.txt").write_text(f"Captured at {captured}\nCommand: {' '.join(command)}\nExit code: {result.returncode}\n\n{result.stdout}\n{result.stderr}", encoding="utf-8")
    summary.append({"name": name, "exitCode": result.returncode, "capturedAt": captured})
    print(f"{name}: exit {result.returncode}")
(evidence / "checks.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
raise SystemExit(1 if any(check["exitCode"] != 0 for check in summary) else 0)
