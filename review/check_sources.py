"""Read-only syntax and link checks across every numbered homework folder."""

import ast
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("HOMEWORK_RESULTS_DIR", ROOT / "review/results"))


class UniqueLoader(yaml.BaseLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key} at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def main():
    results = []
    for task in sorted(ROOT.glob("task-*"), key=lambda p: int(p.name.split("-")[1])):
        record = {"task": task.name, "checked": {}, "issues": [], "template_files": []}
        for path in sorted(task.rglob("*")):
            if not path.is_file() or any(part in {".terraform", "node_modules", ".venv", "__pycache__"} for part in path.parts):
                continue
            relative = path.relative_to(ROOT).as_posix()
            suffix = path.suffix.lower()
            if suffix not in {".yaml", ".yml", ".json", ".py", ".md"}:
                continue
            text = path.read_text(encoding="utf-8-sig")
            try:
                if suffix in {".yaml", ".yml"}:
                    if "templates" in path.parts and "{{" in text:
                        record["template_files"].append(relative)
                        continue
                    list(yaml.load_all(text, Loader=UniqueLoader))
                elif suffix == ".json":
                    json.loads(text)
                elif suffix == ".py":
                    ast.parse(text, filename=relative)
                else:
                    # Only inspect inline relative links; anchors and external URLs are separate checks.
                    for target in re.findall(r"\]\(([^)\n]+)\)", text):
                        target = target.strip().split("#", 1)[0]
                        if not target or re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("<"):
                            continue
                        target = unquote(target.split(' "', 1)[0])
                        if not (path.parent / target).exists():
                            record["issues"].append({"file": relative, "type": "missing-link", "target": target})
                record["checked"][suffix] = record["checked"].get(suffix, 0) + 1
            except (ValueError, SyntaxError, yaml.YAMLError) as error:
                record["issues"].append({"file": relative, "type": "syntax", "detail": str(error)})
        results.append(record)
        print(f"{task.name}: {sum(record['checked'].values())} files checked, {len(record['issues'])} issues")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "source-checks.json").write_text(json.dumps({
        "captured_at": datetime.now(UTC).isoformat(), "tasks": results,
        "scope": "Syntax and relative file links only; not deployment or screenshot authenticity."
    }, indent=2) + "\n", encoding="utf-8")
    return int(any(record["issues"] for record in results))


if __name__ == "__main__":
    raise SystemExit(main())
