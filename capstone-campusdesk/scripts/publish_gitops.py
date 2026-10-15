"""Promote tested images on the current branch tip without rebasing stale release values."""

import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT = "capstone-campusdesk"
RELEASE = f"{PROJECT}/helm/campusdesk/values-release.json"


def publish(root, sha, attempts=3):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Expected full Git commit SHA")

    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=root, check=check)

    for _ in range(attempts):
        git("fetch", "origin", "main")
        changed = git("diff", "--quiet", sha, "origin/main", "--", PROJECT,
                      ".github/workflows/campusdesk.yml", f":(exclude){RELEASE}", check=False)
        if changed.returncode == 1:
            print("A newer capstone source revision exists; this run will not promote stale images.")
            return "superseded"
        changed.check_returncode()
        # This runs in an isolated CI checkout. Never reset a developer's working tree.
        git("switch", "--detach", "origin/main")
        subprocess.run([sys.executable, str(root / PROJECT / "scripts/promote.py")],
                       cwd=root, env={**os.environ, "GITHUB_SHA": sha}, check=True)
        git("add", RELEASE)
        staged = git("diff", "--cached", "--quiet", check=False)
        if staged.returncode == 0:
            return "unchanged"
        if staged.returncode != 1:
            staged.check_returncode()
        git("commit", "-m", "chore(gitops): promote verified CampusDesk images [skip ci]")
        if git("push", "origin", "HEAD:main", check=False).returncode == 0:
            return "promoted"
        print("Remote changed or push failed; rechecking current source before retrying.")
    raise RuntimeError("Could not publish GitOps promotion after bounded retries")


if __name__ == "__main__":
    print(publish(Path(__file__).resolve().parents[2], os.environ["GITHUB_SHA"]))
