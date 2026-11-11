# Select a busy readiness result

Use this task to exercise a nonready result. Requires Python 3.11 or newer.
Run from the example project root containing `tools/status.py`.

## Select and verify the result

```sh
python3 tools/status.py --state busy
```

The command prints `busy` and exits **1**. That exit code is the intended result
for this input. It does not mean that the fixture inspected an unhealthy service.

The state applies only to this invocation. To obtain the default result again:

```sh
python3 tools/status.py
```

Expect `ready` and exit code zero. No persisted setting or resource needs cleanup.

## Correct an invalid value

An unsupported value produces an argument error and exit code **2**. Select
`ready` or `busy`; see the [reference](../reference/command.md) for exact behavior.

[First result](../getting-started/first-result.md) · [Documentation index](../README.md)
