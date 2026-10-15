"""Exercise task 15 install, test, upgrade and rollback in an isolated namespace."""

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime

from run_checks import RESULTS, executable, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True)
    args = parser.parse_args()
    namespace = "homework-helm-" + uuid.uuid4().hex[:8]
    helm = [executable("helm", "tools/helm/windows-amd64/helm.exe"), "--kube-context", args.context, "-n", namespace]
    kubectl = ["kubectl", "--context", args.context, "-n", namespace]
    checks = []
    created = False

    def check(name, command):
        result = run("task15-" + name, command)
        checks.append(result)
        if result["exit_code"]:
            raise RuntimeError(name)

    try:
        check("lifecycle-namespace", [*kubectl, "create", "namespace", namespace])
        created = True
        check("lifecycle-install", [*helm, "install", "notes-review", "task-15-helm/notes-chart",
                                    "--set", "service.type=ClusterIP", "--wait", "--timeout", "3m"])
        check("lifecycle-test", [*helm, "test", "notes-review", "--logs", "--timeout", "2m"])
        check("lifecycle-upgrade", [*helm, "upgrade", "notes-review", "task-15-helm/notes-chart",
                                    "--set", "service.type=ClusterIP", "--set", "replicaCount=2",
                                    "--set", "app.message=Updated review release", "--wait", "--timeout", "3m"])
        check("lifecycle-upgraded-content", [*kubectl, "exec", "deploy/notes-review-deploy", "--", "sh", "-ec",
              'test "$(cat /usr/share/nginx/html/index.html | grep -c "Updated review release")" = 1'])
        check("lifecycle-rollback", [*helm, "rollback", "notes-review", "1", "--wait", "--timeout", "3m"])
        check("lifecycle-rollback-test", [*helm, "test", "notes-review", "--logs", "--timeout", "2m"])
        check("lifecycle-restored-content", [*kubectl, "exec", "deploy/notes-review-deploy", "--", "grep",
              "Welcome to the Notes app", "/usr/share/nginx/html/index.html"])
        check("lifecycle-history", [*helm, "history", "notes-review"])
    except RuntimeError as error:
        print(f"Helm lifecycle failed: {error}", file=sys.stderr)
    finally:
        if created:
            checks.append(run("task15-lifecycle-uninstall", [*helm, "uninstall", "notes-review", "--wait", "--timeout", "2m"]))
            checks.append(run("task15-lifecycle-cleanup", [*kubectl, "delete", "namespace", namespace, "--wait=true", "--timeout=120s"]))
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "helm-lifecycle.json").write_text(json.dumps({
            "captured_at": datetime.now(UTC).isoformat(), "context": args.context,
            "checks": checks, "scope": "Local Helm lifecycle; no AWS resources."
        }, indent=2) + "\n", encoding="utf-8")
    return int(any(check["exit_code"] for check in checks))


if __name__ == "__main__":
    sys.exit(main())
