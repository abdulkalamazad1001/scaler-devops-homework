"""Check rendered workload command types, including Helm test hooks skipped on install."""

import sys
from pathlib import Path

import yaml


def main():
    checked = 0
    for document in yaml.safe_load_all(Path(sys.argv[1]).read_text(encoding="utf-8")):
        if not document:
            continue
        spec = document.get("spec", {})
        if document["kind"] == "CronJob":
            spec = spec["jobTemplate"]["spec"]
        pod = spec.get("template", {}).get("spec", spec)
        for container in pod.get("containers", []) + pod.get("initContainers", []):
            for field in ("command", "args"):
                value = container.get(field, [])
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    raise ValueError(f"{document['metadata']['name']}: {container['name']}.{field} must be a list of strings")
            checked += 1
    print(f"PASS: command/args types for {checked} rendered containers, including test hooks")


if __name__ == "__main__":
    main()
