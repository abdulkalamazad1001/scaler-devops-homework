"""Verify task 7 network isolation and named-volume persistence in disposable containers."""

import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime

from run_checks import RESULTS, run


def main():
    prefix = "homework-review-" + uuid.uuid4().hex[:8]
    networks = [prefix + suffix for suffix in ["-front", "-back", "-database"]]
    containers = [prefix + suffix for suffix in ["-frontend", "-backend", "-db"]]
    volume = prefix + "-data"
    checks = []
    created_networks, created_containers = [], []
    created_volume = False

    def check(name, args):
        result = run("task7-" + name, ["docker", *args])
        checks.append(result)
        if result["exit_code"]:
            raise RuntimeError(name)

    try:
        check("pull", ["pull", "alpine:3.22"])
        for index, network in enumerate(networks):
            check(f"network-{index}", ["network", "create", network])
            created_networks.append(network)
        for index, container in enumerate(containers):
            network = networks[0] if index < 2 else networks[1]
            check(f"container-{index}", ["run", "-d", "--name", container, "--network", network,
                                         "alpine:3.22", "sleep", "300"])
            created_containers.append(container)
        check("connect-backend", ["network", "connect", networks[1], containers[1]])
        check("connect-database", ["network", "connect", networks[2], containers[2]])
        check("front-to-back", ["exec", containers[0], "ping", "-c", "1", containers[1]])
        check("back-to-db", ["exec", containers[1], "ping", "-c", "1", containers[2]])
        info = json.loads(subprocess.check_output(["docker", "inspect", containers[2]], text=True))[0]
        database_ip = info["NetworkSettings"]["Networks"][networks[1]]["IPAddress"]
        check("front-isolated-from-db", ["exec", containers[0], "sh", "-ec",
              f"if ping -c 1 -W 2 {database_ip}; then exit 1; fi; echo PASS: separate networks block traffic"])
        check("volume-create", ["volume", "create", volume])
        created_volume = True
        check("volume-write", ["run", "--rm", "-v", f"{volume}:/data", "alpine:3.22", "sh", "-ec",
                               "echo preserved-after-container-removal > /data/proof.txt"])
        check("volume-read-new-container", ["run", "--rm", "-v", f"{volume}:/data:ro", "alpine:3.22",
                                            "grep", "preserved-after-container-removal", "/data/proof.txt"])
    except RuntimeError as error:
        print(f"Task 7 check failed: {error}", file=sys.stderr)
    finally:
        for container in created_containers:
            checks.append(run("task7-cleanup-" + container, ["docker", "rm", "-f", container]))
        for network in created_networks:
            checks.append(run("task7-cleanup-" + network, ["docker", "network", "rm", network]))
        if created_volume:
            checks.append(run("task7-cleanup-volume", ["docker", "volume", "rm", volume]))
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "networks.json").write_text(json.dumps({
            "captured_at": datetime.now(UTC).isoformat(), "checks": checks,
            "scope": "Network reachability/isolation and named-volume persistence; not a MySQL application test."
        }, indent=2) + "\n", encoding="utf-8")
    return int(any(check["exit_code"] for check in checks))


if __name__ == "__main__":
    sys.exit(main())
