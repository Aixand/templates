#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check PR commit certifications without checking out or executing PR code."""

import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def identity(value):
    match = re.fullmatch(r"([^<>\r\n]+?)\s+<([^<>\s]+@[^<>\s]+)>", value.strip())
    if not match:
        return None
    return match[1].strip(), match[2].casefold()


def commit_errors(commit):
    """Require the author and every declared co-author to certify in trailers."""
    details = commit["commit"]
    author = details["author"]
    author_id = identity(f"{author['name']} <{author['email']}>")
    parsed = subprocess.run(
        ["git", "-c", "trailer.separators=:", "interpret-trailers", "--parse"],
        input=details["message"], text=True, capture_output=True, check=True,
    ).stdout
    signers, coauthors, errors = set(), set(), []
    for line in parsed.splitlines():
        key, separator, value = line.partition(":")
        if not separator or key.casefold() not in {"signed-off-by", "co-authored-by"}:
            continue
        person = identity(value)
        if person is None:
            errors.append("malformed sign-off or co-author trailer")
        elif key.casefold() == "signed-off-by":
            signers.add(person)
        else:
            coauthors.add(person)
    if author_id is None or author_id not in signers:
        errors.append("missing sign-off matching the commit author's name and email")
    if coauthors - signers:
        errors.append("a co-author is missing their matching sign-off")
    return errors


def inspect_pull_request(api, number, expected_head):
    """Fail closed if the API cannot provide the entire expected commit set."""
    path = f"pulls/{number}"
    before = api(path)
    if before["head"]["sha"] != expected_head:
        raise ValueError("PR head changed; rerun the check for the current head")
    count = before["commits"]
    if not isinstance(count, int) or not 1 <= count <= 250:
        raise ValueError("the commits API supports 1–250 PR commits; split larger PRs")
    commits = []
    for page in range(1, math.ceil(count / 100) + 1):
        commits.extend(api(f"{path}/commits?per_page=100&page={page}"))
    shas = [item["sha"] for item in commits]
    if (len(shas) != count or len(set(shas)) != count or shas[-1] != expected_head
            or any(not re.fullmatch(r"[0-9a-f]{40}", sha) for sha in shas)):
        raise ValueError("incomplete or changed PR commit list; rerun the check")
    failures = [(item["sha"], commit_errors(item)) for item in commits]
    after = api(path)
    if (after["head"]["sha"] != expected_head or after["commits"] != count
            or after["base"]["sha"] != before["base"]["sha"]):
        raise ValueError("PR changed during validation; rerun the check")
    return [(sha, errors) for sha, errors in failures if errors]


def main():
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request_target":
        raise ValueError("this checker requires a pull_request_target event")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    repository = os.environ["GITHUB_REPOSITORY"]
    number = event["number"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid repository")
    if type(number) is not int or number < 1:
        raise ValueError("invalid pull request number")

    def api(path):
        request = Request(
            f"https://api.github.com/repos/{repository}/{path}",
            headers={
                "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "open-source-dco-check",
            },
        )
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    failures = inspect_pull_request(api, number, event["pull_request"]["head"]["sha"])
    for sha, errors in failures:
        # Only validated hex SHAs and fixed messages reach the Actions log.
        print(f"{sha[:12]}: {'; '.join(errors)}")
    if failures:
        print("DCO check failed. Read CONTRIBUTING.md and DCO before signing.")
        return 1
    print("DCO sign-off passed for every PR commit.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HTTPError as error:
        print(f"DCO check could not read GitHub metadata (HTTP {error.code}).", file=sys.stderr)
    except (URLError, OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError):
        print("DCO check could not validate the complete PR. Check API access and rerun; "
              "PRs must contain 1–250 commits.", file=sys.stderr)
    raise SystemExit(1)
