"""Verify the session 13/15 mini-project scenarios in isolated namespaces."""
import argparse
import json
from datetime import UTC, datetime

from check_lab_scenarios import Lab, reason
from run_checks import RESULTS, run


def storage_project(lab):
    base = "task-13-storage-hpa-probes/03-mini-project"
    lab.client()
    lab.apply("application", *(f"{base}/{name}.yaml" for name in ["pvc", "deployment", "service"]))
    lab.rollout("deployment/web-app")
    lab.http("service-before", "http://web-service", "Welcome to nginx")
    pods = json.loads(lab.check("original-pods", "get", "pods", "-l", "app=web-app", "-o", "json"))["items"]
    old_names = {p["metadata"]["name"] for p in pods}
    old = pods[0]["metadata"]["name"]
    lab.check("write-student", "exec", old, "--", "sh", "-ec",
              "printf '%s\\n' 'Student: T. Abdul Kalam Azad, 24BCS10053' > /data/student.txt")
    lab.check("read-before", "exec", old, "--", "cat", "/data/student.txt")
    lab.delete_pod(old)
    found = lab.observe("replacement-created", "pods", "", lambda o: any(
        p["metadata"]["name"] not in old_names and p["metadata"].get("labels", {}).get("app") == "web-app"
        for p in o["items"]))
    new = next(p["metadata"]["name"] for p in found["items"]
               if p["metadata"]["name"] not in old_names and p["metadata"].get("labels", {}).get("app") == "web-app")
    lab.ready(new)
    lab.check("read-after-replacement", "exec", new, "--", "grep", "24BCS10053", "/data/student.txt")
    lab.check("bound-claim", "get", "pvc", "web-data", "-o", "wide")
    lab.http("service-after", "http://web-service", "Welcome to nginx")


def helm_project(lab, context):
    helm = ["helm", "--kube-context", context, "-n", lab.namespace]
    chart = "task-15-helm/notes-chart"

    def check(name, *args):
        result = run("helm-project-" + name, [*helm, *args])
        lab.checks.append(result)
        if result["exit_code"]:
            raise RuntimeError(name)

    try:
        check("install", "install", "notes-project", chart, "--set", "service.type=ClusterIP", "--wait", "--timeout", "3m")
        check("upgrade-production", "upgrade", "notes-project", chart, "-f", chart + "/values-prod.yaml",
              "--set", "service.type=ClusterIP", "--wait", "--timeout", "3m")
        lab.observe("production-replicas", "deployment", "notes-project-deploy", lambda o:
                    o["spec"]["replicas"] == 3 and o["status"].get("readyReplicas") == 3)
        lab.check("production-environment", "exec", "deploy/notes-project-deploy", "--", "sh", "-ec", 'test "$(printenv ENVIRONMENT)" = production && printenv ENVIRONMENT')
        check("broken-upgrade", "upgrade", "notes-project", chart, "--reuse-values",
              "--set", "image.tag=broken-tag-does-not-exist")
        lab.observe("image-failure-observed", "pods", "", lambda o: any(
            reason(p, {"ErrImagePull", "ImagePullBackOff"}) for p in o["items"]), timeout=180)
        lab.check("broken-pods", "get", "pods", "-o", "wide")
        lab.check("diagnose", "describe", "pods")
        lab.check("events", "get", "events", "--sort-by=.lastTimestamp")
        check("rollback", "rollback", "notes-project", "2", "--wait", "--timeout", "3m")
        lab.observe("restored-three-replicas", "deployment", "notes-project-deploy", lambda o:
                    o["spec"]["replicas"] == 3 and o["status"].get("readyReplicas") == 3
                    and o["spec"]["template"]["spec"]["containers"][0]["image"] == "nginx:1.25")
        check("restored-http", "test", "notes-project", "--logs", "--timeout", "2m")
        check("history", "history", "notes-project")
    finally:
        result = run("helm-project-uninstall", [*helm, "uninstall", "notes-project", "--ignore-not-found", "--wait", "--timeout", "2m"])
        lab.checks.append(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True)
    parser.add_argument("--suite", choices=["all", "storage-project", "helm-project"], default="all")
    args = parser.parse_args()
    failed = False
    for name in ["storage-project", "helm-project"]:
        if args.suite not in ["all", name]:
            continue
        lab = Lab(args.context, name)
        error = None
        try:
            lab.check("namespace", "create", "namespace", lab.namespace)
            if name == "storage-project":
                storage_project(lab)
            else:
                helm_project(lab, args.context)
        except Exception as exc:
            error = str(exc)
            print(error, flush=True)
        finally:
            lab.checks.append(run(name + "-cleanup", [*lab.command, "delete", "namespace", lab.namespace,
                                                       "--ignore-not-found", "--wait=true", "--timeout=120s"]))
            failed |= bool(error) or any(x["exit_code"] for x in lab.checks)
            RESULTS.mkdir(parents=True, exist_ok=True)
            (RESULTS / (name + ".json")).write_text(json.dumps({"captured_at": datetime.now(UTC).isoformat(),
                "context": args.context, "namespace": lab.namespace, "error": error, "checks": lab.checks,
                "scope": "Namespaced mini-project scenarios; existing cluster and other applications preserved."}, indent=2) + "\n")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
