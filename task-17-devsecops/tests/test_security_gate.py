import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "security_gate", Path(__file__).resolve().parents[1] / "scripts/security_gate.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

CLEAN = {
    "bandit.json": {"results": [], "errors": []},
    "pip-audit.json": {"dependencies": [{"name": "demo", "version": "1", "vulns": []}]},
    "gitleaks.json": [],
    "trivy-image.json": {"Results": [{"Target": "demo", "Vulnerabilities": []}]},
}


@pytest.fixture
def reports(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    for name, data in CLEAN.items():
        (tmp_path / name).write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def test_clean_reports_pass(reports):
    assert gate.main(["security_gate.py", str(reports)]) == 0


@pytest.mark.parametrize("filename", CLEAN)
@pytest.mark.parametrize("replacement", [None, {}, "invalid"])
def test_malformed_reports_fail_closed(reports, filename, replacement):
    (reports / filename).write_text(json.dumps(replacement), encoding="utf-8")
    assert gate.main(["security_gate.py", str(reports)]) == 1


@pytest.mark.parametrize("filename", CLEAN)
def test_missing_reports_fail_closed(reports, filename):
    (reports / filename).unlink()
    assert gate.main(["security_gate.py", str(reports)]) == 1


@pytest.mark.parametrize("filename,data", [
    ("bandit.json", {"results": [], "errors": [{"reason": "parse error"}]}),
    ("pip-audit.json", {"dependencies": [{"name": "unknown", "skip_reason": "not found"}]}),
    ("pip-audit.json", {"dependencies": [{"name": "demo", "version": "1", "vulns": [
        {"id": "TEST-1", "fix_versions": ["2"]}
    ]}]}),
    ("gitleaks.json", [{"RuleID": "test", "File": "test.txt", "StartLine": 1}]),
    ("trivy-image.json", {"Results": [{"Vulnerabilities": [{
        "Severity": "HIGH", "VulnerabilityID": "TEST-2", "PkgName": "demo", "InstalledVersion": "1"
    }]}]}),
])
def test_findings_or_incomplete_scans_block(reports, filename, data):
    (reports / filename).write_text(json.dumps(data), encoding="utf-8")
    assert gate.main(["security_gate.py", str(reports)]) == 1
