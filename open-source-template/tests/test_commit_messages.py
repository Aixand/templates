# SPDX-License-Identifier: Apache-2.0
"""Exercise Git range handling and hook dispatch without network dependencies."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "examples/git-hooks/scripts/checks/check-commit-messages.py"
spec = importlib.util.spec_from_file_location("commit_messages", SCRIPT)
CHECK = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CHECK)


class CommitMessageTests(unittest.TestCase):
    def setUp(self):
        self.original = Path.cwd()
        self.directory = tempfile.TemporaryDirectory()
        os.chdir(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(os.chdir, self.original)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture Author")
        self.git("config", "user.email", "fixture@example.invalid")
        self.base = self.commit("Historical message before adopting conventions")

    def git(self, *args):
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.PIPE).strip()

    def commit(self, message):
        self.git("-c", "core.hooksPath=/dev/null", "commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def test_range_excludes_old_history_and_includes_every_new_commit(self):
        first = self.commit("feat: add a command")
        second = self.commit("fix: handle empty input")
        self.assertEqual(CHECK.commits_between(self.base, second), [first, second])

    def test_option_and_revision_syntax_are_rejected(self):
        for value in ("--all", "HEAD", self.base + "..HEAD", "0" * 40):
            with self.subTest(value=value), self.assertRaises((ValueError, subprocess.CalledProcessError)):
                CHECK.commits_between(value, self.base)

    def test_empty_range_is_not_reported_as_success(self):
        with self.assertRaises(ValueError):
            CHECK.commits_between(self.base, self.base)

    def test_unrelated_histories_are_rejected(self):
        tree = self.git("rev-parse", self.base + "^{tree}")
        unrelated = self.git("commit-tree", tree, "-m", "Unrelated root")
        with self.assertRaises(subprocess.CalledProcessError):
            CHECK.commits_between(self.base, unrelated)

    def run_with_hook(self, messages, fail_message=None):
        shas = [self.commit(message) for message in messages]
        seen = []
        real_run = subprocess.run

        def run(command, **kwargs):
            if command[:3] == [sys.executable, "-m", "pre_commit"]:
                self.assertIn("--commit-msg-filename", command)
                self.assertNotIn("shell", kwargs)
                text = Path(command[-1]).read_text()
                seen.append(text.strip())
                return subprocess.CompletedProcess(command, int(text.strip() == fail_message))
            return real_run(command, **kwargs)

        output = io.StringIO()
        with patch.object(CHECK.subprocess, "run", side_effect=run), contextlib.redirect_stdout(output):
            code = CHECK.check_commits(self.base, shas[-1])
        return code, seen, output.getvalue(), shas

    def test_all_messages_reach_the_configured_hook(self):
        messages = ["feat: add a command", "fix: handle empty input"]
        code, seen, output, _ = self.run_with_hook(messages)
        self.assertEqual(code, 0)
        self.assertEqual(seen, messages)
        self.assertIn("passed", output)

    def test_middle_failure_cannot_be_hidden_by_a_valid_tip(self):
        messages = ["feat: first", "unformatted middle", "fix: last"]
        code, seen, output, shas = self.run_with_hook(messages, fail_message=messages[1])
        self.assertEqual(code, 1)
        self.assertEqual(seen, messages)
        self.assertIn(shas[1][:12], output)

    def test_message_contents_are_not_executed_or_printed(self):
        message = 'invalid $(touch marker)\n\n::error::untrusted message'
        code, seen, output, _ = self.run_with_hook([message], fail_message=message)
        self.assertEqual(code, 1)
        self.assertEqual(seen, [message])
        self.assertFalse(Path("marker").exists())
        self.assertNotIn("::error::", output)


if __name__ == "__main__":
    unittest.main()
