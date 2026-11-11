"""Command versions, PATH precedence, and Windows resource qualification."""

import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "files/scripts/dev"))
sys.path.insert(0, str(ROOT / "scripts"))

import command_environment as commands  # noqa: E402
from core import Failure, write_json  # noqa: E402
from windows_metadata import resource, stamp, version_parts  # noqa: E402


class CommandEnvironment(unittest.TestCase):
    def test_keep_preserves_existing_precedence_and_prefer_moves_only_installed_directory(
        self,
    ):
        self.assertEqual(
            commands.ordered_path(["/old", "/other"], "/new", "keep"),
            ["/old", "/other", "/new"],
        )
        self.assertEqual(
            commands.ordered_path(["/old", "/new", "/other"], "/new", "keep"),
            ["/old", "/new", "/other"],
        )
        self.assertEqual(
            commands.ordered_path(["/old", "/new", "/other", "/new"], "/new", "prefer"),
            ["/new", "/old", "/other"],
        )
        with self.assertRaises(Failure):
            commands.ordered_path([], "/new", "latest")

    def test_prerelease_has_numeric_windows_version_and_preserves_product_version(self):
        self.assertEqual(version_parts("0.1.0-beta"), (0, 1, 0, 0))
        data = resource("0.1.0-beta", "example-tool", "example-tool", launcher=True)
        self.assertEqual(struct.unpack_from("<H", data)[0], len(data))
        self.assertIn("0.1.0-beta".encode("utf-16le"), data)
        self.assertIn("example-tool command launcher".encode("utf-16le"), data)
        with self.assertRaises(Failure):
            version_parts("65536.0.0")

    @unittest.skipIf(os.name == "nt", "POSIX executable fixture")
    def test_actual_cli_versions_and_default_are_reported_for_two_separate_installs(
        self,
    ):
        with tempfile.TemporaryDirectory(prefix="command defaults 世界 ") as temporary:
            base = Path(temporary)
            old, store = base / "cargo/bin", base / "products"
            old.mkdir(parents=True)
            (store / "bin").mkdir(parents=True)
            for directory, version in ((old, "2.0.0"), (store / "bin", "0.1.0-beta")):
                executable = directory / "example-tool"
                executable.write_text(
                    f"#!/bin/sh\nprintf 'example-tool {version}\\n'\n"
                )
                executable.chmod(0o755)
            write_json(
                store / "installation-receipt.json",
                {
                    "products": {
                        "example-tool": {
                            "product": {
                                "version": "0.1.0-beta",
                                "commands": {"example-tool": {}},
                            }
                        }
                    }
                },
            )
            with patch.dict(
                os.environ, {"PATH": os.pathsep.join(map(str, (old, store / "bin")))}
            ):
                report = commands.inspect_commands(store, ["example-tool"])
                self.assertEqual(report["commands"][0]["default"]["version"], "2.0.0")
                self.assertEqual(
                    report["commands"][0]["installedVersion"], "0.1.0-beta"
                )
                self.assertTrue(report["commands"][0]["conflict"])
            with patch.dict(
                os.environ, {"PATH": os.pathsep.join(map(str, (store / "bin", old)))}
            ):
                self.assertTrue(
                    commands.inspect_commands(store, ["example-tool"])["commands"][0][
                        "default"
                    ]["managed"]
                )

            public = base / "local/bin"
            public.mkdir(parents=True)
            (public / "example-tool").symlink_to(store / "bin/example-tool")
            with patch.dict(os.environ, {"PATH": str(public)}):
                row = commands.inspect_commands(store, ["example-tool"])["commands"][0]
                self.assertTrue(row["default"]["managed"])
                self.assertFalse(row["conflict"])


@unittest.skipUnless(os.name == "nt", "Native Windows version and registry APIs")
class WindowsCommandEnvironment(unittest.TestCase):
    def test_product_metadata_command_defaults_and_cleanup_without_changing_real_user_path(
        self,
    ):
        import uuid
        import winreg
        from catalog import Workspace
        from operations import install, remove
        from releases import package
        from render_fixture import render

        real_paths = commands.windows_paths()
        key = str(Path("Software") / "Aixand" / "InstallerTests" / uuid.uuid4().hex)
        with tempfile.TemporaryDirectory(prefix="command versions 世界 ") as temporary:
            base = Path(temporary)
            project = render("product-workspace", base / "source")
            config = project / "installation.toml"
            config.write_text(
                config.read_text().replace(
                    '"3.14"', f'"{sys.version_info.major}.{sys.version_info.minor}"'
                )
            )
            artifact, store = base / "artifact", base / "products"
            package(Workspace(project), artifact)
            install(artifact, store)
            receipt = json.loads((store / "installation-receipt.json").read_text())
            old = base / "cargo/bin"
            old.mkdir(parents=True)
            new_exe = store / "bin/alpha.exe"
            old_exe = old / "alpha.exe"
            shutil.copyfile(new_exe, old_exe)
            stamp(old_exe, "2.0.0", "previous alpha", "alpha", launcher=True)
            # The native launcher must still function after adding VERSIONINFO.
            help_result = subprocess.run(
                [str(new_exe), "--help"], capture_output=True, timeout=15
            )
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            script = r"""[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
$file=Get-Item -LiteralPath $env:AIXAND_TEST_EXECUTABLE
@{numeric=[string](Get-Command -Name $file.FullName).Version;product=$file.VersionInfo.ProductVersion;description=$file.VersionInfo.FileDescription}|ConvertTo-Json -Compress
"""
            alpha = receipt["products"]["example-suite/alpha"]["product"]["version"]
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                env={**os.environ, "AIXAND_TEST_EXECUTABLE": str(new_exe)},
                capture_output=True,
                encoding="utf-8-sig",
                timeout=20,
                check=True,
            )
            metadata = json.loads(result.stdout)
            self.assertEqual(
                metadata["numeric"], ".".join(map(str, version_parts(alpha)))
            )
            self.assertEqual(metadata["product"], alpha)
            self.assertIn("command launcher", metadata["description"])
            # Packaging a native command stamps the payload before its hashes are sealed.
            shutil.copyfile(new_exe, project / "app/alpha.exe")
            native_config = (
                config.read_text()
                .replace(
                    'files = [{source = "app/tool.py", destination = "app/tool.py"}]',
                    'files = [{source = "app/alpha.exe", destination = "bin/alpha.exe"}]',
                )
                .replace(
                    '[products."example-suite/alpha"]',
                    '[products."example-suite/alpha"]\nversion = "0.1.0-beta"',
                )
                .replace(
                    'program = "app/tool.py"\nargs = ["alpha"]\nruntime = "python"',
                    'program = "bin/alpha{exe}"',
                )
            )
            config.write_text(native_config)
            native_artifact = base / "native-artifact"
            package(Workspace(project), native_artifact, product="example-suite/alpha")
            manifest = json.loads(
                (native_artifact / "release-manifest.json").read_text()
            )
            payload = (
                native_artifact
                / manifest["products"]["example-suite/alpha"]["files"]["bin/alpha.exe"][
                    "artifact"
                ]
            )
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                env={**os.environ, "AIXAND_TEST_EXECUTABLE": str(payload)},
                capture_output=True,
                encoding="utf-8-sig",
                timeout=20,
                check=True,
            )
            packaged_metadata = json.loads(result.stdout)
            self.assertEqual(packaged_metadata["numeric"], "0.1.0.0")
            self.assertEqual(packaged_metadata["product"], "0.1.0-beta")
            self.assertEqual(packaged_metadata["description"], "alpha")
            with patch.object(commands, "USER_PATH_KEY", key):
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as handle:
                        winreg.SetValueEx(
                            handle, "Path", 0, winreg.REG_EXPAND_SZ, str(old)
                        )
                    kept = commands.register(store, "keep")
                    self.assertTrue(kept["registered"])
                    report = commands.inspect_commands(store, ["alpha"])
                    self.assertEqual(
                        report["commands"][0]["default"]["path"], str(old_exe)
                    )
                    commands.register(store, "prefer")
                    report = commands.inspect_commands(store, ["alpha"])
                    self.assertEqual(
                        report["commands"][0]["default"]["path"], str(new_exe)
                    )
                    self.assertTrue(report["commands"][0]["default"]["managed"])
                finally:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
            self.assertEqual(real_paths, commands.windows_paths())
            # A versioned launcher remains a valid owned template during removal.
            remove(store, "example-suite", stopped=True)
            self.assertEqual(
                json.loads((store / "installation-receipt.json").read_text())[
                    "products"
                ],
                {},
            )


if __name__ == "__main__":
    unittest.main()
