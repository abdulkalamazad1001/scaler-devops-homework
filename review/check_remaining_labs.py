"""Replay the remaining Kubernetes homework exercises on a disposable Minikube cluster."""

import argparse
import base64
import json
import subprocess
import sys
import time
from datetime import UTC, datetime

import yaml

from check_lab_scenarios import Lab, reason
from run_checks import RESULTS, ROOT, run


def ingress(lab):
    base = "task-12-ingress-configmaps-secrets"
    lab.client()
    lab.apply("apps", f"{base}/03-ingress/apps.yaml")
    lab.rollout("deploy/web")
    lab.rollout("deploy/api")
    lab.apply("routes", f"{base}/03-ingress/ingress.yaml")
    gateway = "http://ingress-nginx-controller.ingress-nginx.svc"

    def route(name, host, path, pattern):
        lab.check(name, "exec", "lab-client", "--", "sh", "-ec",
                  f"for i in $(seq 1 30); do wget -T 3 -qO- --header='Host: {host}' '{gateway}{path}' | grep '{pattern}' && exit 0; sleep 2; done; exit 1")

    route("host-web", "demo.local", "/", "WEB app")
    route("path-api", "demo.local", "/api", "API app")
    route("host-api", "api.demo.local", "/", "API app")
    for filename, code in [("wrong-backend-service", "503"), ("wrong-ingressclass", "404")]:
        lab.apply(filename, f"{base}/troubleshooting/manifests/{filename}.yaml")
        lab.check(filename + "-observed", "exec", "lab-client", "--", "sh", "-ec",
                  f"for i in $(seq 1 30); do wget -T 3 -S -O /dev/null --header='Host: demo.local' '{gateway}/api' 2>&1 | grep 'HTTP/1.1 {code}' && exit 0; sleep 2; done; exit 1")
        lab.apply(filename + "-repair", f"{base}/03-ingress/ingress.yaml")
        route(filename + "-recovered", "demo.local", "/api", "API app")
    lab.apply("configmap", f"{base}/01-configmap/app-config.yaml",
              f"{base}/troubleshooting/manifests/missing-configmap-pod.yaml")
    lab.observe("missing-config-observed", "pod", "typo-demo", lambda o: reason(o, {"CreateContainerConfigError"}))
    lab.delete_pod("typo-demo")
    obj = yaml.safe_load((ROOT / base / "troubleshooting/manifests/missing-configmap-pod.yaml").read_text())
    obj["metadata"]["namespace"] = lab.namespace
    obj["spec"]["containers"][0]["envFrom"][0]["configMapRef"]["name"] = "app-config"
    lab.check("configmap-repaired", "apply", "-f", "-", stdin=yaml.safe_dump(obj))
    lab.ready("typo-demo")
    # Compare the byte shape, never print a secret value. These are published dummy fixtures.
    for filename, expected in [("troubleshooting/manifests/newline-secret.yaml", True), ("02-secret/db-secret.yaml", False)]:
        lab.apply("secret-fixture", f"{base}/{filename}")
        result = subprocess.check_output([*lab.command, "get", "secret", "db-secret", "-o", "json"], text=True)
        actual = base64.b64decode(json.loads(result)["data"]["DB_PASSWORD"]).endswith(b"\n")
        lab.record("secret-newline-" + str(expected).lower(), ["compare", "decoded-secret-trailing-newline"],
                   f"Trailing newline present: {actual}; expected: {expected}", int(actual != expected), time.monotonic())
        if actual != expected:
            raise RuntimeError("secret byte check failed")


def mini(lab):
    base = "task-14-k8s-troubleshooting/03-mini-project"
    lab.client()
    lab.apply("broken", f"{base}/deployment.yaml", f"{base}/broken-service.yaml", f"{base}/broken-pod.yaml")
    lab.rollout("deploy/troubleshooting-app")
    lab.observe("image-failure", "pod", "project-broken-pod", lambda o: reason(o, {"ImagePullBackOff", "ErrImagePull"}))
    lab.observe("empty-endpoints", "endpoints", "troubleshooting-service", lambda o: not o.get("subsets"))
    for name, args in [("get-wide", ["get", "pods", "-o", "wide"]),
                       ("describe", ["describe", "pod", "project-broken-pod"]),
                       ("events", ["events"]), ("explain", ["explain", "pod.spec.containers"]),
                       ("logs", ["logs", "deploy/troubleshooting-app"]),
                       ("exec", ["exec", "deploy/troubleshooting-app", "--", "nginx", "-v"])]:
        lab.check(name, *args)
    lab.delete_pod("project-broken-pod")
    lab.apply("fixed", f"{base}/service.yaml", f"{base}/fixed-pod.yaml")
    lab.ready("project-broken-pod")
    lab.http("service-recovered", "http://troubleshooting-service", "Welcome to nginx")
    lab.check("ready-endpoints", "get", "endpoints", "troubleshooting-service", "-o", "wide")


def storage(lab):
    base = "task-13-storage-hpa-probes/01-kubernetes-volumes"
    lab.apply("hostpath", f"{base}/hostpath-pod.yaml")
    lab.ready("hostpath-demo")
    lab.check("hostpath-write", "exec", "hostpath-demo", "--", "sh", "-ec", "echo retained-homework-data > /data/proof.txt")
    lab.delete_pod("hostpath-demo")
    lab.apply("hostpath-recreate", f"{base}/hostpath-pod.yaml")
    lab.ready("hostpath-demo")
    lab.check("hostpath-persisted", "exec", "hostpath-demo", "--", "grep", "retained-homework-data", "/data/proof.txt")
    objects = list(yaml.safe_load_all((ROOT / base / "static-pv.yaml").read_text()))
    pv, pvc = objects
    name = lab.namespace + "-pv"
    pv["metadata"]["name"] = name
    pv["spec"]["hostPath"]["path"] = "/data/" + name
    pvc["metadata"]["namespace"] = lab.namespace
    pvc["spec"]["volumeName"] = name
    try:
        lab.check("static-volume", "apply", "-f", "-", stdin=yaml.safe_dump_all(objects))
        lab.apply("static-consumer", f"{base}/static-pvc-pod.yaml")
        lab.ready("pvc-demo")
        lab.check("static-write", "exec", "pvc-demo", "--", "sh", "-ec", "echo static-retained-data > /data/proof.txt")
        lab.delete_pod("pvc-demo")
        lab.check("release-claim", "delete", "pvc", "manual-pvc")
        lab.observe("retained-volume", "pv", name, lambda o: o["status"]["phase"] == "Released")
        lab.check("clear-old-claim", "patch", "pv", name, "--type=json", "-p", '[{"op":"remove","path":"/spec/claimRef"}]')
        lab.check("rebind-claim", "apply", "-f", "-", stdin=yaml.safe_dump(pvc))
        lab.apply("static-recreate", f"{base}/static-pvc-pod.yaml")
        lab.ready("pvc-demo")
        lab.check("static-persisted", "exec", "pvc-demo", "--", "grep", "static-retained-data", "/data/proof.txt")
    finally:
        lab.check("static-pod-cleanup", "delete", "pod", "pvc-demo", "--ignore-not-found")
        lab.check("static-claim-cleanup", "delete", "pvc", "manual-pvc", "--ignore-not-found")
        lab.check("static-pv-cleanup", "delete", "pv", name, "--ignore-not-found")


def loadbalancer(lab):
    base = "task-11-k8s-services-dns/services/03-loadbalancer"
    lab.apply("service", f"{base}/app-deployment.yaml", f"{base}/service.yaml")
    lab.rollout("deploy/web-lb")
    obj = lab.observe("external-address", "service", "web-lb",
                      lambda o: bool(o.get("status", {}).get("loadBalancer", {}).get("ingress")))
    address = obj["status"]["loadBalancer"]["ingress"][0]["ip"]
    result = run("loadbalancer-external-http", ["docker", "run", "--rm", "--network", "homework-review",
                 "alpine:3.22", "sh", "-ec",
                 f"for i in $(seq 1 20); do wget -T 3 -qO- http://{address} && exit 0; sleep 2; done; exit 1"])
    lab.checks.append(result)
    if result["exit_code"]:
        raise RuntimeError("external LoadBalancer HTTP failed")


def basics(lab):
    lab.client()
    lab.apply("bootcamp", "task-9-kubernetes-fundamentals/manifests/kubernetes-bootcamp.yaml")
    lab.rollout("deploy/kubernetes-bootcamp")
    lab.http("bootcamp-http", "http://kubernetes-bootcamp:8080", "Hello")
    lab.check("explore", "get", "deploy,rs,pods,svc", "-o", "wide")
    lab.check("logs", "logs", "deploy/kubernetes-bootcamp")
    lab.check("exec", "exec", "deploy/kubernetes-bootcamp", "--", "env")
    lab.check("scale", "scale", "deployment", "kubernetes-bootcamp", "--replicas=4")
    lab.rollout("deploy/kubernetes-bootcamp")
    lab.check("scale-down", "scale", "deployment", "kubernetes-bootcamp", "--replicas=2")
    lab.rollout("deploy/kubernetes-bootcamp")
    lab.check("update-v2", "set", "image", "deployment/kubernetes-bootcamp", "kubernetes-bootcamp=jocatalin/kubernetes-bootcamp:v2")
    lab.rollout("deploy/kubernetes-bootcamp")
    lab.http("updated-http", "http://kubernetes-bootcamp:8080", "v=2")
    lab.check("broken-update", "set", "image", "deployment/kubernetes-bootcamp", "kubernetes-bootcamp=jocatalin/kubernetes-bootcamp:v10")
    lab.observe("broken-image-observed", "pods", "", lambda o: any(reason(p, {"ErrImagePull", "ImagePullBackOff"}) for p in o['items']))
    lab.check("rollback", "rollout", "undo", "deployment/kubernetes-bootcamp")
    lab.rollout("deploy/kubernetes-bootcamp")
    lab.http("rollback-http", "http://kubernetes-bootcamp:8080", "v=2")
    lab.check("history", "rollout", "history", "deployment/kubernetes-bootcamp")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True)
    parser.add_argument("--suite", choices=["ingress", "mini", "storage", "loadbalancer", "basics"], required=True)
    args = parser.parse_args()
    lab = Lab(args.context, args.suite)
    error = None
    try:
        lab.check("namespace", "create", "namespace", lab.namespace)
        {"ingress": ingress, "mini": mini, "storage": storage, "loadbalancer": loadbalancer, "basics": basics}[args.suite](lab)
    except Exception as exc:
        error = str(exc)
        print(error, file=sys.stderr)
    finally:
        lab.checks.append(run(args.suite + "-cleanup", [*lab.command, "delete", "namespace", lab.namespace,
                                                     "--ignore-not-found", "--wait=true", "--timeout=180s"]))
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / f"{args.suite}.json").write_text(json.dumps({
            "captured_at": datetime.now(UTC).isoformat(), "context": args.context,
            "error": error, "checks": lab.checks,
        }, indent=2) + "\n")
    return int(bool(error) or any(c["exit_code"] for c in lab.checks))


if __name__ == "__main__":
    sys.exit(main())
