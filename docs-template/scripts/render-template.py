#!/usr/bin/env python3
"""Render one selected template into a new file; never overwrite or execute it."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

TOKEN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def render(source: str, values: dict[str, str]) -> str:
    required = set(TOKEN.findall(source))
    missing, extra = required - values.keys(), values.keys() - required
    if missing:
        raise ValueError("missing values: " + ", ".join(sorted(missing)))
    if extra:
        raise ValueError("unused values: " + ", ".join(sorted(extra)))
    if any(not value.strip() or "\x00" in value for value in values.values()):
        raise ValueError("replacement values must be nonempty and contain no NUL")
    result = TOKEN.sub(lambda match: values[match[1]], source)
    if TOKEN.search(result):
        raise ValueError("replacement introduced an unresolved template token")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args(argv)
    try:
        values: dict[str, str] = {}
        for assignment in args.set:
            key, separator, value = assignment.partition("=")
            if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
                raise ValueError("--set needs an uppercase KEY=VALUE")
            if key in values:
                raise ValueError(f"duplicate value: {key}")
            values[key] = value
        content = render(args.template.read_text(encoding="utf-8"), values)
        if args.destination.exists() or args.destination.is_symlink():
            raise FileExistsError(f"destination already exists: {args.destination}")
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with args.destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
        print(f"Created {args.destination}; complete author instructions and verify the content before publication.")
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
