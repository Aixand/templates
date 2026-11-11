#!/usr/bin/env python3
"""Install a checksum-pinned Linux x86_64 linter into an explicitly selected path."""

import argparse
import hashlib
import io
from pathlib import Path
import platform
import tarfile
from urllib.request import urlopen

VERSION = "1.7.7"
SHA256 = "023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757"
URL = f"https://github.com/rhysd/actionlint/releases/download/v{VERSION}/actionlint_{VERSION}_linux_amd64.tar.gz"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        parser.error(
            "This bootstrap is Linux x86_64 only; install actionlint for your platform separately"
        )
    if args.output.exists() or args.output.is_symlink():
        parser.error("Output must not already exist")
    with urlopen(URL, timeout=30) as response:
        data = response.read(16 * 1024 * 1024)
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("actionlint archive checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        entry = archive.getmember("actionlint")
        if not entry.isfile():
            raise ValueError("Expected a regular actionlint executable")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with (
            archive.extractfile(entry) as source,
            args.output.open("xb") as destination,
        ):
            destination.write(source.read())
    args.output.chmod(0o755)
    print(args.output)


if __name__ == "__main__":
    main()
