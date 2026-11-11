"""Executable schema-2 qualification; no public publication or product migrations."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import io
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "files/scripts/dev"))

from catalog import Workspace, host  # noqa: E402
from core import Failure, digest, filesystem_path, write_json  # noqa: E402
from operations import (  # noqa: E402
    activate,
    atomic,
    empty_state,
    helper_copy,
    inspect,
    install,
    locked,
    plan,
    payload_inventory,
    prepare,
    probe,
    prune,
    remove,
    rollback,
    state_of,
)
from releases import export, package, product_hash, seal, validate  # noqa: E402
from render_fixture import render  # noqa: E402
from runtime_support import provision, unpack  # noqa: E402


def fixture(name, path):
    root = render(name, path)
    config = root / "installation.toml"
    config.write_text(
        config.read_text().replace(
            '"3.14"', f'"{sys.version_info.major}.{sys.version_info.minor}"'
        )
    )
    return root


def cli(project, *args, expected=0):
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(project / "scripts/dev/cli.py"),
            "--project",
            str(project),
            *map(str, args),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "UV_LINK_MODE": "copy"},
    )
    if result.returncode != expected:
        raise AssertionError(
            f"{args}: {result.returncode}\n{result.stdout}\n{result.stderr[-6000:]}"
        )
    return result


def execute(store, command, *args, expected=0):
    helper = next((store / "helpers").glob("*/consumer.py"))
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(helper),
            "exec",
            "--prefix",
            str(store),
            "--command",
            command,
            "--",
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != expected:
        raise AssertionError(result.stdout + result.stderr)
    return result


class ProductContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="product contracts 世界 ")
        self.base = Path(self.temp.name)
        self.project = fixture("product-workspace", self.base / "project with spaces")
        self.workspace = Workspace(self.project)
        self.artifact = self.base / "release"
        package(self.workspace, self.artifact)
        self.store = self.base / "shared products"

    def tearDown(self):
        self.temp.cleanup()

    def test_public_command_receives_shutdown_and_preserves_clean_exit(self):
        install(self.artifact, self.store)
        ready = self.base / "command.ready"
        executable = self.store / "bin" / ("alpha.exe" if os.name == "nt" else "alpha")
        process = subprocess.Popen(
            [executable, "--wait", ready],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 20
            while not ready.exists():
                self.assertIsNone(process.poll())
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.05)
            if os.name != "nt":
                self.assertEqual(int(ready.read_text()), process.pid)
            process.send_signal(
                signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGTERM
            )
            stdout, stderr = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, stdout + stderr)
            self.assertEqual(
                ready.with_suffix(".stopped").read_text(), "clean shutdown"
            )
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)

    def test_individual_then_collection_reuses_same_product_and_survives_source_removal(
        self,
    ):
        individual = self.base / "individual"
        package(self.workspace, individual, product="example-suite/alpha")
        install(individual, self.store)
        before = state_of(self.store)["products"]["example-suite/alpha"]["payload"]
        install(self.artifact, self.store)
        after = state_of(self.store)
        self.assertEqual(before, after["products"]["example-suite/alpha"]["payload"])
        self.assertTrue(after["products"]["example-suite/alpha"]["explicit"])
        shutil.rmtree(self.project)
        normal_command = (
            self.store / "bin" / ("alpha.exe" if os.name == "nt" else "alpha")
        )
        normal = subprocess.run(
            [normal_command, "space value", "$(literal)", "a&b"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertEqual(
            json.loads(normal.stdout)["arguments"], ["space value", "$(literal)", "a&b"]
        )
        result = execute(self.store, "alpha", "space value", "$(literal)", "a&b")
        self.assertEqual(
            json.loads(result.stdout)["arguments"], ["space value", "$(literal)", "a&b"]
        )
        execute(self.store, "beta", "--fail", expected=23)
        removed = remove(self.store, "example-suite", stopped=True)
        self.assertEqual(removed["products"], ["example-suite/beta"])
        self.assertIn("example-suite/alpha", inspect(self.store)["products"])

    def test_plan_is_read_only_and_wrong_target_fails_before_mutation(self):
        result = plan(self.artifact, self.store)
        self.assertEqual(
            [x["action"] for x in result["products"]], ["install", "install"]
        )
        self.assertFalse(self.store.exists())

        _, manifest = validate(self.artifact)
        manifest["target"] = (
            "macos-x86_64" if host() != "macos-x86_64" else "linux-x86_64-gnu"
        )
        for item in manifest["products"].values():
            item["target"] = manifest["target"]
            item["release"] = product_hash(item)
        manifest["groups"]["example-suite"]["releases"] = {
            k: v["release"] for k, v in manifest["products"].items()
        }
        seal(self.artifact, manifest)
        with self.assertRaisesRegex(Failure, "target differs"):
            plan(self.artifact, self.store)
        with self.assertRaisesRegex(Failure, "target differs"):
            install(self.artifact, self.store)
        self.assertFalse(self.store.exists())

    def test_baseline_is_enforced_before_store_creation(self):
        _, manifest = validate(self.artifact)
        manifest["baseline"] = {key: "99999.0" for key in manifest["baseline"]}
        for item in manifest["products"].values():
            item["baseline"] = manifest["baseline"]
            item["release"] = product_hash(item)
        manifest["groups"]["example-suite"]["releases"] = {
            k: v["release"] for k, v in manifest["products"].items()
        }
        seal(self.artifact, manifest)
        with self.assertRaisesRegex(Failure, "older"):
            plan(self.artifact, self.store)
        with self.assertRaisesRegex(Failure, "older"):
            install(self.artifact, self.store)
        self.assertFalse(self.store.exists())

    def test_doctor_reports_missing_build_tools_without_provisioning(self):
        project = fixture("native-bundle", self.base / "native-doctor")
        with patch.dict(os.environ, {"PATH": ""}):
            result = cli(project, "doctor", expected=1)
        self.assertFalse(json.loads(result.stdout)["ready"])
        self.assertFalse((project / "target").exists())

    def test_product_release_gate_binds_tag_clean_source_and_version(self):
        def git(*args):
            env = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith("GIT_")
            }
            env.update(
                {
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_TERMINAL_PROMPT": "0",
                }
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "core.hooksPath=" + str(self.project / ".git/disabled-hooks"),
                    "-c",
                    "commit.gpgsign=false",
                    "-c",
                    "tag.gpgsign=false",
                    *args,
                ],
                cwd=self.project,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                env=env,
            )

        git("init", "-q")
        git("add", ".")
        git(
            "-c",
            "user.name=Installation Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "Synthetic product fixture",
        )
        tag = "example-suite/alpha/v1.0.0"
        git("tag", tag)
        artifact = self.base / "tagged"
        package(self.workspace, artifact, product="example-suite/alpha")
        args = (
            "release-check",
            "--product",
            "example-suite/alpha",
            "--artifact",
            artifact,
        )
        cli(self.project, *args, "--version", tag)
        cli(self.project, *args, "--version", "v1.0.0", expected=1)
        _, manifest = validate(artifact)
        manifest["version"] = "9.9.9"
        seal(artifact, manifest)
        cli(self.project, *args, "--version", tag, expected=1)
        (self.project / "LICENSE").write_text("dirty source")
        cli(
            self.project,
            "release-check",
            "--product",
            "example-suite/alpha",
            "--version",
            tag,
            expected=1,
        )

    def test_verification_evidence_is_bound_to_the_exported_bytes(self):
        report = self.base / "verification.json"
        result = cli(
            self.project,
            "verify",
            "--artifact",
            self.artifact,
            "--install",
            "--report",
            report,
        )
        self.assertTrue(json.loads(result.stdout)["installation_tested"])
        exported = self.base / "qualified"
        export(self.artifact, exported, report=report)
        descriptor = json.loads((exported / "product-descriptor.json").read_text())
        self.assertTrue(descriptor["verification"]["runtime"])
        self.assertEqual(
            report.read_bytes(), (exported / "verification-report.json").read_bytes()
        )
        individual = self.base / "different"
        package(self.workspace, individual, product="example-suite/alpha")
        with self.assertRaisesRegex(Failure, "exact artifact"):
            export(individual, self.base / "rejected", report=report)
        self.assertFalse((self.base / "rejected").exists())

    def test_batch_failure_retains_completed_member_and_same_request_resumes(self):
        with patch.dict(os.environ, {"INSTALLATION_FIXTURE_FAIL": "beta"}):
            with self.assertRaises(Failure):
                install(self.artifact, self.store, request="resume-request")
        interrupted = state_of(self.store)
        self.assertEqual(
            interrupted["requests"]["resume-request"]["status"], "interrupted"
        )
        before = interrupted["products"]["example-suite/alpha"]["payload"]
        self.assertNotIn("example-suite", interrupted["groups"])
        install(self.artifact, self.store, request="resume-request")
        self.assertEqual(
            state_of(self.store)["products"]["example-suite/alpha"]["payload"], before
        )
        with self.assertRaisesRegex(Failure, "different inputs"):
            install(
                self.artifact,
                self.store,
                product="example-suite/alpha",
                request="resume-request",
            )

    def test_corrupt_artifact_missing_dependency_and_command_conflicts(self):
        _, record = validate(self.artifact)
        path = self.artifact / next(iter(record["files"]))
        original = path.read_bytes()
        path.write_bytes(b"broken")
        with self.assertRaises(Failure):
            validate(self.artifact)
        path.write_bytes(original)
        original_record = json.loads(json.dumps(record))
        record["products"]["example-suite/beta"]["commands"] = record["products"][
            "example-suite/alpha"
        ]["commands"]
        record["products"]["example-suite/beta"]["release"] = product_hash(
            record["products"]["example-suite/beta"]
        )
        record["groups"]["example-suite"]["releases"] = {
            k: v["release"] for k, v in record["products"].items()
        }
        seal(self.artifact, record)
        with self.assertRaisesRegex(Failure, "Command conflict"):
            plan(self.artifact, self.store)
        record = original_record
        record["products"]["example-suite/beta"]["dependencies"] = ["missing"]
        record["products"]["example-suite/beta"]["release"] = product_hash(
            record["products"]["example-suite/beta"]
        )
        seal(self.artifact, record)
        with self.assertRaises(Failure):
            validate(self.artifact)
        self.assertFalse(self.store.exists())

    def test_group_pins_and_dependencies_block_incompatible_individual_update(self):
        install(self.artifact, self.store)
        self.project.joinpath("app/tool.py").write_text(
            self.project.joinpath("app/tool.py").read_text() + "\n# new release\n"
        )
        newer = self.base / "newer"
        package(Workspace(self.project), newer, product="example-suite/alpha")
        with self.assertRaisesRegex(Failure, "collection"):
            plan(newer, self.store, operation="upgrade")
        with self.assertRaisesRegex(Failure, "referenced"):
            remove(self.store, "example-suite/alpha", stopped=True)

    def test_private_and_shared_stores_coexist_with_distinct_ownership(self):
        install(self.artifact, self.store)
        private = self.base / "application" / "runtime"
        install(self.artifact, private, scope="private", owner="example-app")
        self.assertEqual(inspect(private)["scope"], "private")
        with self.assertRaises(Failure):
            install(self.artifact, private)
        remove(private, "example-suite", stopped=True)
        execute(self.store, "alpha", "--self-test")

    def test_lost_activation_restores_previous_receipt_and_owned_shims(self):
        install(self.artifact, self.store)
        original = state_of(self.store)
        helper = next((self.store / "helpers").iterdir())
        changed = json.loads(json.dumps(original))
        changed["groups"] = {}
        import operations

        actual = operations.atomic

        def fail_receipt(path, content):
            if (
                path.name == "installation-receipt.json"
                and json.loads(content)["groups"] == {}
            ):
                raise OSError("interrupted receipt publication")
            return actual(path, content)

        with patch("operations.atomic", side_effect=fail_receipt):
            with self.assertRaises(OSError):
                activate(self.store, original, changed, helper)
        self.assertEqual(original, state_of(self.store))
        execute(self.store, "beta", "--self-test")

    def test_locks_and_external_command_changes_are_preserved(self):
        install(self.artifact, self.store)
        with locked(self.store):
            with self.assertRaisesRegex(Failure, "Another installation"):
                install(self.artifact, self.store)
        name = "alpha.exe" if os.name == "nt" else "alpha"
        (self.store / "bin" / name).write_text("user changed command\n")
        with self.assertRaisesRegex(Failure, "command changed"):
            install(self.artifact, self.store)
        self.assertEqual(
            (self.store / "bin" / name).read_text(), "user changed command\n"
        )

    def test_variant_export_and_source_independent_consumer_cli(self):
        variant = self.base / "variant"
        package(
            self.workspace, variant, product="example-suite/alpha", variant="extended"
        )
        install(variant, self.store)
        self.assertTrue(json.loads(execute(self.store, "alpha").stdout)["resources"])
        exported = self.base / "export"
        export(variant, exported)
        descriptor = json.loads((exported / "product-descriptor.json").read_text())
        self.assertEqual(
            descriptor["manifest_sha256"], digest(variant / "release-manifest.json")
        )
        helper = next((self.store / "helpers").glob("*/consumer.py"))
        shutil.rmtree(self.project)
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(helper),
                "verify",
                "--artifact",
                str(exported / "artifacts"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["installation_tested"])

    def test_cli_json_events_and_invalid_options(self):
        cli(
            self.project,
            "package",
            "--variant",
            "unknown",
            "--output",
            self.base / "invalid",
            expected=1,
        )
        cli(
            self.project,
            "inspect",
            "--prefix",
            self.store,
            "--target",
            host(),
            expected=2,
        )
        result = cli(
            self.project,
            "install",
            "--artifact",
            self.artifact,
            "--prefix",
            self.store,
            "--events",
            "jsonl",
            "--request-id",
            "events-request",
        )
        events = [json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual(events[-1]["stage"], "result")
        self.assertIn("activated", [e["stage"] for e in events])

    def test_failed_replacement_upgrade_rollback_and_retention_preserve_data(self):
        artifact = self.base / "alpha"
        package(self.workspace, artifact, product="example-suite/alpha")
        install(artifact, self.store)
        original = state_of(self.store)["products"]["example-suite/alpha"]["payload"]
        data = self.store / "user-data.txt"
        data.write_text("user state")
        config = self.project / "installation.toml"
        config.write_text(
            config.read_text().replace('version = "1.0.0"', 'version = "1.1.0"')
        )
        newer = self.base / "new-alpha"
        package(
            Workspace(self.project),
            newer,
            product="example-suite/alpha",
            variant="extended",
        )
        with patch.dict(os.environ, {"INSTALLATION_FIXTURE_FAIL": "alpha"}):
            with self.assertRaises(Failure):
                install(newer, self.store, operation="upgrade")
        self.assertEqual(
            state_of(self.store)["products"]["example-suite/alpha"]["payload"], original
        )
        install(newer, self.store, operation="upgrade")
        self.assertTrue(json.loads(execute(self.store, "alpha").stdout)["resources"])
        rollback(self.store, "example-suite/alpha")
        self.assertFalse(json.loads(execute(self.store, "alpha").stdout)["resources"])
        config.write_text(
            config.read_text().replace('version = "1.1.0"', 'version = "1.2.0"')
        )
        newest = self.base / "newest-alpha"
        package(Workspace(self.project), newest, product="example-suite/alpha")
        install(newest, self.store, operation="upgrade")
        retired = prune(self.store, dry_run=True)
        self.assertEqual(len(retired["payloads"]), 1)
        with self.assertRaises(Failure):
            prune(self.store)
        prune(self.store, stopped=True)
        remove(self.store, "example-suite/alpha", stopped=True)
        self.assertEqual(data.read_text(), "user state")

    def test_generated_metadata_and_events_match_versioned_schemas(self):
        install(self.artifact, self.store)
        exported = self.base / "exported"
        report = self.base / "static-report.json"
        cli(self.project, "verify", "--artifact", self.artifact, "--report", report)
        export(self.artifact, exported, report=report)
        result = cli(
            self.project,
            "install",
            "--artifact",
            self.artifact,
            "--prefix",
            self.store,
            "--events",
            "jsonl",
        )
        events = self.base / "events.json"
        events.write_text(
            json.dumps([json.loads(x) for x in result.stdout.splitlines()])
        )
        code = (
            "import json,jsonschema,pathlib,sys,tomllib;"
            "r=pathlib.Path(sys.argv[1]);"
            "pairs=[(tomllib.loads(pathlib.Path(sys.argv[2]).read_text()),'installation.schema.json'),"
            "(json.load(open(sys.argv[3])),'product-release.schema.json'),"
            "(json.load(open(sys.argv[4])),'product-receipt.schema.json'),"
            "(json.load(open(sys.argv[5])),'product-descriptor.schema.json')];"
            "pairs.append((json.load(open(sys.argv[7])),'verification-report.schema.json'));"
            "pairs.extend((v,'operation-event.schema.json') for v in json.load(open(sys.argv[6])));"
            "[(jsonschema.validate(v,json.loads((r/'schemas'/s).read_text()))) for v,s in pairs]"
        )
        result = subprocess.run(
            [
                "uv",
                "run",
                "--locked",
                "--project",
                str(ROOT / "tools"),
                "python",
                "-B",
                "-c",
                code,
                str(ROOT),
                str(self.project / "installation.toml"),
                str(self.artifact / "release-manifest.json"),
                str(self.store / "installation-receipt.json"),
                str(exported / "product-descriptor.json"),
                str(events),
                str(report),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_source_install_and_route_ownership(self):
        cli(self.project, "help")
        planned = cli(
            self.project,
            "install",
            "--product",
            "example-suite/alpha",
            "--prefix",
            self.store,
            "--dry-run",
        )
        self.assertFalse(json.loads(planned.stdout)["executed"])
        self.assertFalse(self.store.exists())
        cli(
            self.project,
            "install",
            "--product",
            "example-suite/alpha",
            "--prefix",
            self.store,
        )
        self.assertEqual(
            state_of(self.store)["products"]["example-suite/alpha"]["origin"], "source"
        )
        with self.assertRaisesRegex(Failure, "another installation route"):
            install(self.artifact, self.store)

    def test_license_acceptance_precedes_mutation_and_tracks_changed_text(self):
        config = self.project / "installation.toml"
        config.write_text(
            config.read_text().replace(
                '[products."example-suite/alpha"]',
                '[products."example-suite/alpha"]\nlicense-acceptance = "LICENSE"',
            )
        )
        artifact = self.base / "licensed"
        package(Workspace(self.project), artifact, product="example-suite/alpha")
        license_record = plan(artifact, self.store)["licenses"][0]
        self.assertFalse(license_record["accepted"])
        with self.assertRaisesRegex(Failure, "License acceptance required"):
            install(artifact, self.store)
        self.assertFalse(self.store.exists())
        cli(
            self.project,
            "install",
            "--artifact",
            artifact,
            "--prefix",
            self.store,
            "--accept-license",
            license_record["sha256"],
        )
        self.assertTrue(plan(artifact, self.store)["licenses"][0]["accepted"])
        install(artifact, self.store, operation="reinstall")
        previous = state_of(self.store)["products"]["example-suite/alpha"]["payload"]
        config.write_text(
            config.read_text().replace('version = "1.0.0"', 'version = "1.1.0"')
        )
        license_path = self.project / "LICENSE"
        license_path.write_text(license_path.read_text() + "\nChanged license text\n")
        newer = self.base / "changed-license"
        package(Workspace(self.project), newer, product="example-suite/alpha")
        with self.assertRaisesRegex(Failure, "License acceptance required"):
            install(
                newer,
                self.store,
                operation="upgrade",
                accepted_licenses=[license_record["sha256"]],
            )
        self.assertEqual(
            state_of(self.store)["products"]["example-suite/alpha"]["payload"], previous
        )
        new_digest = plan(newer, self.store, operation="upgrade")["licenses"][0][
            "sha256"
        ]
        install(newer, self.store, operation="upgrade", accepted_licenses=[new_digest])
        self.assertTrue(plan(newer, self.store)["licenses"][0]["accepted"])
        report = self.base / "licensed-proof.json"
        cli(
            self.project, "verify", "--artifact", newer, "--install", "--report", report
        )
        self.assertTrue(json.loads(report.read_text())["installation_tested"])

    def test_platform_runtime_matrix_packages_without_fetching(self):
        config = self.project / "installation.toml"
        text = config.read_text().replace(
            '[products."example-suite/alpha"]',
            '[products."example-suite/alpha"]\nruntimes = ["python-runtime"]',
        )
        text += '\n[runtimes.python-runtime]\nrole="python"\nversion="3.14"\n'
        text += '[runtimes.python-runtime.targets."' + host() + '"]\n'
        text += (
            'url="https://example.invalid/pinned-python.tar.gz"\nsha256="'
            + "a" * 64
            + '"\nexecutable="bin/python3"\n'
        )
        config.write_text(text)
        workspace = Workspace(self.project)
        self.assertEqual(workspace.runtime("python-runtime", host())["target"], host())
        artifact = self.base / "runtime-release"
        package(workspace, artifact, product="example-suite/alpha")
        _, manifest = validate(artifact)
        self.assertEqual(manifest["runtimes"]["python-runtime"]["sha256"], "a" * 64)


class RuntimeContracts(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows native launcher ownership")
    def test_native_helper_uses_owned_receipt_and_rejects_orphans_and_tampering(self):
        with tempfile.TemporaryDirectory(
            prefix="native helper ownership "
        ) as temporary:
            root = Path(temporary)
            write_json(
                root / ".aixand-store.json",
                {
                    "schema": 2,
                    "origin": "artifact-helper",
                    "scope": "shared",
                    "owner": "user",
                },
            )
            orphan = root / "helpers/000-orphan/command-launcher.exe"
            orphan.parent.mkdir(parents=True)
            orphan.write_bytes(b"unrelated cached launcher")
            owned = root / "helpers/999-owned/command-launcher.exe"
            owned.parent.mkdir()
            content = b"current owned native launcher"
            owned.write_bytes(content)
            state = empty_state("shared", "user")
            state["shims"] = {
                "tool.exe": {
                    "file": owned.relative_to(root).as_posix(),
                    "sha256": digest(owned),
                    "size": len(content),
                }
            }
            write_json(root / "installation-receipt.json", state)
            copied = helper_copy(root)
            self.assertEqual((copied / "command-launcher.exe").read_bytes(), content)
            owned.write_bytes(b"tampered")
            with self.assertRaisesRegex(Failure, "Native launcher changed"):
                helper_copy(root)
            owned.write_bytes(content)
            state["shims"] = {}
            write_json(root / "installation-receipt.json", state)
            with self.assertRaisesRegex(Failure, "Missing owned native"):
                helper_copy(root)

    @unittest.skipUnless(os.name == "nt", "Windows long wheel paths")
    def test_deep_wheel_files_are_installed_verified_and_tamper_checked(self):
        with tempfile.TemporaryDirectory(prefix="deep wheel 世界 ") as temporary:
            base = Path(temporary)
            store = base / ("store-" + "x" * max(1, 103 - len(str(base))))
            wheel = base / "fixture_deep_paths-1.0.0-py3-none-any.whl"
            info = "fixture_deep_paths-1.0.0.dist-info"
            notice = info + "/licenses/" + "nested/" * 8 + "NOTICE"
            resource = "schemas/draft202012/vocabularies/registry/format-annotation"
            members = {
                "fixture_deep_paths/__init__.py": (
                    "from importlib.resources import files\nvalue = 'verified'\n"
                    "def main():\n"
                    f"    assert files(__package__).joinpath({resource!r}).read_text(encoding='utf-8') == 'schema verified'\n"
                    "    print(value)\n"
                ).encode(),
                "fixture_deep_paths/" + resource: b"schema verified",
                info
                + "/METADATA": b"Metadata-Version: 2.1\nName: fixture-deep-paths\nVersion: 1.0.0\n",
                info
                + "/WHEEL": b"Wheel-Version: 1.0\nGenerator: fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
                info
                + "/entry_points.txt": b"[console_scripts]\nfixture-deep = fixture_deep_paths:main\n",
                notice: b"original deep license bytes\n",
            }
            record = "\n".join(
                name + ",," + str(len(data)) for name, data in members.items()
            )
            members[info + "/RECORD"] = (record + "\n" + info + "/RECORD,,\n").encode()
            with zipfile.ZipFile(wheel, "w") as archive:
                for name, data in members.items():
                    archive.writestr(name, data)
            product = {
                "id": "deep-fixture",
                "release": "a" * 64,
                "adapter": "hybrid",
                "files": {
                    "wheelhouse/" + wheel.name: {
                        "artifact": wheel.name,
                        "executable": False,
                    }
                },
                "python": sys.version.split()[0],
                "commands": {},
                "extras": {},
                "runtime_records": {},
                "verification": [
                    [
                        "{python}",
                        "-I",
                        "-B",
                        "-c",
                        "import fixture_deep_paths; fixture_deep_paths.main()",
                    ]
                ],
            }
            try:
                entry = prepare(store, base, product, {}, sys.executable)
                payload = store / entry["payload"]
                logical = "env/Lib/site-packages/" + notice
                self.assertGreater(len(str(payload / logical)), 260)
                self.assertLess(
                    len(
                        str(
                            payload
                            / "env/Lib/site-packages/fixture_deep_paths"
                            / resource
                        )
                    ),
                    260,
                )
                self.assertIn(logical, payload_inventory(payload))
                self.assertEqual(
                    filesystem_path(payload / logical).read_bytes(), members[notice]
                )
                self.assertFalse(entry["python"].startswith("\\\\?\\"))
                result = subprocess.run(
                    [str(payload / "env/Scripts/fixture-deep.exe")],
                    capture_output=True,
                    check=True,
                    timeout=30,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertEqual(result.stdout.strip(), b"verified")
                probe(store, entry)
                filesystem_path(payload / logical).write_bytes(b"tampered")
                with self.assertRaisesRegex(Failure, "payload changed"):
                    probe(store, entry)
            finally:
                if filesystem_path(store).exists():
                    shutil.rmtree(filesystem_path(store))

    @unittest.skipUnless(os.name == "nt", "Windows file sharing")
    def test_atomic_receipt_waits_for_reader_and_keeps_original_until_commit(self):
        with tempfile.TemporaryDirectory(prefix="atomic receipt ") as temporary:
            root = Path(temporary)
            target = root / "installation-receipt.json"
            target.write_bytes(b"original")
            started = threading.Event()

            def update():
                started.set()
                atomic(target, b"committed")

            with ThreadPoolExecutor(max_workers=1) as workers:
                with target.open("rb") as reader:
                    future = workers.submit(update)
                    self.assertTrue(started.wait(5))
                    with self.assertRaises(TimeoutError):
                        future.result(timeout=0.1)
                    self.assertEqual(reader.read(), b"original")
                future.result(timeout=5)
            self.assertEqual(target.read_bytes(), b"committed")
            self.assertEqual(list(root.glob("*.tmp")), [])

    def test_bootstrap_downloads_verified_interpreter_and_installs_without_python_on_path(
        self,
    ):
        from bootstrap import generate

        with tempfile.TemporaryDirectory(
            prefix="bootstrap contracts 世界 "
        ) as temporary:
            base = Path(temporary)
            source = Path(sys.base_prefix)
            archive_path = base / (
                "runtime.zip" if os.name == "nt" else "runtime.tar.gz"
            )
            selected = {}
            if os.name == "nt":
                for path in source.iterdir():
                    if path.is_file() and path.suffix.lower() in {".exe", ".dll"}:
                        selected[path.name] = path
                directories = [source / "Lib", source / "DLLs"]
                executable = "python.exe"
            else:
                selected["bin/python3"] = Path(sys.executable).resolve()
                if (source / "Python").is_file():
                    selected["Python"] = source / "Python"
                directories = [source / "lib"]
                executable = "bin/python3"
            for directory in directories:
                for parent, dirs, files in os.walk(directory):
                    dirs[:] = [
                        d
                        for d in dirs
                        if d
                        not in {
                            "site-packages",
                            "__pycache__",
                            "test",
                            "tests",
                            "idlelib",
                            "tkinter",
                        }
                    ]
                    for filename in files:
                        path = Path(parent) / filename
                        if path.is_file() and not filename.endswith((".pyc", ".a")):
                            selected[path.relative_to(source).as_posix()] = (
                                path.resolve()
                            )
            self.assertTrue(selected)
            if os.name == "nt":
                with zipfile.ZipFile(
                    archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=1
                ) as archive:
                    for name, path in selected.items():
                        archive.write(path, name)
            else:
                with tarfile.open(
                    archive_path, "w:gz", compresslevel=1, dereference=True
                ) as archive:
                    for name, path in selected.items():
                        archive.add(path, arcname=name, recursive=False)

            class Handler(http.server.SimpleHTTPRequestHandler):
                def log_message(self, *args):
                    pass

            server = http.server.ThreadingHTTPServer(
                ("127.0.0.1", 0), functools.partial(Handler, directory=str(base))
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                record = {
                    "role": "helper",
                    "version": ".".join(map(str, sys.version_info[:3])),
                    "target": host(),
                    "url": f"http://127.0.0.1:{server.server_port}/{archive_path.name}",
                    "sha256": digest(archive_path),
                    "executable": executable,
                    "format": "zip" if os.name == "nt" else "tar",
                }
                output = base / "bootstrap"
                generate(record, output, allow_local=True)
                project = fixture("product-workspace", base / "source")
                artifact = base / "product"
                package(Workspace(project), artifact, product="example-suite/alpha")
                tools = base / "system-tools"
                tools.mkdir()
                if os.name != "nt":
                    for name in (
                        "uname",
                        "mkdir",
                        "mktemp",
                        "rm",
                        "rmdir",
                        "mv",
                        "tar",
                        "gzip",
                        "sha256sum",
                        "shasum",
                    ):
                        if shutil.which(name):
                            (tools / name).symlink_to(shutil.which(name))
                    (tools / "curl").symlink_to(shutil.which("curl"))
                    command = ["/bin/sh", str(output / "bootstrap.sh")]
                    path = str(tools)
                else:
                    system = Path(os.environ["SystemRoot"]) / "System32"
                    command = [
                        str(system / "WindowsPowerShell/v1.0/powershell.exe"),
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(output / "bootstrap.ps1"),
                    ]
                    path = str(system)
                store = base / "installed"
                environment = {
                    **os.environ,
                    "PATH": path,
                    "AIXAND_INSTALLER_CACHE": str(base / "installer-cache"),
                }
                result = subprocess.run(
                    [
                        *command,
                        "install",
                        "--artifact",
                        str(artifact),
                        "--prefix",
                        str(store),
                    ],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                self.assertEqual(
                    result.returncode, 0, result.stdout + result.stderr[-5000:]
                )
                state = state_of(store)
                self.assertIn(
                    "installer-cache",
                    state["products"]["example-suite/alpha"]["python"],
                )
                # A product's own runtime must remain immutable and supply its
                # command shims after setup's helper interpreter is gone.
                bundled_archive = project / archive_path.name
                shutil.copyfile(archive_path, bundled_archive)
                config = project / "installation.toml"
                config.write_text(
                    config.read_text().replace(
                        '[products."example-suite/alpha"]',
                        '[products."example-suite/alpha"]\nruntimes = ["python"]',
                    )
                    + "\n[runtimes.python]\n"
                    + "\n".join(
                        f"{key} = {json.dumps(value)}"
                        for key, value in {
                            **{k: v for k, v in record.items() if k != "url"},
                            "role": "python",
                            "path": archive_path.name,
                        }.items()
                    )
                    + "\n"
                )
                bundled = base / "bundled-product"
                package(Workspace(project), bundled, product="example-suite/alpha")
                shutil.rmtree(project)
                result = subprocess.run(
                    [*command, "inspect", "--prefix", str(store)],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                owned = base / "owned-runtime-store"
                install(bundled, owned)
                entry = state_of(owned)["products"]["example-suite/alpha"]
                self.assertTrue(
                    Path(entry["python"]).is_relative_to(owned / "runtimes")
                )
                shim = (
                    owned
                    / "bin"
                    / ("alpha.aixand-command" if os.name == "nt" else "alpha")
                )
                self.assertIn(str(owned / "runtimes"), shim.read_text())
                result = subprocess.run(
                    [
                        owned / "bin" / ("alpha.exe" if os.name == "nt" else "alpha"),
                        "--self-test",
                    ],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                install(bundled, owned, operation="reinstall")
                inspect(owned)
                if os.name != "nt":
                    self.assertFalse(list((base / "installer-cache").glob("*.lock")))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_runtime_archive_integrity_internal_links_and_unsafe_links(self):
        with tempfile.TemporaryDirectory(prefix="runtime contracts ") as temporary:
            root = Path(temporary)
            archive = root / "runtime.tar"
            with tarfile.open(archive, "w") as stream:
                data = b"#!/bin/sh\nexit 0\n"
                entry = tarfile.TarInfo("bin/runtime")
                entry.size = len(data)
                entry.mode = 0o755
                stream.addfile(entry, io.BytesIO(data))
                link = tarfile.TarInfo("bin/alias")
                link.type = tarfile.SYMTYPE
                link.linkname = "runtime"
                stream.addfile(link)
            record = {
                "artifact": "runtime.tar",
                "sha256": digest(archive),
                "executable": "bin/runtime",
                "format": "tar",
            }
            result = provision(root / "store", record, root)
            self.assertTrue(result.is_file())
            self.assertEqual(
                result.read_bytes(), result.with_name("alias").read_bytes()
            )
            result.write_text("corrupt")
            with self.assertRaisesRegex(Failure, "runtime changed"):
                provision(root / "store", record, root)
            with tarfile.open(archive, "w") as stream:
                link = tarfile.TarInfo("bad")
                link.type = tarfile.SYMTYPE
                link.linkname = "../escape"
                stream.addfile(link)
            destination = root / "unpacked"
            destination.mkdir()
            with self.assertRaisesRegex(Failure, "escapes"):
                unpack(archive, destination, record)
            self.assertFalse((root / "escape").exists())

    def test_deep_runtime_inventory_reuse_still_detects_tampering(self):
        with tempfile.TemporaryDirectory(prefix="runtime deep path ") as temporary:
            root = Path(temporary)
            archive = root / "runtime.tar"
            member = "lib/" + "cached-module-" + "x" * 130 + ".pyc"
            with tarfile.open(archive, "w") as stream:
                for name, data in [
                    ("bin/runtime", b"#!/bin/sh\nexit 0\n"),
                    (member, b"verified"),
                ]:
                    entry = tarfile.TarInfo(name)
                    entry.size = len(data)
                    entry.mode = 0o755 if name == "bin/runtime" else 0o644
                    stream.addfile(entry, io.BytesIO(data))
            record = {
                "artifact": "runtime.tar",
                "sha256": digest(archive),
                "executable": "bin/runtime",
                "format": "tar",
            }
            store = root / "store"
            cleanup = Path("\\\\?\\" + str(store)) if os.name == "nt" else store
            try:
                result = provision(store, record, root)
                self.assertEqual(
                    result, store / "runtimes" / record["sha256"] / "bin/runtime"
                )
                self.assertEqual(provision(store, record, root), result)
                deep = result.parent.parent / member
                if os.name == "nt":
                    self.assertGreater(len(str(deep)), 260)
                    deep = Path("\\\\?\\" + str(deep))
                deep.write_bytes(b"tampered")
                with self.assertRaisesRegex(Failure, "runtime changed"):
                    provision(store, record, root)
            finally:
                if cleanup.exists():
                    shutil.rmtree(cleanup)


class EcosystemProducts(unittest.TestCase):
    def test_real_embedded_python_loads_independent_installed_sdk(self):
        with tempfile.TemporaryDirectory(prefix="embedded Python 世界 ") as temporary:
            base = Path(temporary)
            project = fixture("hybrid-product", base / "source")
            artifact = base / "release"
            package(Workspace(project), artifact)
            store = base / "store"
            install(artifact, store)
            shutil.rmtree(project)
            self.assertIn(
                "embedded Python verified", execute(store, "fixture-embedded").stdout
            )

    def test_python_multiwheel_installs_offline_and_sdk_exports_independently(self):
        with tempfile.TemporaryDirectory(prefix="python product 世界 ") as temporary:
            base = Path(temporary)
            project = fixture("python-products", base / "source")
            workspace = Workspace(project)
            artifact = base / "release"
            package(workspace, artifact)
            store = base / "store"
            sdk = base / "sdk"
            package(workspace, sdk, component="library")
            result = cli(project, "verify", "--artifact", sdk, "--install")
            self.assertFalse(json.loads(result.stdout)["global_commands_created"])
            install(artifact, store)
            shutil.rmtree(project)
            result = execute(store, "fixture-python-product", "--self-test")
            self.assertIn("independent Python resource", result.stdout)
            payload = next((store / "payloads/python-fixture/tool").iterdir())
            self.assertTrue((payload / "env/pyvenv.cfg").is_file())

    def test_native_bundle_runs_without_python_or_rust_on_command_path(self):
        with tempfile.TemporaryDirectory(prefix="native product 世界 ") as temporary:
            base = Path(temporary)
            project = fixture("native-bundle", base / "source")
            artifact = base / "release"
            package(Workspace(project), artifact)
            store = base / "store"
            install(artifact, store)
            entry = state_of(store)["products"]["native-fixture"]
            binary = (
                store
                / entry["payload"]
                / "bin"
                / ("fixture-native.exe" if os.name == "nt" else "fixture-native")
            )
            shutil.rmtree(project)
            env = {
                **os.environ,
                "PATH": ""
                if os.name != "nt"
                else os.environ.get("SystemRoot", "C:/Windows") + "/System32",
            }
            result = subprocess.run(
                [binary, "--self-test"],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("complete native bundle", result.stdout)


if __name__ == "__main__":
    unittest.main()
