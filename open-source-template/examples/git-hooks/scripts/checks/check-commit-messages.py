#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the configured commit-msg hook on every commit introduced by a PR."""

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def commits_between(base, head):
    # Accept resolved object IDs, never options or user-supplied revision syntax.
    for value in (base, head):
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
            raise ValueError("Pass full commit IDs for the PR base and head")
        subprocess.run(["git", "cat-file", "-e", f"{value}^{{commit}}"],
                       check=True, capture_output=True)
    subprocess.run(["git", "merge-base", base, head], check=True, capture_output=True)
    commits = subprocess.check_output(
        ["git", "rev-list", "--reverse", f"{base}..{head}"], text=True,
    ).splitlines()
    if not commits:
        raise ValueError("The PR range contains no commits")
    return commits


def check_commits(base, head):
    failed = False
    with tempfile.TemporaryDirectory(prefix="commit-messages-") as directory:
        message = Path(directory) / "COMMIT_EDITMSG"
        for sha in commits_between(base, head):
            # Keep message contents out of workflow commands and shell interpolation.
            message.write_bytes(subprocess.check_output(["git", "show", "-s", "--format=%B", sha]))
            result = subprocess.run(
                [sys.executable, "-m", "pre_commit", "run", "conventional-pre-commit",
                 "--hook-stage", "commit-msg", "--commit-msg-filename", str(message)],
                capture_output=True,
            )
            if result.returncode:
                failed = True
                print(f"{sha[:12]}: commit-message check failed")
    if failed:
        print("Use type(scope): description, such as fix(api): handle missing input. "
              "Run the configured commit-msg hook locally for details.")
    else:
        print("Commit-message checks passed for every introduced commit.")
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", help="Full PR base commit ID")
    parser.add_argument("head", help="Full PR head commit ID")
    args = parser.parse_args()
    try:
        return check_commits(args.base, args.head)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Cannot validate commit messages: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
