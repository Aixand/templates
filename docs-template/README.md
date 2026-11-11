# Documentation template

Shared documentation standards, page templates, and checks for Aixand projects.
Use them to help readers complete tasks and understand systems with the least
necessary explanation. Keep the technical details that affect decisions.

Follow the setup guide to adopt these files in an application project.

## Start here

| Goal | Start with |
| --- | --- |
| Adopt the template in a project | [Setup](SETUP.md) |
| Find required documentation rules | [Standard](files/docs/_standards/standard.md) |
| Write clear technical English | [Style guide](files/docs/_standards/style-guide.md) |
| Explain a system visually | [Diagram guide](files/docs/_standards/diagrams.md) |
| Keep documentation accurate | [Maintenance](files/docs/_standards/maintenance.md) |
| Assign or review documentation work | [Agent workflow](files/docs/_standards/agent-workflow.md) |
| Choose a project structure | [Project profiles](profiles/README.md) |
| Choose a page template | [Template catalog](templates/README.md) |
| Read a complete working example | [Example project](examples/project/README.md) |
| Run checks and understand their limits | [Checks](checks/README.md) |
| Review the research behind the standard | [References](files/docs/_standards/references.md) |

## What to copy

Copy selected contents of `files/` into a project after reviewing its current
layout. This adds standards, a documentation checker, its tests, and a checker
configuration. Merge existing files deliberately. The examples and page templates
require selection or customization; they are not a complete product manual.

The shared contract is versioned in
[the standard](files/docs/_standards/standard.md). Record its version in the
adopting project's documentation index. Changes here do not update copied files.

## Relationship to adjacent templates

| Template | Owns |
| --- | --- |
| `docs-template` | Documentation structure, language, diagrams, maintenance, and documentation checks |
| `open-source-template` | License and contribution policies, community files, and repository settings |
| `installation-template` | Development commands, installation, packaging, and release contracts |

Use the actual project commands and policies when adapting pages. A documentation
change does not establish installation support, release availability, or a new
public interface.

## Validate this template

Run from this directory with Python 3.11 or newer:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 files/tests/tooling/checks/docs_test.py
python3 files/scripts/checks/check-docs.py --root .
```

See [checks](checks/README.md) for rendered diagrams, the runnable example,
and repository-policy tests.
The Python checker uses only the standard library. Diagram rendering uses the
optional locked Node toolchain in `tools/`.

## Local agent instructions

The tracked [agent contract](files/docs/_standards/agent-workflow.md) is the
canonical instruction source. A local, ignored `AGENTS.md` points to it. Follow
[setup](SETUP.md#connect-local-agent-instructions) to create that entry point
in a clone. A file in this directory does not automatically govern sibling
projects. Shared-path mode requires an accessible checkout; copied mode works
with an independently cloned project.

Original template material uses [Apache-2.0](LICENSE). Reused repository-policy
tooling comes from the adjacent open-source template under the same license.
Research sources are linked and summarized; their full texts are not bundled.
