# Adopt the documentation template

Run these steps from the destination project root. Inspect existing documentation,
commands, and repository instructions first. Preserve useful content and paths.

## Select a profile

Choose a [project profile](profiles/README.md). Create only sections that readers
need. A library can use a small README and generated API reference. A suite needs
a project map and integration guidance in addition to its child-project docs.

## Copy the shared files

Review `files/` in this template. Copy its selected contents, including
`docs/_standards/`, `scripts/checks/check-docs.py`, and
`tests/tooling/checks/docs_test.py`. Merge `docs-checks.json` with existing
configuration and adapt its include/exclude paths. Do not replace an existing
README, contribution policy, documentation tree, or workflow wholesale.

Record `Documentation standard: 0.1.0` in the destination documentation index.
Keep the copied standards together so their relative links resolve.

## Create the reader paths

Select pages from the [template catalog](templates/README.md). For example, run
the renderer from this template's root, replacing `/path/to/project` first:

```sh
python3 scripts/render-template.py templates/project/README.md.example /path/to/project/README.md --set PROJECT_NAME=Example
```

The renderer refuses an existing destination and unresolved placeholders. Merge
into an existing page manually. Complete the author comments before publication;
remove the comments after replacing them with verified project facts.
Substitution is literal; review any quoting required by the destination format.

Prefer one complete tutorial to several unfinished walkthroughs. Keep exact
contracts in reference pages and link to them from procedures.

## Connect local agent instructions

The adjacent open-source template keeps coding-assistant instructions local and
ignored. Keep the shared rules in tracked ordinary documentation. Merge its
assistant-file ignore rules into the project's `.gitignore` first.

From this template's root, create a project-local entry point:

```sh
python3 scripts/render-template.py templates/agent-instructions.md.example /path/to/project/AGENTS.md --set STANDARDS_PATH=docs/_standards
```

The path is relative to the destination project root. For shared-checkout mode,
set `STANDARDS_PATH` to an accessible absolute path ending in this template's
`files/docs/_standards` directory. Such a local path belongs only in the ignored
entry point. Published documentation must use portable links.

If `AGENTS.md` already exists, merge the documentation instruction into it.
Do not discard project-specific instructions or replace it with a symlink to a
file that lacks the project's other rules. Start a fresh agent session from the
project directory and verify that it reads the intended instruction and standard.
A sibling `AGENTS.md` is outside normal project instruction discovery.

For this template's own clone:

```sh
python3 scripts/render-template.py templates/agent-instructions.md.example AGENTS.md --set STANDARDS_PATH=files/docs/_standards
```

That command is needed only if the local entry point does not already exist.
A normal clone does not contain ignored local instructions.

## Validate and review

From the destination project root:

```sh
python3 tests/tooling/checks/docs_test.py
python3 scripts/checks/check-docs.py --root .
```

Run the project's actual documentation examples separately. Follow
[diagram validation](files/docs/_standards/diagrams.md#validate-a-diagram)
to render changed diagrams. Add the checks to existing CI using the
[workflow example](examples/workflows/docs.yml.example), after adapting paths.
Use the template's locked renderer or adopt its `tools/package.json` and lockfile
in a separate documentation-tool directory. The checker targets Mermaid CLI 12;
an existing product renderer still needs qualification for its publishing target.

Use the [review checklist](files/docs/_standards/standard.md#accept-a-documentation-change).
Record executed checks and unresolved behavior in the change report. A checker
pass does not establish technical accuracy or a successful reader outcome.

## Keep the adoption current

Use the [maintenance guide](files/docs/_standards/maintenance.md). Upgrade copied
standards deliberately and record their new version. Project-specific additions
belong outside `_standards/`, linked from the documentation index. Preserve older
standards only when supporting an explicitly maintained documentation version.
