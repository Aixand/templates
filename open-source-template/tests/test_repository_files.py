"""Load reusable policy regression tests and check the template's adopted copies."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "shared_repository_files_test",
    ROOT / "files/tests/tooling/checks/repository_files_test.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PolicyNamesTests = MODULE.PolicyNamesTests
PolicyGitTests = MODULE.PolicyGitTests


class AdoptedCopiesTests(unittest.TestCase):
    def test_baseline_and_template_policy_copies_agree(self):
        for name in [
            "scripts/checks/check-repository-files.py",
            "scripts/checks/install-file-policy-hook.py",
            "tests/tooling/checks/repository_files_test.py",
            ".github/workflows/repository-files.yml",
            "REPOSITORY_FILES.md",
        ]:
            with self.subTest(path=name):
                self.assertEqual(
                    (ROOT / name).read_bytes(), (ROOT / "files" / name).read_bytes()
                )
