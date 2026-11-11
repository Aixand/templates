"""Synthetic executable for collection, restart, argument, and failure tests."""

import json
import os
from pathlib import Path
import sys

name = sys.argv[1] if len(sys.argv) > 1 else "tool"
if "--self-test" in sys.argv:
    if os.environ.get("INSTALLATION_FIXTURE_FAIL") == name:
        raise SystemExit(17)
    print("verified " + name)
elif "--fail" in sys.argv:
    raise SystemExit(23)
elif "--wait" in sys.argv:
    import signal
    import time

    ready = Path(sys.argv[sys.argv.index("--wait") + 1])

    def stop(signum, frame):
        ready.with_suffix(".stopped").write_text("clean shutdown")
        raise SystemExit(0)

    for value in (signal.SIGINT, signal.SIGTERM):
        signal.signal(value, stop)
    if os.name == "nt":
        signal.signal(signal.SIGBREAK, stop)
    ready.write_text(str(os.getpid()))
    while True:
        time.sleep(0.05)
else:
    print(
        json.dumps(
            {
                "name": name,
                "arguments": sys.argv[2:],
                "resources": (Path(__file__).parents[1] / "share/extra.txt").exists(),
            }
        )
    )
