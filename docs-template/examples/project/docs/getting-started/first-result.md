# Read the first readiness result

Run the fixture once and confirm its output. Use Python 3.11 or newer from the
example project root, which contains `tools/status.py`.

## Run the command

```sh
python3 tools/status.py
```

Expected stdout:

```text
ready
```

The command exits zero. It reads a synthetic argument default and creates no
files, network connections, or services. No cleanup is required.

## Check a setup failure

If Python cannot open the file, confirm that your directory contains
[tools/status.py](../../tools/status.py). If Python is unavailable, use your
platform's supported Python installation method before continuing.

Continue with [selecting a busy result](../guides/select-state.md), or look up
the [command contract](../reference/command.md).
