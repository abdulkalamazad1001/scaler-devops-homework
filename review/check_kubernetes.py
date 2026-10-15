"""Validate all task 9-14 manifests and exercise selected labs in an isolated namespace."""

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime

import yaml

from run_checks import RESULTS, ROOT, executable, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True, help="Explicit local lab context; never inferred")
    args = parser.parse_args()
    namespace = "homework-review-" + uuid.uuid4().hex[:8]
    kubectl = ["kubectl", "--context", args.context, "-n", namespace]
    checks = []

    def check(name, command, **kwargs):
        result = run(name, command, **kwargs)
        checks.append(result)
        if result["exit_code"]:
            raise RuntimeError(f"{name} failed; see {result['log']}")
        return (RESULTS / result["log"]).read_text(encoding="utf-8")

    def apply(name, paths):
        objects = []
        for path in paths:
            objects.extend(doc for doc in yaml.safe_load_all((ROOT / path).read_text(encoding="utf-8")) if doc)
        for obj in objects:
            if obj["kind"] == "Service" and obj["spec"].get("type") == "NodePort":
                # Avoid fixed node-port conflicts with existing workloads; test cluster traffic only.
                obj["spec"]["type"] = "ClusterIP"
                for port in obj["spec"]["ports"]:
                    port.pop("nodePort", None)
        check(name, [*kubectl, "apply", "-f", "-"], stdin=yaml.safe_dump_all(objects))

    created = False
    try:
        check("k8s-review-namespace", [*kubectl, "create", "namespace", namespace])
        created = True
        for task in range(9, 15):
            directory = next(ROOT.glob(f"task-{task}-*"))
            files = sorted(directory.rglob("*.yaml"))
            # Client dry-run validates API schemas but does not claim runtime success for broken exercises.
            command = ["kubectl", "--context", args.context, "create", "--dry-run=client", "--validate=strict"]
            for file in files:
                command += ["-f", str(file)]
            check(f"task{task}-k8s-schema", command)

        apply("task9-apply", ["task-9-kubernetes-fundamentals/manifests/nginx-pod.yaml"])
        check("task9-ready", [*kubectl, "wait", "--for=condition=Ready", "pod/nginx-pod", "--timeout=180s"])

        folder = "task-10-k8s-deployments-pod-lifecycle/deployment-strategies/02-blue-green"
        apply("task10-apply", [f"{folder}/{file}.yaml" for file in ["deployment-blue", "deployment-green", "service"]])
        for color in ["blue", "green"]:
            check(f"task10-{color}-ready", [*kubectl, "rollout", "status", f"deployment/app-{color}", "--timeout=180s"])

        apply("task12-config-apply", ["task-12-ingress-configmaps-secrets/01-configmap/app-config.yaml",
                                    "task-12-ingress-configmaps-secrets/01-configmap/config-demo-pod.yaml"])
        check("task12-config-ready", [*kubectl, "wait", "--for=condition=Ready", "pod/config-demo", "--timeout=180s"])
        check("task12-config-values", [*kubectl, "exec", "config-demo", "--", "sh", "-ec",
                                      'test "$APP_LOG_LEVEL" = INFO; grep -q "color=teal" /etc/config/theme.txt'])
        for color in ["blue", "green"]:
            check(f"task10-select-{color}", [*kubectl, "patch", "service", "myapp-service", "--type=merge",
                                            "-p", json.dumps({"spec": {"selector": {"slot": color}}})])
            check(f"task10-traffic-{color}", [*kubectl, "exec", "config-demo", "--", "sh", "-ec",
                  f"for i in 1 2 3 4 5; do wget -qO- http://myapp-service | grep '{color} v' && exit 0; sleep 2; done; exit 1"])

        folder = "task-11-k8s-services-dns/services/01-clusterip"
        apply("task11-apply", [f"{folder}/app-deployment.yaml", f"{folder}/service.yaml"])
        check("task11-ready", [*kubectl, "rollout", "status", "deployment/web-clusterip", "--timeout=180s"])
        check("task11-dns-http", [*kubectl, "exec", "config-demo", "--", "sh", "-ec",
              f"nslookup web-clusterip.{namespace}.svc.cluster.local; "
              "for i in 1 2 3 4 5; do wget -qO- http://web-clusterip:8080 | grep web-clusterip && exit 0; sleep 2; done; exit 1"])

        apply("task12-secret-apply", ["task-12-ingress-configmaps-secrets/02-secret/db-secret.yaml",
                                     "task-12-ingress-configmaps-secrets/02-secret/secret-demo-pod.yaml"])
        check("task12-secret-ready", [*kubectl, "wait", "--for=condition=Ready", "pod/secret-demo", "--timeout=180s"])
        check("task12-secret-values", [*kubectl, "exec", "secret-demo", "--", "sh", "-ec",
              'test -n "$DB_PASSWORD"; test "$DB_PASSWORD" = "$(cat /etc/secrets/DB_PASSWORD)"'])

        apply("task13-apply", ["task-13-storage-hpa-probes/01-kubernetes-volumes/emptydir-pod.yaml",
                               "task-13-storage-hpa-probes/01-kubernetes-volumes/dynamic-pvc.yaml"])
        for pod in ["emptydir-demo", "dynamic-demo"]:
            check(f"task13-{pod}-ready", [*kubectl, "wait", "--for=condition=Ready", f"pod/{pod}", "--timeout=180s"])
        check("task13-shared-volume", [*kubectl, "exec", "emptydir-demo", "-c", "reader", "--",
                                       "grep", "written by writer", "/cache/log.txt"])
        check("task13-pvc-write", [*kubectl, "exec", "dynamic-demo", "--", "sh", "-ec",
                                  'echo review-persistence > /data/review.txt; cat /data/review.txt'])
        check("task13-pod-delete", [*kubectl, "delete", "pod", "dynamic-demo", "--wait=true"])
        apply("task13-recreate", ["task-13-storage-hpa-probes/01-kubernetes-volumes/dynamic-pvc.yaml"])
        check("task13-recreated-ready", [*kubectl, "wait", "--for=condition=Ready", "pod/dynamic-demo", "--timeout=180s"])
        check("task13-pvc-persistence", [*kubectl, "exec", "dynamic-demo", "--", "grep", "review-persistence", "/data/review.txt"])

        apply("task14-fixed-apply", ["task-14-k8s-troubleshooting/02-scenarios/02-imagepullbackoff/fixed.yaml"])
        check("task14-fixed-ready", [*kubectl, "wait", "--for=condition=Ready", "pod/image-demo", "pod/fail-2-imagepull-pod", "--timeout=180s"])

        helm = executable("helm", "tools/helm/windows-amd64/helm.exe")
        check("task15-install", [helm, "--kube-context", args.context, "install", "review-notes",
                                "task-15-helm/notes-chart", "-n", namespace, "--set", "service.type=ClusterIP", "--wait", "--timeout", "3m"])
        check("task15-http", [*kubectl, "exec", "config-demo", "--", "sh", "-ec",
                              "wget -qO- http://review-notes-svc | grep 'Welcome to the Notes app'"])
        check("k8s-final-pods", [*kubectl, "get", "pods", "-o", "wide"])
    except RuntimeError as error:
        print(error, file=sys.stderr)
    finally:
        if created:
            checks.append(run("k8s-review-pods-cleanup", [*kubectl, "delete", "pods", "--all", "--grace-period=1", "--wait=true", "--timeout=90s"]))
            checks.append(run("k8s-review-cleanup", [*kubectl, "delete", "namespace", namespace, "--wait=true", "--timeout=180s"]))
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "kubernetes.json").write_text(json.dumps({
            "captured_at": datetime.now(UTC).isoformat(), "context": args.context, "namespace": namespace,
            "checks": checks,
            "scope": "All task 9-14 manifest schemas plus selected local lab exercises; not all scenarios. NodePort changed to ClusterIP only in the test input."
        }, indent=2) + "\n", encoding="utf-8")
    return int(any(check["exit_code"] for check in checks))


if __name__ == "__main__":
    sys.exit(main())
