from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "files/scripts/dev"))

from core import Project, digest, write_json  # noqa: E402
from installs import activate, locked, reference, state_of  # noqa: E402
from packages import descriptor  # noqa: E402
from render_fixture import render as render_original  # noqa: E402


def render(name, destination):
    project = render_original(name, destination)
    if name.startswith("python-"):
        config = project / "installation.toml"
        config.write_text(
            config.read_text().replace(
                'version = "3.14"',
                f'version = "{sys.version_info.major}.{sys.version_info.minor}"',
            )
        )
    return project


def invoke(project, *args, expected=0, cwd=None):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "UV_LINK_MODE": "copy"}
    command = [
        sys.executable,
        "-B",
        str(project / "scripts/dev/cli.py"),
        "--project",
        str(project),
        *map(str, args),
    ]
    result = subprocess.run(
        command,
        cwd=cwd or project.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
    )
    if result.returncode != expected:
        raise AssertionError(
            f"{args} returned {result.returncode}, expected {expected}\n{result.stdout}\n{result.stderr[-9000:]}"
        )
    return result


def reseal(artifact, manifest):
    for name in manifest["files"]:
        manifest["files"][name] = descriptor(artifact / name)
    write_json(artifact / "release-manifest.json", manifest)
    sums = {
        **manifest["files"],
        "release-manifest.json": descriptor(artifact / "release-manifest.json"),
    }
    (artifact / "SHA256SUMS").write_text(
        "".join(f"{item['sha256']}  {name}\n" for name, item in sorted(sums.items()))
    )


def fixture_git(project, *args):
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=" + str(project / ".git/disabled-hooks"),
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            *args,
        ],
        cwd=project,
        env=env,
        check=True,
        capture_output=True,
        timeout=30,
    )


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="contract dispatch 世界 ")
        self.base = Path(self.temporary.name)
        self.project = render("python-library", self.base / "project with spaces")

    def tearDown(self):
        self.temporary.cleanup()

    def test_help_does_not_need_project_or_tools(self):
        result = subprocess.run(
            [str(self.project / "dev.sh"), "help"],
            cwd=self.base,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doctor", result.stdout)
        self.assertFalse((self.project / ".venv").exists())
        self.assertFalse(list((self.project / "scripts").rglob("__pycache__")))
        older = self.base / "unsupported-python"
        older.write_text("#!/bin/sh\nexit 1\n")
        older.chmod(0o755)
        fallback = subprocess.run(
            [str(self.project / "dev.sh"), "help"],
            cwd=self.base,
            env={**os.environ, "AIXAND_DEV_PYTHON": str(older)},
            capture_output=True,
            text=True,
        )
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertIn("Commands:", fallback.stdout)

    def test_unknown_and_inapplicable_flags_fail(self):
        invoke(self.project, "test", "--prefix", self.base / "prefix", expected=2)
        invoke(self.project, "build", "--target", "bogus", expected=2)
        invoke(self.project, "install", "--editable", expected=2)

    def test_library_global_install_and_implicit_publish_are_unsupported(self):
        invoke(self.project, "install", expected=2)
        invoke(self.project, "publish", expected=2)

    def test_doctor_does_not_repair_missing_lock(self):
        (self.project / "uv.lock").unlink()
        result = invoke(self.project, "doctor", expected=1)
        self.assertFalse(json.loads(result.stdout)["lock_present"])
        invoke(self.project, "develop", expected=1)
        self.assertFalse((self.project / "uv.lock").exists())
        self.assertFalse((self.project / ".venv").exists())

    def test_malformed_config_and_unsafe_resource_fail(self):
        config = self.project / "installation.toml"
        original = config.read_text()
        config.write_text("unknown = true\n" + original)
        invoke(self.project, "doctor", expected=1)
        config.write_text(
            original.replace(
                'manifest = "pyproject.toml"', 'resources = ["../outside"]'
            )
        )
        invoke(self.project, "doctor", expected=1)

    def test_custom_arguments_are_not_shell_code(self):
        config = self.project / "installation.toml"
        config.write_text("""schema=1
profile="custom"
[custom]
name="custom-fixture"
version="unreleased"
[commands]
test=[["{python}","-c","import sys; assert sys.argv[1] == '$(touch sentinel)'", "$(touch sentinel)"]]
""")
        invoke(self.project, "test")
        self.assertFalse((self.project / "sentinel").exists())

    def test_dry_run_does_not_create_prefix_or_build(self):
        project = render("python-tool", self.base / "tool")
        prefix = self.base / "unused"
        result = invoke(project, "install", "--prefix", prefix, "--dry-run")
        self.assertFalse(json.loads(result.stdout)["executed"])
        self.assertFalse(prefix.exists())
        self.assertFalse((project / "dist").exists())

    def test_ignored_runtime_data_is_not_a_release_source_input(self):
        ignore = self.project / ".gitignore"
        ignore.write_text(ignore.read_text() + ".runtime-data/\n")
        fixture_git(self.project, "init", "-q")
        fixture_git(self.project, "add", ".")
        fixture_git(
            self.project,
            "-c",
            "user.name=Installation Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "Synthetic fixture",
        )
        original = Project(self.project).identity()
        (self.project / ".runtime-data").mkdir()
        (self.project / ".runtime-data/database").write_text("private synthetic state")
        self.assertEqual(Project(self.project).identity(), original)


@unittest.skipUnless(
    shutil.which("uv") and shutil.which("cargo"), "integration requires uv and Cargo"
)
class PackageAndLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="artifact contracts 世界 ")
        cls.base = Path(cls.temporary.name)
        cls.projects = {}
        cls.artifacts = {}
        for name in [
            "python-library",
            "python-tool",
            "rust-library",
            "rust-cli",
            "rust-workspace",
        ]:
            project = render(name, cls.base / name)
            cls.projects[name] = project
            invoke(project, "develop")
            invoke(project, "check")
            invoke(project, "test")
            artifact = cls.base / (name + "-artifact")
            invoke(project, "package", "--output", artifact)
            cls.artifacts[name] = artifact

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(prefix="installation-case-")
        self.case_root = Path(self.case.name)

    def tearDown(self):
        self.case.cleanup()

    def artifact_copy(self, name):
        path = self.case_root / "artifact"
        shutil.copytree(self.artifacts[name], path)
        return path

    def test_all_distributions_have_independent_consumers(self):
        for name, project in self.projects.items():
            with self.subTest(profile=name):
                result = invoke(
                    project, "verify", "--artifact", self.artifacts[name], "--install"
                )
                self.assertTrue(json.loads(result.stdout)["installation_tested"])

    def test_registry_dependency_wheel_is_inventoried(self):
        artifact = self.artifacts["python-tool"]
        manifest = json.loads((artifact / "release-manifest.json").read_text())
        self.assertTrue(
            any(name.startswith("wheelhouse/idna-") for name in manifest["files"])
        )
        self.assertEqual(
            manifest["source"]["locks"]["uv.lock"],
            digest(self.projects["python-tool"] / "uv.lock"),
        )

    def test_generated_manifests_and_receipts_match_schemas(self):
        executable = (
            ROOT
            / "tools/.venv"
            / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        )
        self.assertTrue(
            executable.exists(), "Run ./dev.sh develop before the template tests"
        )
        for artifact in self.artifacts.values():
            result = subprocess.run(
                [
                    executable,
                    "-c",
                    "import json,jsonschema,sys;jsonschema.validate(json.load(open(sys.argv[1])),json.load(open(sys.argv[2])))",
                    artifact / "release-manifest.json",
                    ROOT / "schemas/release-manifest.schema.json",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        if os.name != "nt":
            prefix = self.case_root / "prefix"
            invoke(
                self.projects["rust-cli"],
                "install",
                "--artifact",
                self.artifacts["rust-cli"],
                "--prefix",
                prefix,
            )
            result = subprocess.run(
                [
                    executable,
                    "-c",
                    "import json,jsonschema,sys;jsonschema.validate(json.load(open(sys.argv[1])),json.load(open(sys.argv[2])))",
                    prefix / "installation-receipt.json",
                    ROOT / "schemas/installation-receipt.schema.json",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_output_is_immutable_and_corrupt_package_is_rejected(self):
        artifact = self.artifact_copy("rust-cli")
        project = self.projects["rust-cli"]
        invoke(project, "package", "--output", artifact, expected=1)
        manifest = json.loads((artifact / "release-manifest.json").read_text())
        with (artifact / manifest["primary"]).open("ab") as stream:
            stream.write(b"tampered")
        invoke(project, "verify", "--artifact", artifact, expected=1)

    def test_missing_python_dependency_fails_even_with_warm_cache(self):
        artifact = self.artifact_copy("python-tool")
        project = self.projects["python-tool"]
        manifest = json.loads((artifact / "release-manifest.json").read_text())
        for name in list(manifest["files"]):
            if name.startswith("wheelhouse/"):
                (artifact / name).unlink()
                del manifest["files"][name]
        reseal(artifact, manifest)
        invoke(project, "verify", "--artifact", artifact, "--install", expected=1)

    def test_archive_paths_links_and_duplicate_members_are_rejected(self):
        for kind in ["traversal", "symlink", "duplicate"]:
            with (
                self.subTest(kind=kind),
                tempfile.TemporaryDirectory(prefix="bad-archive-") as temporary,
            ):
                artifact = Path(temporary) / "artifact"
                shutil.copytree(self.artifacts["rust-cli"], artifact)
                manifest = json.loads((artifact / "release-manifest.json").read_text())
                with tarfile.open(artifact / manifest["primary"], "w:gz") as archive:
                    entry = tarfile.TarInfo(
                        "../sentinel" if kind == "traversal" else "bin/fixture-rust-cli"
                    )
                    if kind == "symlink":
                        entry.type = tarfile.SYMTYPE
                        entry.linkname = "/etc/passwd"
                        archive.addfile(entry)
                    else:
                        entry.size = 1
                        archive.addfile(entry, io.BytesIO(b"x"))
                        if kind == "duplicate":
                            archive.addfile(entry, io.BytesIO(b"x"))
                reseal(artifact, manifest)
                invoke(
                    self.projects["rust-cli"],
                    "verify",
                    "--artifact",
                    artifact,
                    expected=1,
                )
                self.assertFalse((Path(temporary) / "sentinel").exists())

    @unittest.skipIf(os.name == "nt", "managed activation is Unix-only")
    def test_conflict_rejection_and_successful_retry_preserve_user_data(self):
        project, artifact = self.projects["rust-cli"], self.artifacts["rust-cli"]
        prefix = self.case_root / "prefix"
        prefix.mkdir()
        unrelated = prefix / "unrelated"
        unrelated.write_text("preserve")
        invoke(
            project, "install", "--artifact", artifact, "--prefix", prefix, expected=1
        )
        self.assertEqual(unrelated.read_text(), "preserve")
        unrelated.unlink()
        invoke(project, "install", "--artifact", artifact, "--prefix", prefix)
        state = prefix / "state/database"
        state.parent.mkdir()
        state.write_text("user data")
        run = subprocess.run(
            [prefix / "bin/fixture-rust-cli", "--self-test"], capture_output=True
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        invoke(project, "uninstall", "--prefix", prefix, expected=1)
        invoke(project, "uninstall", "--prefix", prefix, "--stopped")
        self.assertEqual(state.read_text(), "user data")
        result = invoke(project, "uninstall", "--prefix", prefix, "--stopped")
        self.assertTrue(json.loads(result.stdout)["already_absent"])

    @unittest.skipIf(os.name == "nt", "managed activation is Unix-only")
    def test_python_private_environment_survives_source_removal(self):
        source = render("python-tool", self.case_root / "source")
        artifact = self.artifacts["python-tool"]
        prefix = self.case_root / "prefix with spaces 世界"
        invoke(source, "install", "--artifact", artifact, "--prefix", prefix)
        shutil.rmtree(source)
        result = subprocess.run(
            [prefix / "bin/fixture-tool", "--self-test"],
            cwd=self.case_root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        invoke(
            self.projects["python-tool"], "uninstall", "--prefix", prefix, "--stopped"
        )

    @unittest.skipIf(os.name == "nt", "managed activation is Unix-only")
    def test_versions_rollback_retention_and_failed_upgrade(self):
        project = render("rust-cli", self.case_root / "source")
        versions = [self.artifacts["rust-cli"]]
        for number in [1, 2]:
            manifest = project / "Cargo.toml"
            manifest.write_text(
                manifest.read_text().replace(
                    f'version = "0.0.{number - 1}"', f'version = "0.0.{number}"'
                )
            )
            subprocess.run(
                ["cargo", "generate-lockfile"],
                cwd=project,
                check=True,
                capture_output=True,
            )
            artifact = self.case_root / f"release-{number}"
            invoke(project, "package", "--output", artifact)
            versions.append(artifact)
        prefix = self.case_root / "prefix"
        invoke(project, "install", "--artifact", versions[0], "--prefix", prefix)
        for artifact in versions[1:]:
            invoke(project, "upgrade", "--artifact", artifact, "--prefix", prefix)
        current = (prefix / "installation-receipt.json").read_bytes()
        bad = self.artifact_copy("rust-cli")
        manifest = json.loads((bad / "release-manifest.json").read_text())
        (bad / manifest["primary"]).write_bytes(b"corrupt")
        invoke(project, "upgrade", "--artifact", bad, "--prefix", prefix, expected=1)
        self.assertEqual((prefix / "installation-receipt.json").read_bytes(), current)
        invoke(project, "rollback", "--prefix", prefix)
        version = subprocess.check_output(
            [prefix / "bin/fixture-rust-cli", "--version"], text=True
        )
        self.assertIn("0.0.1", version)
        plan = json.loads(
            invoke(project, "prune", "--prefix", prefix, "--dry-run").stdout
        )
        self.assertEqual(len(plan["retired_payloads"]), 1)
        invoke(project, "prune", "--prefix", prefix, expected=1)
        invoke(project, "prune", "--prefix", prefix, "--stopped")
        self.assertEqual(len(list((prefix / "payloads").iterdir())), 2)

    @unittest.skipIf(os.name == "nt", "Unix locking contract")
    def test_concurrent_mutations_and_changed_commands_are_rejected(self):
        project, artifact = self.projects["rust-cli"], self.artifacts["rust-cli"]
        prefix = self.case_root / "prefix"
        invoke(project, "install", "--artifact", artifact, "--prefix", prefix)
        with locked(prefix, Project(project)):
            invoke(
                project,
                "reinstall",
                "--artifact",
                artifact,
                "--prefix",
                prefix,
                expected=1,
            )
        command = prefix / "bin/fixture-rust-cli"
        command.unlink()
        command.write_text("unrelated")
        invoke(project, "uninstall", "--prefix", prefix, "--stopped", expected=1)
        self.assertEqual(command.read_text(), "unrelated")

    @unittest.skipIf(os.name == "nt", "Unix activation contract")
    def test_interrupted_activation_recovers_previous_selection(self):
        project, artifact = self.projects["rust-cli"], self.artifacts["rust-cli"]
        prefix = self.case_root / "prefix"
        invoke(project, "install", "--artifact", artifact, "--prefix", prefix)
        configured = Project(project)
        with locked(prefix, configured):
            old = state_of(prefix, configured)
            new = {**old, "current": "a" * 64, "previous": old["current"]}
            from installs import atomic_json

            def fail_receipt(path, value):
                if path.name == "installation-receipt.json" and value == new:
                    raise OSError("synthetic receipt write failure")
                return atomic_json(path, value)

            with (
                patch("installs.atomic_json", side_effect=fail_receipt),
                self.assertRaises(OSError),
            ):
                activate(prefix, new, old)
            self.assertEqual(state_of(prefix, configured), old)
            self.assertFalse((prefix / ".activation.json").exists())
            # Simulate a process ending after pointer switch but before receipt commit.
            write_json(prefix / ".activation.json", {"old": old, "new": new})
            reference(prefix, new["current"])
        with locked(prefix, configured):
            self.assertEqual(state_of(prefix, configured), old)

    def test_release_gate_rejects_wrong_tag_and_dirty_source(self):
        project = render("rust-library", self.case_root / "source")
        invoke(project, "release-check", "--version", "v9.9.9", expected=1)
        fixture_git(project, "init", "-q")
        fixture_git(project, "add", ".")
        fixture_git(
            project,
            "-c",
            "user.name=Installation Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "Synthetic fixture",
        )
        fixture_git(project, "tag", "v0.0.0")
        invoke(project, "release-check", "--version", "v0.0.0")
        artifact = self.case_root / "release-package"
        invoke(project, "package", "--output", artifact)
        invoke(project, "release-check", "--version", "v0.0.0", "--artifact", artifact)
        manifest = json.loads((artifact / "release-manifest.json").read_text())
        manifest["source"]["source_sha256"] = "0" * 64
        reseal(artifact, manifest)
        invoke(
            project,
            "release-check",
            "--version",
            "v0.0.0",
            "--artifact",
            artifact,
            expected=1,
        )
        (project / "src/lib.rs").write_text("broken unpublished change")
        invoke(project, "release-check", "--version", "v0.0.0", expected=1)


if __name__ == "__main__":
    unittest.main()
