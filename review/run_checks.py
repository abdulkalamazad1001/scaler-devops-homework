"""Run isolated application tests and infrastructure validation without deploying AWS."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("HOMEWORK_RESULTS_DIR", ROOT / "review/results"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(name, command, cwd=ROOT, timeout=900, stdin=None, env=None):
    print(f"Running {name} ...", flush=True)
    started = datetime.now(UTC)
    try:
        result = subprocess.run(command, check=False, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, input=stdin, env=env)
        output, code = result.stdout, result.returncode
    except (OSError, subprocess.TimeoutExpired) as error:
        output, code = str(error), 1
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{name}.txt").write_text(output, encoding="utf-8")
    print(f"{name}: {'PASS' if code == 0 else 'FAIL'}\n{output[-1800:]}", flush=True)
    return {"check": name, "exit_code": code, "started_at": started.isoformat(),
            "duration_seconds": round((datetime.now(UTC) - started).total_seconds(), 2),
            "log": f"{name}.txt", "command": command}


def executable(name, local):
    return shutil.which(name) or str(ROOT / local)


def application_checks():
    projects = [
        ("task16-tests", "task-16-cicd-github-actions", "requirements-dev.txt",
         "python -m flake8 app tests && python -m pytest --cov=app --cov-fail-under=90"),
        ("task17-tests", "task-17-devsecops", "requirements-dev.txt",
         "python -m pytest --cov=app --cov-fail-under=90"),
        ("task20-tests", "task-20-monitoring-gitops/monitoring/app", "requirements.txt",
         "python -m pip install pytest==9.1.1 && python -m pytest -q"),
        ("task21-tests", "task-21-final-devops-project/application/backend", "requirements-dev.txt",
         "python -m pytest -q"),
    ]
    results = []
    for name, folder, requirements, test in projects:
        results.append(run(name, [
            "docker", "run", "--rm", "--mount", f"type=bind,source={ROOT / folder},target=/src,readonly",
            "python:3.12-slim", "sh", "-ec",
            (f"cp -R /src /tmp/project; cd /tmp/project; "
            f"python -m pip install --disable-pip-version-check -q -r {requirements}; "
             f"python -m pip check; {test}")
        ]))
    return results


def infrastructure_checks():
    results = []
    helm = executable("helm", "tools/helm/windows-amd64/helm.exe")
    for task, chart, variants in [
        (15, "task-15-helm/notes-chart", ["values.yaml", "values-prod.yaml"]),
        (21, "task-21-final-devops-project/helm/taskboard", ["values.yaml", "values-dev.yaml", "values-prod.yaml"]),
    ]:
        for values in variants:
            suffix = values.removesuffix(".yaml")
            options = ["-f", f"{chart}/{values}"]
            if task == 21 and values == "values.yaml":
                # Default chart intentionally requires operator-supplied credentials; no real secret is needed to render.
                options += ["--set", "database.existingSecret=review-placeholder"]
            results.append(run(f"task{task}-helm-{suffix}", [helm, "lint", chart, *options]))
            results.append(run(f"task{task}-render-{suffix}", [helm, "template", "review", chart, *options]))
            if results[-1]["exit_code"] == 0:
                results.append(run(f"task{task}-render-types-{suffix}", [
                    sys.executable, str(ROOT / "review/check_rendered.py"), str(RESULTS / f"task{task}-render-{suffix}.txt")
                ]))

    terraform = executable("terraform", "tools/terraform/terraform.exe")
    cache = ROOT / "tools/terraform-provider-cache"
    cache.mkdir(parents=True, exist_ok=True)
    terraform_env = {**os.environ, "TF_PLUGIN_CACHE_DIR": cache.as_posix(), "TF_REGISTRY_CLIENT_TIMEOUT": "90"}
    for task, folder in [
        (18, "task-18-terraform-aws/terraform-s3-demo"),
        (19, "task-19-terraform-cloud-project"),
        (21, "task-21-final-devops-project/terraform"),
    ]:
        results.append(run(f"task{task}-terraform-fmt", [terraform, "fmt", "-check", "-recursive"], ROOT / folder))
        # Isolate downloaded providers and state from the submission and any real deployment.
        with tempfile.TemporaryDirectory(prefix=f"homework-tf{task}-") as temp:
            target = Path(temp) / "config"
            shutil.copytree(ROOT / folder, target, ignore=shutil.ignore_patterns(".terraform", "*.tfstate*"))
            init = run(f"task{task}-terraform-init", [terraform, "init", "-backend=false", "-input=false", "-no-color"], target, env=terraform_env)
            results.append(init)
            if init["exit_code"] == 0:
                results.append(run(f"task{task}-terraform-validate", [terraform, "validate", "-no-color"], target))

    rules = ROOT / "task-20-monitoring-gitops/monitoring/rules"
    for name, args in [("rules", ["check", "rules", "metrics-demo-rules.yaml"]),
                       ("rule-tests", ["test", "rules", "metrics-demo-rules.test.yaml"])]:
        results.append(run(f"task20-{name}", [
            "docker", "run", "--rm", "--mount", f"type=bind,source={rules},target=/rules,readonly",
            "-w", "/rules", "--entrypoint", "promtool", "prom/prometheus:v3.2.1", *args
        ]))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=["apps", "infra", "shell", "all"], default="all", nargs="?")
    args = parser.parse_args()
    results = []
    if args.suite in {"apps", "all"}:
        results += application_checks()
    if args.suite in {"infra", "all"}:
        results += infrastructure_checks()
    if args.suite in {"shell", "all"}:
        results.append(run("shell-tests", [
            "docker", "run", "--rm", "--mount", f"type=bind,source={ROOT},target=/src,readonly",
            "ubuntu:24.04", "bash", "-ec",
            "apt-get update -qq; apt-get install -y -qq procps iproute2 iputils-ping git; bash /src/review/test_shell.sh"
        ]))
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.suite}.json").write_text(json.dumps({
        "captured_at": datetime.now(UTC).isoformat(), "checks": results,
        "scope": "Local isolated tests and validation. No AWS deployment or grading guarantee."
    }, indent=2) + "\n", encoding="utf-8")
    return int(any(result["exit_code"] for result in results))


if __name__ == "__main__":
    sys.exit(main())
