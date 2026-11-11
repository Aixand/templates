#!/usr/bin/env python3
"""Check authored files, profile renders, schemas, pins, and workflow structure."""

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

import jsonschema
import yaml

from render_fixture import render

ROOT = Path(__file__).resolve().parents[1]
SKIP = {
    ".git",
    ".venv",
    "target",
    "dist",
    "build",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
}


def authored_files():
    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = [
            name for name in dirs if name not in SKIP and not name.endswith(".egg-info")
        ]
        for name in names:
            path = Path(directory) / name
            if not path.is_symlink():
                yield path


def main():
    from update_v2_schemas import main as check_product_schemas

    check_product_schemas()
    subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts/checks/check-repository-files.py")],
        cwd=ROOT,
        check=True,
    )
    schemas = {
        p.stem: json.loads(p.read_text()) for p in (ROOT / "schemas").glob("*.json")
    }
    for schema in schemas.values():
        jsonschema.Draft202012Validator.check_schema(schema)
    config_schema = schemas["installation.schema"]
    configs = [
        ROOT / "installation.toml",
        *(ROOT / "tests/fixtures").glob("*/installation.toml"),
    ]
    for config in configs:
        jsonschema.validate(tomllib.loads(config.read_text()), config_schema)
    file_count = 0
    link_count = 0
    for path in authored_files():
        file_count += 1
        content = path.read_text()
        if not content.endswith("\n") or "\r" in content:
            raise ValueError(f"Line endings/final newline: {path.relative_to(ROOT)}")
        if any(line.rstrip() != line for line in content.splitlines()):
            raise ValueError(f"Trailing whitespace: {path.relative_to(ROOT)}")
        if path.suffix == ".py":
            ast.parse(content, filename=str(path))
        if path.suffix == ".md":
            if content.count("```") % 2:
                raise ValueError(f"Unbalanced fences: {path}")
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", content):
                if target.startswith(("https://", "http://", "mailto:")):
                    continue
                target = target.split("#", 1)[0]
                if target and not (path.parent / target).exists():
                    raise ValueError(f"Missing relative link: {path} -> {target}")
                link_count += 1
    with tempfile.TemporaryDirectory(
        prefix="installation-profile-renders-"
    ) as temporary:
        for profile in [
            "python-library",
            "python-tool",
            "rust-library",
            "rust-cli",
            "custom",
            "workspace",
        ]:
            project = render(
                {"custom": "python-library", "workspace": "product-workspace"}.get(
                    profile, profile
                ),
                Path(temporary) / profile,
            )
            sample = ROOT / "profiles" / profile / "installation.toml.example"
            replacements = {
                "PYTHON_VERSION": "3.14",
                "IMPORT_NAME": "fixture_library",
                "LIBRARY_ASSERTION": "assert fixture_library.greet('world') == 'Hello, world!'",
                "COMMAND_NAME": "fixture-tool"
                if profile.startswith("python")
                else "fixture-rust-cli",
                "RUST_CONSUMER_MAIN": 'fn main() { assert_eq!(fixture_rust_library::greet("world"), "Hello, world!"); }',
                "PROJECT_NAME": "example-web",
            }
            text = sample.read_text()
            for key, value in replacements.items():
                text = text.replace("{{" + key + "}}", value)
            if "{{" in text:
                raise ValueError(f"Unrendered profile: {profile}")
            (project / "installation.toml").write_text(text)
            if profile.startswith("rust-"):
                toolchain = (
                    (ROOT / "profiles/rust-toolchain.toml.example")
                    .read_text()
                    .replace("{{RUST_VERSION}}", "1.98.0")
                )
                (project / "rust-toolchain.toml").write_text(toolchain)
                if tomllib.loads(toolchain)["toolchain"]["channel"] != "1.98.0":
                    raise ValueError("Rust toolchain profile did not render")
            jsonschema.validate(tomllib.loads(text), config_schema)
            command = [
                sys.executable,
                "-B",
                str(project / "scripts/dev/cli.py"),
                "--project",
                str(project),
                "help",
            ]
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
            sys.path.insert(0, str(ROOT / "files/scripts/dev"))
            from core import Project

            if profile == "workspace":
                from catalog import Workspace

                Workspace(project)
            else:
                Project(project)
    workflows = [
        *(ROOT / ".github/workflows").glob("*.yml"),
        *(ROOT / "examples/workflows").glob("*.yml.example"),
    ]
    for path in workflows:
        content = path.read_text()
        workflow = yaml.load(content, Loader=yaml.BaseLoader)
        if "pull_request_target" in workflow.get("on", {}):
            raise ValueError(
                f"Project helper workflow cannot use pull_request_target: {path}"
            )
        if workflow.get("permissions") != {"contents": "read"}:
            raise ValueError(f"Workflow needs read-only defaults: {path}")
        if path.name.startswith("publish-") and set(workflow["on"]) != {"push"}:
            raise ValueError(
                f"Release examples must use intentional tag pushes: {path}"
            )
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                action = step.get("uses")
                if action and not re.fullmatch(r"[^@]+@[0-9a-f]{40}", action):
                    raise ValueError(f"Unpinned action: {path}: {action}")
    for license in (ROOT / "tests/fixtures").glob("*/LICENSE"):
        if license.read_bytes() != (ROOT / "LICENSE").read_bytes():
            raise ValueError(f"Fixture license differs: {license}")
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", "files/scripts", "scripts", "tests"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "files/scripts",
            "scripts",
            "tests",
        ],
        cwd=ROOT,
        check=True,
    )
    print(
        f"Checked {file_count} source documents/files, {link_count} relative links, 6 rendered profiles, schemas, pins, and {len(workflows)} workflows"
    )


if __name__ == "__main__":
    main()
