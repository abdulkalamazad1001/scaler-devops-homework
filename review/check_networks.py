"""Verify task 7 network isolation and named-volume persistence in disposable containers."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
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
            image_args = (["-e", "MYSQL_ALLOW_EMPTY_PASSWORD=yes", "mysql:8.4"] if index == 2
                          else ["alpine:3.22", "sleep", "600"])
            check(f"container-{index}", ["run", "-d", "--name", container, "--network", network,
                                         *image_args])
            created_containers.append(container)
        check("connect-backend", ["network", "connect", networks[1], containers[1]])
        check("connect-database", ["network", "connect", networks[2], containers[2]])
        check("front-to-back", ["exec", containers[0], "ping", "-c", "1", containers[1]])
        check("back-to-db", ["exec", containers[1], "ping", "-c", "1", containers[2]])
        check("mysql-ready", ["exec", containers[2], "sh", "-ec",
              "for i in $(seq 1 90); do mysqladmin -h127.0.0.1 ping --silent && exit 0; sleep 2; done; exit 1"])
        check("mysql-query", ["exec", containers[2], "mysql", "-uroot", "-e",
              "SELECT VERSION() AS database_version; CREATE DATABASE homework; SHOW DATABASES;"])
        check("backend-mysql-port", ["exec", containers[1], "nc", "-z", "-w", "5", containers[2], "3306"])
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
        with tempfile.TemporaryDirectory(prefix="homework-bind-") as folder:
            # TemporaryDirectory uses 0700; Nginx's unprivileged worker must be able to traverse it.
            Path(folder).chmod(0o755)
            page = Path(folder) / "index.html"
            page.write_text("Hello students\n")
            page.chmod(0o644)
            web = prefix + "-bind"
            check("bind-start", ["run", "-d", "--name", web, "--network", networks[0],
                  "--mount", f"type=bind,source={folder},target=/usr/share/nginx/html,readonly", "nginx:1.27-alpine"])
            created_containers.append(web)
            for label, expected in [("initial", "Hello students"), ("updated", "Hello students updated live")]:
                page.write_text(expected + "\n")
                check("bind-" + label, ["exec", containers[0], "sh", "-ec",
                      f"for i in 1 2 3 4 5; do wget -qO- http://{web} | grep '{expected}' && exit 0; sleep 1; done; exit 1"])
        host = prefix + "-host"
        check("host-start", ["run", "-d", "--name", host, "--network", "host", "httpd:2.4-alpine"])
        created_containers.append(host)
        check("host-port80", ["run", "--rm", "--network", "host", "alpine:3.22", "sh", "-ec",
              "for i in 1 2 3 4 5; do wget -qO- http://127.0.0.1:80 | grep 'It works' && exit 0; sleep 2; done; exit 1"])
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
            "scope": "Isolated MySQL lab (empty root password, no published database port), three networks, connectivity/isolation, volume persistence, live bind mount and Apache host networking. Host means the Docker Linux host, including the VM on macOS."
        }, indent=2) + "\n", encoding="utf-8")
    return int(any(check["exit_code"] for check in checks))


if __name__ == "__main__":
    sys.exit(main())
