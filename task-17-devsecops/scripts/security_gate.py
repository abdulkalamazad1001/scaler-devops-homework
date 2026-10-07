#!/usr/bin/env python3
"""Security gate for the DevSecOps pipeline.

Reads the JSON reports written by the scanner jobs and decides whether the
build may be pushed and deployed. The scanners themselves run in "report"
mode (they never fail their own job), so every finding from every tool is
visible in one run, and this script is the single place that says pass/fail.

Blocking rules
  bandit     any issue with severity HIGH and confidence MEDIUM or HIGH
  pip-audit  any known vulnerability in a runtime dependency
  gitleaks   any finding at all
  trivy      any HIGH or CRITICAL vulnerability (fixed-only, see workflow)

A missing or unreadable report also blocks: the gate fails closed.

Usage: python scripts/security_gate.py <reports-dir>
"""

import json
import os
import sys
from pathlib import Path

BLOCKING_TRIVY = {"HIGH", "CRITICAL"}
BLOCKING_BANDIT_CONFIDENCE = {"MEDIUM", "HIGH"}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def check_bandit(report):
    findings = []
    for r in report.get("results", []):
        if r["issue_severity"] == "HIGH" and r["issue_confidence"] in BLOCKING_BANDIT_CONFIDENCE:
            findings.append(f"{r['test_id']} {r['filename']}:{r['line_number']} {r['issue_text']}")
    return findings


def check_pip_audit(report):
    findings = []
    seen = set()
    for dep in report.get("dependencies", []):
        for v in dep.get("vulns", []):
            key = (dep["name"], v["id"])
            if key in seen:
                continue
            seen.add(key)
            fix = ", ".join(v.get("fix_versions", [])) or "no fix"
            findings.append(f"{dep['name']} {dep['version']} {v['id']} (fix: {fix})")
    return findings


def check_gitleaks(report):
    # gitleaks writes a JSON list, empty when nothing was found.
    return [f"{f['RuleID']} {f['File']}:{f['StartLine']} commit {f.get('Commit', '')[:7]}" for f in report or []]


def check_trivy(report):
    findings = []
    for result in report.get("Results", []) or []:
        for v in result.get("Vulnerabilities", []) or []:
            if v["Severity"] in BLOCKING_TRIVY:
                fixed = v.get("FixedVersion") or "no fix"
                findings.append(
                    f"{v['Severity']} {v['VulnerabilityID']} {v['PkgName']} "
                    f"{v['InstalledVersion']} -> {fixed}"
                )
    return findings


CHECKS = [
    ("SAST (bandit)", "bandit.json", check_bandit),
    ("SCA (pip-audit)", "pip-audit.json", check_pip_audit),
    ("Secrets (gitleaks)", "gitleaks.json", check_gitleaks),
    ("Image (trivy)", "trivy-image.json", check_trivy),
]


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    reports = Path(argv[1])

    rows = []
    details = []
    blocked = False
    for name, filename, check in CHECKS:
        path = reports / filename
        try:
            findings = check(load(path))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            rows.append((name, "-", f"FAIL (cannot read {filename}: {exc.__class__.__name__})"))
            blocked = True
            continue
        if findings:
            blocked = True
            rows.append((name, str(len(findings)), "FAIL"))
            details.append((name, findings))
        else:
            rows.append((name, "0", "PASS"))

    width = max(len(r[0]) for r in rows)
    lines = [f"{'Check':<{width}}  {'Blocking':>8}  Result", f"{'-' * width}  {'-' * 8}  ------"]
    lines += [f"{n:<{width}}  {c:>8}  {r}" for n, c, r in rows]
    print("\n".join(lines))

    for name, findings in details:
        print(f"\n{name}:")
        for f in findings:
            print(f"  - {f}")

    verdict = "BLOCKED: fix the findings above before this image can be pushed." if blocked \
        else "PASSED: no blocking findings, image may be pushed."
    print(f"\nSecurity gate {verdict}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("## Security gate\n\n| Check | Blocking findings | Result |\n|---|---|---|\n")
            for n, c, r in rows:
                fh.write(f"| {n} | {c} | {r} |\n")
            fh.write(f"\n**{verdict}**\n")

    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
