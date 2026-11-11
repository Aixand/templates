#!/usr/bin/env python3
"""Render a disposable fixture, never merge fixture application code into a project."""

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def render(name, destination):
    source = ROOT / "tests/fixtures" / name
    if not source.is_dir():
        raise ValueError(f"Unknown fixture: {name}")
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Fixture destination must not already exist")
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            "target", ".venv", "__pycache__", "dist", "build", "*.egg-info"
        ),
    )
    for name in ["dev.sh", "dev.ps1"]:
        shutil.copyfile(ROOT / "files" / name, destination / name)
    (destination / "dev.sh").chmod(0o755)
    shutil.copytree(
        ROOT / "files/scripts",
        destination / "scripts",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copyfile(ROOT / "files/gitignore.example", destination / ".gitignore")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture",
        choices=sorted(
            p.name for p in (ROOT / "tests/fixtures").iterdir() if p.is_dir()
        ),
    )
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(render(args.fixture, args.destination))
