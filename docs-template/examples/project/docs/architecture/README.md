# Understand the status fixture

This view explains argument handling and results in one Python process. The
[implementation](../../tools/status.py) is the authoritative source.

```mermaid
flowchart LR
    accTitle: Status fixture input and result
    accDescr: Python argparse validates command arguments. The selected ready or busy value is printed to stdout, and the program returns the corresponding exit code to its caller.
    Args[Command arguments] -->|Validate choices| Parser[argparse]
    Parser --> State[Selected state]
    State --> Output[stdout and exit code]
```

The value is supplied by the caller or its default. It is not evidence about a
running service. Argument errors exit before a state is printed. Exact values
belong to the [command reference](../reference/command.md).

From this example's root, run `python3 tools/status.py` and
`python3 tools/status.py --state busy` to check both results. The template's tests
also exercise an invalid value and verify stdout, stderr, and exit codes.

[Documentation index](../README.md)
