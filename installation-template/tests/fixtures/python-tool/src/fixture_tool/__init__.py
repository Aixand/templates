import argparse
from importlib.metadata import version
from importlib.resources import files

import idna


def describe(domain):
    label = files(__package__).joinpath("greeting.txt").read_text().strip()
    return label + ": " + idna.encode(domain).decode("ascii")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", action="version", version=version("fixture-python-tool")
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        assert describe("bücher.example") == "Installed resource: xn--bcher-kva.example"
        print("Python tool dependency and resource verified")
