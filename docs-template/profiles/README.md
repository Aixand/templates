# Choose a project documentation profile

Apply the shared [standard](../files/docs/_standards/standard.md) to the smallest
useful documentation set. Profiles describe reader coverage, not required empty
folders. Adapt established project layouts where they already work.

| Profile | Initial coverage | Add when useful |
| --- | --- | --- |
| Small tool | README, first successful task, configuration/CLI lookup, troubleshooting, development checks | Separate guides and reference as the content grows |
| Library / SDK | README, runnable integration, generated symbol reference, error and compatibility contracts, contributor setup | Language-specific SDK guides, architecture, migration guide |
| Service / application | Setup, common tasks, API/configuration reference, architecture, diagnostics and recovery, development | Deployment, backup/restore, upgrade and operator runbooks |
| Suite / workspace | Suite overview, real project map, shared setup, integration flows, cross-project troubleshooting | Shared operations and version compatibility matrix |
| Internal package | Local README with responsibility, supported boundary, entry points, focused checks | Local internals and reference for complex mechanisms |

## Suggested larger-project layout

```text
project/
  README.md
  CONTRIBUTING.md
  docs/
    README.md
    getting-started/
    guides/
      troubleshooting.md
    reference/
    architecture/
      decisions/
    development/
    sdk/                      # Only if an SDK exists
    assets/
    _standards/               # Copied-mode shared rules
```

For a suite, document composition and integration at its root. Each real child
project owns its local behavior and contracts. An ownership map should name
project paths, entry points, shared interfaces, and verification commands.
Keep platform or version differences explicit where they change the reader path.

Use [page templates](../templates/README.md) and compare the
[working example](../examples/project/README.md) before writing a new section.
