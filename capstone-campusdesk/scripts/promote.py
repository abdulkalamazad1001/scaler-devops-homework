"""Promote only the source SHA whose workflow tests and scans have passed."""
import json
import os
import re
from pathlib import Path

sha = os.environ["GITHUB_SHA"]
if not re.fullmatch(r"[0-9a-f]{40}", sha):
    raise ValueError("Expected full Git commit SHA")
path = Path(__file__).resolve().parents[1] / "helm/campusdesk/values-release.json"
values = json.loads(path.read_text())
for component in ("backend", "frontend"):
    values[component]["tag"] = sha
path.write_text(json.dumps(values, indent=2) + "\n")
