"""Verify that a missing tool or failed gate cannot become a successful release."""

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("security_check", Path(__file__).with_name("security-check.py"))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


class SecurityCheckTests(unittest.TestCase):
    def run_checks(self, outcomes):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "bandit.json").write_text('{"stale": true}', encoding="utf-8")
            with patch.object(scan, "OUTPUT", output), patch.object(
                scan.subprocess, "run", side_effect=outcomes
            ) as execute, contextlib.redirect_stdout(io.StringIO()):
                code = scan.main()
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertFalse((output / "bandit.json").exists())
            self.assertEqual(execute.call_count, 4)
            command = execute.call_args_list[-1].args[0]
            self.assertIn("--redact", command)
            self.assertIn("--log-opts=--all -- capstone-campusdesk .github/workflows/campusdesk.yml", command)
            return code, summary

    def test_all_checks_must_pass(self):
        code, summary = self.run_checks([subprocess.CompletedProcess([], 0, "{}", "")] * 4)
        self.assertEqual(code, 0)
        self.assertTrue(all(item["exit_code"] == 0 for item in summary))

    def test_finding_blocks_release_but_runs_remaining_checks(self):
        code, summary = self.run_checks([
            subprocess.CompletedProcess([], 1, "{}", "finding"),
            *[subprocess.CompletedProcess([], 0, "{}", "")] * 3,
        ])
        self.assertEqual(code, 1)
        self.assertEqual(summary[0]["exit_code"], 1)

    def test_missing_tool_blocks_release(self):
        code, _ = self.run_checks([FileNotFoundError("missing tool")] * 4)
        self.assertEqual(code, 1)

    def test_timeout_blocks_release(self):
        code, _ = self.run_checks([subprocess.TimeoutExpired("scanner", 600)] * 4)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
