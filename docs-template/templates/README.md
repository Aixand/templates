# Select a documentation template

Render only pages that fill a reader need. Files ending in `.example` are authoring
sources and are excluded from published-page checks. The renderer replaces named
tokens but leaves author instructions for you to complete.

| Template | Typical destination | Purpose |
| --- | --- | --- |
| [Project README](project/README.md.example) | `README.md` | Purpose and first useful result |
| [Documentation index](project/docs-index.md.example) | `docs/README.md` | Reader-goal navigation and version scope |
| [Tutorial](topics/tutorial.md.example) | `docs/getting-started/first-result.md` | One successful learning path |
| [Task guide](topics/task.md.example) | `docs/guides/TASK.md` | Complete a known task |
| [Reference](topics/reference.md.example) | `docs/reference/CONTRACT.md` | Exact technical contract |
| [Architecture](topics/architecture.md.example) | `docs/architecture/README.md` | Responsibilities and boundaries |
| [Troubleshooting](topics/troubleshooting.md.example) | `docs/guides/troubleshooting.md` | Diagnose a specific symptom |
| [Runbook](topics/runbook.md.example) | `docs/guides/operations/TASK.md` | Operate or recover a system |
| [Development](topics/development.md.example) | `docs/development/README.md` | Change and verify the project |
| [Decision record](topics/decision.md.example) | `docs/architecture/decisions/NNNN-TITLE.md` | Preserve a design decision |
| [Component README](topics/component-readme.md.example) | Component-local `README.md` | Scope and supported boundaries |
| [Review report](topics/review-report.md.example) | Change report or review artifact | Evidence and unresolved gaps |
| [Ownership map](ownership-map.json.example) | Project-specific map | Suite and child-project scope |
| [Local instructions](agent-instructions.md.example) | Ignored local `AGENTS.md` | Load the shared agent contract |

Remove unused sections. Replace author instructions with verified content, then
remove those comments before publication. The checker rejects unfinished author
instructions and unresolved uppercase tokens in selected published pages.

The renderer performs literal substitution and refuses existing destinations.
Review escaping in Markdown, code, JSON, and YAML. It never executes the result.
Follow [setup](../SETUP.md) and compare the [working example](../examples/project/README.md).
