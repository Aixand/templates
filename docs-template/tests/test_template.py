"""Qualify template adoption and reader-visible example behavior."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts/render-template.py"
SPEC = importlib.util.spec_from_file_location("aixand_template_renderer", RENDERER)
RENDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDER)


class TemplateTests(unittest.TestCase):
    def test_missing_or_extra_values_fail(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            RENDER.render("{{NAME}}", {})
        with self.assertRaisesRegex(ValueError, "unused"):
            RENDER.render("{{NAME}}", {"NAME": "Example", "EXTRA": "x"})

    def test_values_are_literal_and_new_tokens_fail(self):
        self.assertEqual("$(never-execute)", RENDER.render("{{NAME}}", {"NAME": "$(never-execute)"}))
        with self.assertRaisesRegex(ValueError, "unresolved"):
            RENDER.render("{{NAME}}", {"NAME": "{{NEW_TOKEN}}"})

    def test_every_page_template_renders(self):
        sources = list((ROOT / "templates").rglob("*.example"))
        self.assertGreaterEqual(len(sources), 14)
        for source in sources:
            text = source.read_text()
            values = {key: "Example" for key in RENDER.TOKEN.findall(text)}
            with self.subTest(source=source):
                output = RENDER.render(text, values)
                self.assertNotRegex(output, r"\{\{[A-Z][A-Z0-9_]*\}\}")
                if source.name.endswith(".json.example"):
                    json.loads(output)

    def test_existing_file_and_symlink_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "README.md"
            destination.write_text("keep")
            command = [sys.executable, str(RENDERER), str(ROOT / "templates/project/README.md.example"), str(destination), "--set", "PROJECT_NAME=Example"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertEqual("keep", destination.read_text())
            dangling = root / "AGENTS.md"
            try:
                dangling.symlink_to(root / "missing")
            except OSError:
                return
            command[3] = str(dangling)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertTrue(dangling.is_symlink())
            self.assertFalse((root / "missing").exists())

    def test_invalid_input_does_not_create_destination_parents(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "new" / "README.md"
            result = subprocess.run([sys.executable, str(RENDERER), str(ROOT / "templates/project/README.md.example"), str(destination)], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertFalse(destination.parent.exists())

    def test_local_entry_point_points_to_copied_contract(self):
        output = RENDER.render((ROOT / "templates/agent-instructions.md.example").read_text(), {"STANDARDS_PATH": "docs/_standards"})
        self.assertIn("docs/_standards/agent-workflow.md", output)
        self.assertIn("AGENTS.md", (ROOT / ".gitignore").read_text())

    def test_copied_standards_and_checker_work_without_template_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            shutil.copytree(ROOT / "files", project, dirs_exist_ok=True)
            (project / "README.md").write_text("# Example\n\n[Docs](docs/README.md)\n")
            (project / "CONTRIBUTING.md").write_text("# Contribute\n\nUse the documentation index.\n")
            (project / "docs/README.md").write_text("# Documentation\n\n[Standard](_standards/README.md)\n")
            result = subprocess.run([sys.executable, str(project / "scripts/checks/check-docs.py"), "--root", str(project)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            result = subprocess.run([sys.executable, str(project / "tests/tooling/checks/docs_test.py")], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_template_and_copied_standard_versions_agree(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertEqual(version, (ROOT / "files/docs/_standards/VERSION").read_text().strip())
        self.assertIn(version, (ROOT / "files/docs/_standards/standard.md").read_text())
        self.assertEqual(version, json.loads((ROOT / "tools/package.json").read_text())["version"])

    def test_published_paths_follow_repository_file_policy(self):
        spec = importlib.util.spec_from_file_location("template_file_policy", ROOT / "scripts/checks/check-repository-files.py")
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        ignored = {"node_modules", "build", "__pycache__"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or ignored.intersection(path.relative_to(ROOT).parts):
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative == "AGENTS.md":
                continue
            self.assertFalse(policy.forbidden(relative), relative)
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            shutil.copy2(ROOT / ".gitignore", project / ".gitignore")
            (project / "AGENTS.md").write_text("Local instructions\n")
            subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
            result = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", "AGENTS.md"], capture_output=True)
            self.assertEqual(0, result.returncode)


class WorkingExampleTests(unittest.TestCase):
    def invoke(self, *arguments):
        return subprocess.run([sys.executable, "tools/status.py", *arguments], cwd=ROOT / "examples/project", capture_output=True, text=True)

    def test_default_matches_tutorial(self):
        result = self.invoke()
        self.assertEqual((0, "ready\n", ""), (result.returncode, result.stdout, result.stderr))

    def test_busy_matches_task_and_reference(self):
        result = self.invoke("--state", "busy")
        self.assertEqual((1, "busy\n", ""), (result.returncode, result.stdout, result.stderr))

    def test_invalid_value_matches_error_contract(self):
        result = self.invoke("--state", "broken")
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("invalid choice", result.stderr)

    def test_help_matches_reference(self):
        result = self.invoke("--help")
        self.assertEqual(0, result.returncode)
        self.assertIn("--state", result.stdout)
        self.assertEqual("", result.stderr)


if __name__ == "__main__":
    unittest.main()
