"""Run source/dependency/history gates and retain genuine, redacted reports."""

import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUTPUT = Path(os.environ.get("SECURITY_OUTPUT", ROOT / "evidence/local/security")).resolve()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    npm = shutil.which("npm") or "npm"
    checks = [
        ("bandit", [sys.executable, "-m", "bandit", "-r", "backend/app", "backend/alembic",
                    "--severity-level", "medium", "--confidence-level", "all",
                    "--ignore-nosec", "-f", "json", "-o", str(OUTPUT / "bandit.json")]),
        ("pip-audit", [sys.executable, "-m", "pip_audit", "-r", "backend/requirements-dev.txt",
                       "--strict", "--progress-spinner", "off", "-f", "json",
                       "-o", str(OUTPUT / "pip-audit.json")]),
        ("npm-audit", [npm, "--prefix", str(ROOT / "frontend"), "audit", "--audit-level=high", "--json"]),
        ("gitleaks", ["docker", "run", "--rm", "-v", f"{REPO}:/repo:ro",
                      "-v", f"{OUTPUT}:/reports", "-w", "/repo",
                      "zricethezav/gitleaks:v8.30.1", "git", "--redact", "--no-banner",
                      "--config=/repo/capstone-campusdesk/security/gitleaks.toml",
                      "--log-opts=--all -- capstone-campusdesk .github/workflows/campusdesk.yml",
                      "--report-format=json", "--report-path=/reports/gitleaks.json"]),
    ]
    results = []
    for name, command in checks:
        (OUTPUT / f"{name}.json").unlink(missing_ok=True)
        started = datetime.now(UTC).isoformat()
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=600, check=False)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except (OSError, subprocess.TimeoutExpired) as error:
            code, stdout, stderr = 1, "", str(error)
        if name == "npm-audit":
            (OUTPUT / "npm-audit.json").write_text(stdout, encoding="utf-8")
        (OUTPUT / f"{name}.txt").write_text(
            f"Started: {started}\nCommand: {json.dumps(command)}\n"
            f"{stdout}\n{stderr}\nExit code: {code}\n", encoding="utf-8"
        )
        results.append({"check": name, "started_at": started, "exit_code": code})
        print(f"{name}: {'PASS' if code == 0 else 'FAIL'}", flush=True)
    (OUTPUT / "summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return int(any(result["exit_code"] for result in results))


if __name__ == "__main__":
    sys.exit(main())
