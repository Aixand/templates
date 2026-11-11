# Look up the status command

This reference describes the [fixture implementation](../../tools/status.py) in
this checkout. Python's `argparse` owns argument parsing and usage-error output.

## Arguments and output

| Argument | Values | Default | Meaning |
| --- | --- | --- | --- |
| `--state` | `ready`, `busy` | `ready` | Synthetic value printed for this invocation |
| `--help` / `-h` | No value | Absent | Print generated help and exit zero |

| Result | Stdout | Exit code |
| --- | --- | --- |
| State is `ready` | `ready` followed by a newline | 0 |
| State is `busy` | `busy` followed by a newline | 1 |
| Invalid arguments | No state value; usage error goes to stderr | 2 |

The command performs no health probe and retains no state. It has no network,
retry, or cancellation contract beyond normal local process execution.

[Working task](../guides/select-state.md) · [Architecture](../architecture/README.md)
