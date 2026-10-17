"""Run the unmodified upstream PHP/Apache HPA exercise on an AMD64 lab cluster."""
import argparse
import json
from datetime import UTC, datetime

from check_lab_scenarios import Lab
from run_checks import RESULTS, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True)
    args = parser.parse_args()
    lab = Lab(args.context, "hpa-walkthrough")
    error = None
    try:
        lab.check("namespace", "create", "namespace", lab.namespace)
        base = "task-13-storage-hpa-probes/02-hpa"
        lab.apply("deploy", f"{base}/hpa.yml")
        lab.rollout("deploy/php-apache")
        lab.observe("metrics-ready", "hpa", "php-apache", lambda o: bool(o["status"].get("currentMetrics")), timeout=240)
        lab.apply("generate-load", f"{base}/load-generator.yaml")
        lab.observe("scale-out", "deployment", "php-apache", lambda o: o["status"].get("readyReplicas", 0) > 1, timeout=300)
        lab.check("hpa-loaded", "get", "hpa", "-o", "wide")
        lab.check("pods-loaded", "get", "pods", "-o", "wide")
        lab.check("top", "top", "pods")
        lab.check("describe", "describe", "hpa", "php-apache")
        lab.check("stop-load", "delete", "pod", "load-generator")
        lab.observe("scale-down", "deployment", "php-apache",
                    lambda o: o["spec"]["replicas"] == 1 and o["status"].get("readyReplicas") == 1, timeout=540)
        lab.check("hpa-idle", "get", "hpa", "-o", "wide")
    except Exception as exc:
        error = str(exc)
        print(error, flush=True)
    finally:
        lab.checks.append(run("hpa-walkthrough-cleanup", [*lab.command, "delete", "namespace", lab.namespace,
                                                       "--ignore-not-found", "--wait=true", "--timeout=180s"]))
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "hpa-walkthrough.json").write_text(json.dumps({
            "captured_at": datetime.now(UTC).isoformat(), "context": args.context, "error": error, "checks": lab.checks,
        }, indent=2) + "\n")
    return int(bool(error) or any(c["exit_code"] for c in lab.checks))


if __name__ == "__main__":
    raise SystemExit(main())
