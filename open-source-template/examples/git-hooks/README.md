# Local Git hooks and CI checks

This optional bundle uses [pre-commit](https://pre-commit.com/) to run checks
during `git commit` and `git push`. It works across project languages; the hook
runner needs Python 3.10 or newer and Git. No Node.js dependency is added.

## Adopt the bundle

First install the normal template baseline, including the DCO checker and tests.
Merge these files into the destination, preserving its existing configuration:

| Bundle path | Destination |
| --- | --- |
| `.pre-commit-config.yaml` | `.pre-commit-config.yaml` |
| `requirements-hooks.txt` | `requirements-hooks.txt` |
| `scripts/checks/check-commit-messages.py` | `scripts/checks/check-commit-messages.py` |
| `.github/workflows/quality.yml` | `.github/workflows/quality.yml` |

Keep this README with the template; document the chosen commands in the project's
CONTRIBUTING guide. Add `.venv-hooks/` to its `.gitignore` if using the setup below.
Change workflow branch filters if the default branch is not `main`.

If the project already uses Husky, Lefthook, or another hook manager, integrate
the needed checks there instead of installing a competing manager. Inspect
`git config --show-origin --get-all core.hooksPath` and existing Git hooks before
installation. Do not clear an existing hooksPath or overwrite custom hooks.
pre-commit's normal install preserves existing hook scripts in migration mode;
do not use `--overwrite` without reviewing what it would replace.

## Install in each clone

Read the hook configuration before executing it. On Linux or macOS:

```sh
python3 -m venv .venv-hooks
.venv-hooks/bin/python -m pip install -r requirements-hooks.txt
.venv-hooks/bin/python -m pre_commit install --install-hooks
.venv-hooks/bin/python -m pre_commit run --all-files --hook-stage pre-commit
```

On Windows use `py -3 -m venv .venv-hooks` and
`.venv-hooks\Scripts\python.exe` in place of `.venv-hooks/bin/python`. Adapt local
`language: system` commands to the available interpreter and project toolchain.
Keep this environment available while its hooks are installed. To uninstall:

```sh
.venv-hooks/bin/python -m pre_commit uninstall -t pre-commit -t commit-msg -t pre-push
```

Cloning alone does not install Git hooks. Each contributor runs installation
once per clone; CI runs its own copy of the checks regardless.

## Defaults

| Stage | Checks |
| --- | --- |
| `pre-commit` | Staged files: whitespace/end-of-file fixes, conflict markers, YAML/JSON/TOML syntax, filename case conflicts, broken symlinks, private-key markers, and files above 1 MiB |
| `commit-msg` | Conventional Commit messages, such as `fix(api): handle missing input` |
| `pre-push` | File checks on the pushed changes and the baseline DCO checker tests |

Whitespace fixers preserve Markdown hard breaks and leave LICENSE, COPYING,
DCO, and NOTICE files unchanged. Review and stage any fixes before retrying a
commit. Adopt appropriate exclusions for actual vendored/generated files and
choose a size limit suitable for the project; keep required notices intact.

**Add the project's real fast test command to `pre-push` and keep it in CI.**
The example runs the baseline DCO checker tests; those do not test the project's
application behavior. Set `pass_filenames: false` and `always_run: true` for a
whole-project test command. Keep expensive platform/build matrices in CI.
The pre-push stage operates in the current checkout, so CI remains authoritative
when pushing another ref or working with local changes.

The private-key marker check is an early warning. Keep the existing full-history
Gitleaks workflow for broader secret detection, including removed material.

The baseline also supplies `check-repository-files.py`. This bundle integrates it
with the existing pre-commit runner. It rejects coding-assistant instruction and
configuration paths from the complete index, including forced additions and
case variants. Keep real product skill/prompt assets. See the installed
`REPOSITORY_FILES.md`; use the standalone hook installer only when no hook manager
exists. The dedicated CI job additionally checks every introduced commit.

## Commit messages and DCO

The selected [Conventional Commit hook](https://github.com/compilerla/conventional-pre-commit)
accepts `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`,
`style`, and `test`, with optional scope and breaking-change notation. Its default
exceptions permit generated merge and autosquash messages; strict mode is
not enabled because this template uses merge commits. This checks message style,
not the truth or ownership of a contribution.
For a revert, edit the generated subject to use `revert: description`.

Continue using truthful DCO sign-offs:

```sh
git commit -s -m "feat: add a new command"
```

Hooks do not insert certifications or rewrite commit messages. The existing
trusted-base DCO workflow still validates author/co-author sign-offs. The new
Commit messages job checks every introduced PR commit using the same configured
style hook; it does not retroactively lint the repository's old history or the
synthetic PR merge commit. Rewriting a branch requires fresh checks.

## Enforce on GitHub

Install `quality.yml` and run it on a real PR. After **Repository hygiene** and
**Commit messages** pass, add both exact names with `app_slug: github-actions`
to `.github/open-source-settings.json` under `project_checks`, then run the
setup tool's plan/apply/verify procedure. Keep the project's tests and license
checks required too. Do not enable required checks before they have run.

Local hooks can be bypassed or not installed. Required CI checks provide the
shared enforcement. The quality workflow uses ordinary `pull_request`, read-only
permissions, and no secrets; never move project-controlled hooks or dependencies
into `pull_request_target`. Review changes to workflows and hook configuration.

## Connect the project's formatters and checks

**Hook adoption includes connecting the project's real development tools.**
The generic whitespace checks and `.editorconfig` do not format source code.
Inspect existing package scripts, formatter/linter configuration, tool versions,
and CI first. Reuse those commands and settings. If no tools exist, choose tools
appropriate to the project's languages and document the choice; do not add a
competing formatting policy or reformat unrelated code while installing hooks.

Use this stage mapping, adjusting slow checks to keep local feedback practical:

| Tool | Local stage | CI coverage |
| --- | --- | --- |
| Formatter | `pre-commit`, on staged source files; fixes may be applied locally | Check formatting across the project's maintained source files |
| Fast linter | `pre-commit`, on staged files when the tool supports filenames | Run the same rules across the project |
| Type checker | `pre-push`, usually a whole-project command | Run the same type check in project CI |
| Fast application tests | `pre-push`, using the project's test command | Run those tests plus any larger build/platform matrix |

Only enable applicable checks. Document any omitted tool or checks reserved for
CI in CONTRIBUTING, together with exact install, format, lint, type-check, and
test commands. Preserve existing exclusions for generated and vendored material.

### Example: a Python project already using Ruff

Add these entries to the existing `repo: local` hook list. This example assumes
Ruff is pinned in the project's development dependencies and available on PATH
whenever Git runs, including from an IDE. `language: system` does not install
Ruff; installing the separate `.venv-hooks` runner does not install project tools.
Use the project's environment runner in `entry` if that is its normal convention.

```yaml
- id: project-ruff-lint
  name: Lint staged Python files
  entry: ruff check
  language: system
  types_or: [python, pyi]
  stages: [pre-commit, manual]
- id: project-ruff-format
  name: Format staged Python files
  entry: ruff format
  language: system
  types_or: [python, pyi]
  stages: [pre-commit, manual]
```

These hooks receive filenames from pre-commit. When formatting changes a file,
the commit stops: review the changes, stage the intended fixes, and retry. Do not
add automatic `git add` commands to hooks. For check-only formatting, use
`entry: ruff format --check`. If enabling Ruff's lint fixes, run them before its
formatter, as described in the [Ruff integration guide](https://docs.astral.sh/ruff/integrations/#pre-commit).

For a JavaScript/TypeScript project, connect its existing Prettier and ESLint
scripts instead; preserve an existing Husky/lint-staged setup. Use the installed,
locked tools. A file-based hook must accept only the filenames supplied to it;
do not run a whole-tree formatter that also rewrites unstaged files. See
[Prettier's hook guidance](https://prettier.io/docs/precommit).

### Whole-project commands before push

For example, if an npm project already defines a noninteractive `typecheck`
script, add this entry to `repo: local` and install its dependencies first:

```yaml
- id: project-typecheck
  name: Type-check the project before pushing
  entry: npm run typecheck
  language: system
  stages: [pre-push]
  pass_filenames: false
  always_run: true
```

Use the same pattern for its fast test command, with a unique hook ID and its
actual package manager or task runner. `pass_filenames: false` prevents Git paths
from becoming test arguments; `always_run: true` also checks changes to shared
configuration. Use one-shot test commands that exit on failure, not watch mode.

### Connect the same tools to CI

The supplied `quality.yml` installs only the hook runner. Before **Check
repository files**, add the project's runtime and locked development-dependency
installation, and make its tools available on PATH. For example, an npm project
with a package lock uses `npm ci`; a Python project uses its existing locked
development-environment setup. Use matching tool versions and configuration
locally and in CI.

**Repository hygiene** runs `--all-files --hook-stage pre-commit`, including any
formatter and linter added to that stage. If a formatter edits files, pre-commit
fails the job; CI must not commit those edits. Alternatively, the project's CI
can check formatting explicitly with commands such as `ruff format --check .`
and lint with `ruff check .`, respecting its source layout and exclusions.

That job does **not** run hooks restricted to `pre-push`. Run the same type-check
and test commands in project CI, or add an explicit stage invocation after
installing the required tools:

```sh
"$RUNNER_TEMP/hooks-venv/bin/python" -m pre_commit run --all-files --hook-stage pre-push
```

Before declaring adoption complete, exercise a formatting failure and a failing
test in a disposable branch or clone, verify the commit/push is rejected, then
fix the input and retry successfully. Confirm the corresponding CI jobs also
reject failures and pass the corrected changes before making them required.
See the [pre-commit configuration reference](https://pre-commit.com/#pre-commit-configyaml---hooks)
for file filters and hook options.

## Maintain tool versions

Hook repositories are pinned to full commit IDs and the runner to a release.
Review updates, use `pre-commit autoupdate --freeze` when appropriate, and run the
local and CI checks before accepting new pins. Transitive package dependencies
are not fully locked by this small requirements file.
