"""Exercise homework failure/recovery scenarios in disposable local namespaces."""

import argparse
import json
import subprocess
import time
import uuid
from datetime import UTC, datetime

import yaml
from run_checks import RESULTS, ROOT, run


class Lab:
    def __init__(self, context, suite):
        self.namespace = f"homework-{suite}-{uuid.uuid4().hex[:8]}"
        self.command = ["kubectl", "--context", context, "-n", self.namespace]
        self.suite = suite
        self.checks = []

    def check(self, name, *args, **kwargs):
        result = run(f"{self.suite}-{name.replace('/', '-')}", [*self.command, *args], **kwargs)
        self.checks.append(result)
        if result["exit_code"]:
            raise RuntimeError(f"{name}: see {result['log']}")
        return (RESULTS / result["log"]).read_text(encoding="utf-8")

    def apply(self, name, *paths):
        objects = []
        for path in paths:
            for obj in yaml.safe_load_all((ROOT / path).read_text(encoding="utf-8")):
                if not obj or obj["kind"] == "Namespace":
                    continue
                obj["metadata"]["namespace"] = self.namespace
                if obj["kind"] == "Service":
                    for port in obj["spec"].get("ports", []):
                        # Let Kubernetes assign an unused NodePort in the shared local cluster.
                        port.pop("nodePort", None)
                objects.append(obj)
        self.check(name, "apply", "-f", "-", stdin=yaml.safe_dump_all(objects))

    def observe(self, name, kind, resource, predicate, timeout=180):
        command = [*self.command, "get", kind, *([resource] if resource else []), "-o", "json"]
        start = time.monotonic()
        output = "No response"
        while time.monotonic() - start < timeout:
            result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8", timeout=30)
            output = result.stderr
            if result.returncode == 0:
                obj = json.loads(result.stdout)
                output = json.dumps(obj.get("status", obj.get("subsets", obj.get("items", {}))), indent=2)
                if predicate(obj):
                    self.record(name, command, output, 0, start)
                    return obj
            time.sleep(2)
        self.record(name, command, output, 1, start)
        raise RuntimeError(f"{name}: expected condition not observed")

    def record(self, name, command, output, code, start):
        RESULTS.mkdir(parents=True, exist_ok=True)
        log = f"{self.suite}-{name}.txt"
        (RESULTS / log).write_text(output + "\n", encoding="utf-8")
        self.checks.append({"check": f"{self.suite}-{name}", "exit_code": code,
                            "command": command, "duration_seconds": round(time.monotonic() - start, 2), "log": log})
        print(f"{self.suite}-{name}: {'PASS' if code == 0 else 'FAIL'}", flush=True)

    def ready(self, pod):
        self.check(f"{pod}-ready", "wait", "--for=condition=Ready", f"pod/{pod}", "--timeout=240s")

    def rollout(self, deployment):
        self.check(f"{deployment}-rollout-{len(self.checks)}", "rollout", "status", deployment, "--timeout=240s")

    def delete_pod(self, pod):
        self.check(f"{pod}-delete", "delete", "pod", pod, "--wait=true", "--timeout=90s")

    def client(self):
        self.check("client-create", "run", "lab-client", "--image=busybox:1.36", "--restart=Never", "--", "sleep", "3600")
        self.ready("lab-client")

    def http(self, name, url, pattern):
        self.check(name, "exec", "lab-client", "--", "sh", "-ec",
                   f"for i in 1 2 3 4 5; do wget -T 5 -qO- {url} | grep '{pattern}' && exit 0; sleep 2; done; exit 1")


def statuses(obj):
    return obj.get("status", {}).get("containerStatuses", [])


def reason(obj, expected):
    return any(state.get("reason") in expected for item in statuses(obj)
               for states in [item.get("state", {}), item.get("lastState", {})] for state in states.values())


def restarted(obj):
    return any(item.get("restartCount", 0) > 0 for item in statuses(obj))


def troubleshoot(lab):
    base = "task-14-k8s-troubleshooting/02-scenarios"
    lab.client()
    cases = [
        ("01-crashloopbackoff", "fail-1-crashloop-pod", lambda o: reason(o, {"CrashLoopBackOff"})),
        ("02-imagepullbackoff", "image-demo", lambda o: reason(o, {"ErrImagePull", "ImagePullBackOff"})),
        ("03-pending", "fail-3-pending-pod", lambda o: any(
            c.get("reason") == "Unschedulable" for c in o.get("status", {}).get("conditions", []))),
        ("04-containercreating", "configvol-demo", lambda o: reason(o, {"ContainerCreating"})),
    ]
    for folder, pod, predicate in cases:
        lab.apply(f"{folder}-broken", f"{base}/{folder}/broken.yaml")
        if folder == "03-pending":
            lab.apply("pending-selector-broken", f"{base}/{folder}/broken-nodeselector.yaml")
            lab.observe("pending-selector-observed", "pod", "pending-demo", predicate)
            lab.delete_pod("pending-demo")
        lab.observe(f"{folder}-failure-observed", "pod", pod, predicate)
        if folder == "04-containercreating":
            # ContainerCreating alone is normal at startup; require the actual missing-volume event.
            lab.observe("missing-configmap-event", "events", "", lambda o: any(
                e.get("reason") == "FailedMount" and "app-settings" in e.get("message", "")
                for e in o.get("items", [])))
        lab.delete_pod(pod)
        if folder == "02-imagepullbackoff":
            lab.observe("invalid-repository-observed", "pod", "fail-2-imagepull-pod", predicate)
            lab.delete_pod("fail-2-imagepull-pod")
        lab.apply(f"{folder}-fixed", f"{base}/{folder}/fixed.yaml")
        lab.ready(pod)
        if folder == "03-pending":
            lab.ready("pending-demo")
        if folder == "02-imagepullbackoff":
            lab.ready("fail-2-imagepull-pod")

    folder = f"{base}/05-service-connectivity"
    lab.apply("service-broken", f"{folder}/deployment.yaml", f"{folder}/broken-service.yaml")
    lab.rollout("deployment/web")
    lab.observe("service-no-endpoints", "endpoints", "web-service", lambda o: not o.get("subsets"))
    lab.apply("service-fixed", f"{folder}/fixed-service.yaml")
    lab.http("service-http-restored", "http://web-service", "Welcome to nginx")

    folder = f"{base}/07-pod-networking"
    lab.apply("loopback-broken", f"{folder}/broken.yaml")
    lab.rollout("deployment/inventory")
    lab.check("loopback-unreachable", "exec", "lab-client", "--", "sh", "-ec",
              "if wget -T 3 -qO- http://inventory; then exit 1; fi")
    lab.apply("loopback-fixed", f"{folder}/fixed.yaml")
    lab.rollout("deployment/inventory")
    lab.http("pod-network-restored", "http://inventory", "Directory listing")

    folder = f"{base}/08-configuration"
    for name, pod, expected in [("secret-key", "config-app", {"CreateContainerConfigError"}),
                                ("oomkilled", "fail-5-oomkilled-pod", {"OOMKilled"})]:
        lab.apply(f"{name}-broken", f"{folder}/broken-{name}.yaml")
        lab.observe(f"{name}-failure-observed", "pod", pod, lambda o, expected=expected: reason(o, expected))
        lab.delete_pod(pod)
        lab.apply(f"{name}-fixed", f"{folder}/fixed-{name}.yaml")
        if name == "oomkilled":
            lab.observe("bounded-memory-completed", "pod", pod, lambda o: o["status"].get("phase") == "Succeeded")
            lab.check("bounded-memory-log", "logs", pod)
        else:
            lab.ready(pod)
            lab.check("secret-key-present", "exec", pod, "--", "sh", "-ec", 'test -n "$DB_PASSWORD"')


def deployments(lab):
    base = "task-10-k8s-deployments-pod-lifecycle"
    lab.client()
    for directory, name, pattern in [("01-rolling-update", "app-rolling", "app-rolling"),
                                      ("04-recreate", "app-recreate", "recreate")]:
        folder = f"{base}/deployment-strategies/{directory}"
        for version in ["v1", "v2"]:
            lab.apply(f"{name}-{version}", f"{folder}/deployment-{version}.yaml", f"{folder}/service.yaml")
            lab.rollout(f"deployment/{name}")
            lab.http(f"{name}-{version}-traffic", f"http://{name}-service", f"{pattern} {version}")
        lab.check(f"{name}-undo", "rollout", "undo", f"deployment/{name}")
        lab.rollout(f"deployment/{name}")
        lab.http(f"{name}-rollback-traffic", f"http://{name}-service", f"{pattern} v1")
        service = json.loads(lab.check(f"{name}-service", "get", "service", f"{name}-service", "-o", "json"))
        node = json.loads(lab.check(f"{name}-node", "get", "nodes", "-o", "json"))["items"][0]
        address = next(a["address"] for a in node["status"]["addresses"] if a["type"] == "InternalIP")
        lab.http(f"{name}-nodeport-traffic", f"http://{address}:{service['spec']['ports'][0]['nodePort']}", f"{pattern} v1")
        lab.check(f"{name}-remove", "delete", "deployment", name, "--wait=true")

    folder = f"{base}/deployment-strategies/03-canary"
    lab.apply("canary-create", *(f"{folder}/{file}.yaml" for file in ["deployment-stable", "deployment-canary", "service"]))
    for name in ["app-stable", "app-canary"]:
        lab.rollout(f"deployment/{name}")
    lab.observe("canary-ten-ready-endpoints", "endpoints", "myapp-canary-service", lambda o:
                sum(len(subset.get("addresses", [])) for subset in o.get("subsets", [])) == 10)
    lab.check("canary-both-versions", "exec", "lab-client", "--", "sh", "-ec",
              "i=0; : > /tmp/responses; while [ $i -lt 120 ]; do "
              "wget -T 5 -qO- http://myapp-canary-service >> /tmp/responses; "
              "if grep -q 'stable v1' /tmp/responses && grep -q 'canary v2' /tmp/responses; "
              "then cat /tmp/responses; exit 0; fi; i=$((i+1)); sleep 1; done; cat /tmp/responses; exit 1")
    lab.check("canary-remove", "delete", "deployment", "app-stable", "app-canary", "--wait=true")

    folder = f"{base}/pod-lifecycle"
    lab.apply("lifecycle-create", *(p.relative_to(ROOT).as_posix() for p in sorted((ROOT / folder).glob("*.yaml"))))
    for pod, phase in [("lifecycle-succeeded", "Succeeded"), ("lifecycle-failed", "Failed"),
                       ("rp-onfailure-exit0", "Succeeded"), ("rp-never-exit1", "Failed")]:
        lab.observe(f"{pod}-phase", "pod", pod, lambda o, phase=phase: o["status"].get("phase") == phase)
    lab.observe("lifecycle-unschedulable", "pod", "lifecycle-pending", lambda o: any(
        c.get("reason") == "Unschedulable" for c in o["status"].get("conditions", [])))
    for pod, expected in [("lifecycle-crashloop", {"CrashLoopBackOff"}),
                          ("lifecycle-image-error", {"ImagePullBackOff", "ErrImagePull"})]:
        lab.observe(f"{pod}-reason", "pod", pod, lambda o, expected=expected: reason(o, expected))
    for pod in ["rp-always-exit0", "rp-onfailure-exit1", "lifecycle-liveness"]:
        lab.observe(f"{pod}-restarted", "pod", pod, restarted)
    for pod in ["lifecycle-running", "lifecycle-init", "lifecycle-hooks"]:
        lab.ready(pod)
    lab.check("init-content", "exec", "lifecycle-init", "--", "grep", "page written by init", "/usr/share/nginx/html/index.html")
    lab.check("poststart-hook", "exec", "lifecycle-hooks", "--", "grep", "postStart ran", "/tmp/poststart.txt")

    folder = "task-11-k8s-services-dns/services"
    lab.apply("headless-create", f"{folder}/05-headless/service.yaml", f"{folder}/05-headless/statefulset.yaml",
              f"{folder}/04-externalname/service.yaml")
    lab.rollout("statefulset/web")
    for index in range(3):
        lab.http(f"headless-pod-{index}", f"http://web-{index}.web-headless.{lab.namespace}.svc.cluster.local", f"web-{index}")
    lab.check("externalname-dns", "exec", "lab-client", "--", "sh", "-ec",
              f"nslookup external-api.{lab.namespace}.svc.cluster.local | grep 'canonical name = example.com'")


def dns(lab):
    folder = "task-14-k8s-troubleshooting/02-scenarios/06-dns"
    lab.apply("dns-server", f"{folder}/server.yaml")
    lab.rollout("deployment/orders-api")
    client_namespace = lab.namespace + "-client"
    lab.check("dns-client-namespace", "create", "namespace", client_namespace)
    server_namespace = lab.namespace
    server_command = lab.command
    try:
        lab.namespace = client_namespace
        lab.command = [*server_command[:-1], client_namespace]
        lab.apply("dns-broken-client", f"{folder}/broken-client.yaml")
        lab.ready("dns-client")
        lab.check("dns-short-name-fails", "exec", "dns-client", "--", "sh", "-ec",
                  "if curl -fsS --connect-timeout 3 http://orders-api; then exit 1; fi")
        lab.delete_pod("dns-client")
        obj = yaml.safe_load((ROOT / folder / "fixed-client.yaml").read_text(encoding="utf-8"))
        obj["spec"]["containers"][0]["args"][0] = obj["spec"]["containers"][0]["args"][0].replace(
            "orders-api.production.svc.cluster.local", f"orders-api.{server_namespace}.svc.cluster.local")
        lab.check("dns-fixed-client", "apply", "-f", "-", stdin=yaml.safe_dump(obj))
        lab.ready("dns-client")
        lab.check("dns-qualified-name-works", "exec", "dns-client", "--", "sh", "-ec",
                  f"curl -fsS --connect-timeout 5 http://orders-api.{server_namespace}.svc.cluster.local | grep 'Welcome to nginx'")
    finally:
        lab.namespace = server_namespace
        lab.command = server_command
        lab.check("dns-client-cleanup", "delete", "namespace", client_namespace, "--wait=true", "--timeout=180s")


def probes(lab):
    folder = "task-13-storage-hpa-probes/03-mini-project"
    lab.apply("mini-project", *(f"{folder}/{file}.yaml" for file in ["pvc", "deployment", "service", "hpa"]))
    lab.rollout("deployment/web-app")
    pods = json.loads(lab.check("initial-pods", "get", "pods", "-l", "app=web-app", "-o", "json"))["items"]
    pod = pods[0]["metadata"]["name"]
    before = statuses(pods[0])[0]["restartCount"]
    lab.check("break-probe", "exec", pod, "--", "sh", "-ec", "mv /usr/share/nginx/html/index.html /tmp/index.html")
    lab.observe("readiness-failed", "pod", pod, lambda o: any(not s.get("ready") for s in statuses(o)), timeout=60)
    lab.observe("liveness-restarted", "pod", pod, lambda o: any(s["restartCount"] > before for s in statuses(o)), timeout=120)
    lab.ready(pod)
    lab.observe("hpa-metrics-ready", "hpa", "web-app-hpa", lambda o: bool(o["status"].get("currentMetrics")), timeout=180)
    for item in pods:
        name = item["metadata"]["name"]
        lab.check(f"load-{name}", "exec", name, "--", "sh", "-ec",
                  "timeout 150 sh -c 'while :; do :; done' >/dev/null 2>&1 </dev/null &")
    lab.observe("hpa-scale-out", "deployment", "web-app", lambda o: o["status"].get("readyReplicas", 0) > 2, timeout=180)
    lab.check("hpa-final", "get", "hpa", "web-app-hpa", "-o", "json")
    lab.check("cpu-memory", "top", "pods")
    lab.check("hpa-description", "describe", "hpa", "web-app-hpa")
    # The bounded CPU workers stop after 150 seconds. Keep the real stabilization window.
    lab.observe("hpa-scale-down", "deployment", "web-app",
                lambda o: o["spec"]["replicas"] == 2 and o["status"].get("readyReplicas") == 2, timeout=540)
    lab.check("hpa-after-load", "get", "hpa", "web-app-hpa", "-o", "json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True)
    parser.add_argument("--suite", choices=["all", "troubleshooting", "deployments", "dns", "probes"], default="all")
    args = parser.parse_args()
    failed = False
    for name, exercise in [("troubleshooting", troubleshoot), ("deployments", deployments), ("dns", dns), ("probes", probes)]:
        if args.suite not in {"all", name}:
            continue
        lab = Lab(args.context, name)
        created = False
        error = None
        try:
            lab.check("namespace", "create", "namespace", lab.namespace)
            created = True
            exercise(lab)
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
            error = str(exc)
            failed = True
            print(error, flush=True)
        finally:
            if created:
                result = run(f"{name}-cleanup", [*lab.command, "delete", "namespace", lab.namespace, "--wait=true", "--timeout=180s"])
                lab.checks.append(result)
                failed |= result["exit_code"] != 0
            RESULTS.mkdir(parents=True, exist_ok=True)
            (RESULTS / f"{name}.json").write_text(json.dumps({
                "captured_at": datetime.now(UTC).isoformat(), "context": args.context,
                "namespace": lab.namespace, "error": error, "checks": lab.checks,
                "scope": "Disposable local lab. Namespaces isolated; NodePort values dynamically assigned. No cloud deployment."
            }, indent=2) + "\n", encoding="utf-8")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
