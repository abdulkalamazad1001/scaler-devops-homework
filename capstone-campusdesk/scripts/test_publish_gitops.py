"""Local Git integration tests; no GitHub credentials or deployment required."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from publish_gitops import PROJECT, RELEASE, publish


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.writer = self.root / "writer"
        self.runner = self.root / "runner"
        self.git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git(self.root, "clone", str(self.remote), str(self.writer))
        self.configure(self.writer)
        project = self.writer / PROJECT
        (project / "helm/campusdesk").mkdir(parents=True)
        (project / "scripts").mkdir()
        shutil.copyfile(Path(__file__).with_name("promote.py"), project / "scripts/promote.py")
        (project / "app.txt").write_text("tested source\n", encoding="utf-8")
        (self.writer / RELEASE).write_text(json.dumps({"backend": {"tag": "old"}, "frontend": {"tag": "old"}}))
        self.commit(self.writer, "source")
        self.sha = self.git(self.writer, "rev-parse", "HEAD")
        self.git(self.writer, "push", "origin", "main")
        self.git(self.root, "clone", str(self.remote), str(self.runner))
        self.configure(self.runner)

    def git(self, cwd, *args):
        return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

    def configure(self, folder):
        self.git(folder, "config", "user.name", "Promotion test fixture")
        self.git(folder, "config", "user.email", "fixture@example.invalid")
        self.git(folder, "config", "commit.gpgsign", "false")

    def commit(self, folder, message):
        self.git(folder, "add", ".")
        self.git(folder, "commit", "-m", message)

    def test_publishes_on_top_of_other_promotion_and_preserves_unrelated_changes(self):
        (self.writer / RELEASE).write_text(json.dumps({"backend": {"tag": "earlier-run"}, "frontend": {"tag": "earlier-run"}}))
        (self.writer / "homework.txt").write_text("keep unrelated work\n", encoding="utf-8")
        self.commit(self.writer, "another promotion and homework update")
        self.git(self.writer, "push", "origin", "main")
        self.assertEqual(publish(self.runner, self.sha), "promoted")
        values = json.loads(self.git(self.remote, "show", f"main:{RELEASE}"))
        self.assertEqual(values["backend"]["tag"], self.sha)
        self.assertEqual(values["frontend"]["tag"], self.sha)
        self.assertEqual(self.git(self.remote, "show", "main:homework.txt"), "keep unrelated work")
        self.assertEqual(publish(self.runner, self.sha), "unchanged")

    def test_newer_source_prevents_stale_promotion(self):
        (self.writer / PROJECT / "app.txt").write_text("newer source\n", encoding="utf-8")
        self.commit(self.writer, "new source")
        self.git(self.writer, "push", "origin", "main")
        tip = self.git(self.remote, "rev-parse", "main")
        self.assertEqual(publish(self.runner, self.sha), "superseded")
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), tip)

    def test_invalid_sha_is_rejected(self):
        with self.assertRaises(ValueError):
            publish(self.runner, "not-a-sha")


if __name__ == "__main__":
    unittest.main()
