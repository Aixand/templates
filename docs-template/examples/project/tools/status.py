#!/usr/bin/env python3
"""Print a caller-selected synthetic readiness value."""
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", choices=("ready", "busy"), default="ready")
    args = parser.parse_args(argv)
    print(args.state)
    return 0 if args.state == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
