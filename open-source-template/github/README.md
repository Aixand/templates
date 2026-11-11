# Configure a project's GitHub settings

Use `scripts/configure-github.py` from this template checkout to **plan**, **apply**,
and **verify** settings on a destination repository. It uses Python 3.10 or newer,
Git, and the existing GitHub CLI (`gh`) authentication. It supports GitHub.com.
Keep the script with this template's `github/profiles/` directory.

## Prepare the destination

1. Install and customize the policy files and workflows using [SETUP](../SETUP.md).
   Land the DCO checker, its tests, and all baseline workflows on the destination's
   default branch, including the repository-file policy workflow. Keep that branch
   name consistent with workflow filters.
2. Run the baseline and project CI on a trial PR targeting that branch. Record
   the actual successful check names, including matrix suffixes where applicable.
   Ensure required jobs run for every relevant PR; a check excluded by path or
   branch filters can leave a PR waiting indefinitely.
3. Copy [the settings example](../examples/open-source-settings.json.example) to
   the destination's `.github/open-source-settings.json`. Customize the repository
   and actual project checks. Remove the example text before running the tool.
4. Authenticate with `gh auth login` and use an account with repository admin
   access. A fine-grained token needs the appropriate repository administration,
   Actions, contents, pull-request, and checks permissions for the API operations
   being performed. Organization policy can restrict operations independently.

Example project configuration:

```json
{
  "version": 1,
  "profile": "solo",
  "repository": "example-org/example-project",
  "new_repository": false,
  "documentation_only": false,
  "project_checks": [
    {"context": "Project tests", "app_slug": "github-actions"}
  ],
  "overrides": {}
}
```

`Project tests` is an example: use the check names actually produced by that
repository. Application projects must specify at least one project check. For
a project containing only documentation, explicitly set `documentation_only` to
`true`; it still requires the four baseline checks. Add the real license-review
check once it exists. Do not enable the deliberately unfinished example checks.

Set `new_repository` to `true` only when initializing a new project's settings.
That opts into turning off Discussions, Wiki, and Projects unless individually
overridden. Existing repositories preserve those choices by default.

## Run the tool

These commands can run from any directory when a destination path is supplied:

```sh
python3 /path/to/open-source-template/scripts/configure-github.py plan --project /path/to/example-project
python3 /path/to/open-source-template/scripts/configure-github.py apply --project /path/to/example-project
python3 /path/to/open-source-template/scripts/configure-github.py verify --project /path/to/example-project
```

`plan` and `verify` perform only reads. `apply` calculates a fresh plan, checks
prerequisites, saves the previous values, performs the changes, and reads the
result back. It does not prompt interactively. An agent setting up a repository
within the user's authorized task can run this sequence directly and report
the result.

Target selection:

- `--project PATH` uses that checkout's `origin`, or its sole remote when there
  is no `origin`. With no target option, the working directory is the project.
- Different fetch/push repositories or ambiguous remotes require an explicit
  target. The tool does not infer a fork's upstream as its destination.
- `--repo OWNER/REPO` chooses a repository explicitly. Pair it with `--config
  /path/to/settings.json`; this mode does not auto-load another checkout's config.
- The configuration's `repository` field, when present, must match the selected
  target. GitHub redirects to a renamed repository also require updating the
  target. `GH_REPO` and `GH_HOST` do not override the target.
- `--profile team` overrides the file's profile for that invocation. Record a
  lasting profile choice in the project's configuration.
- `--check-ref BRANCH_OR_SHA` adds a commit or branch to check discovery. It can
  be repeated. The default search covers the default branch and the head/merge
  commits of the ten most recently updated PRs targeting it.
- `--json` produces a structured plan or final verification result for agents.

## Defaults

The [solo profile](profiles/solo.json) is the baseline. The
[team profile](profiles/team.json) adds one required independent approval and
dismisses old approvals when new changes are pushed.

| Setting | Default |
| --- | --- |
| Merge methods | Merge commits enabled; squash and rebase disabled |
| Delete merged branches | Enabled |
| Auto-merge | Available; enabling it for an individual PR remains a maintainer action |
| Protected branch | Actual default branch, tracked using `~DEFAULT_BRANCH` |
| PRs and resolved review conversations | Required |
| Approvals | Solo: zero; team: one |
| Required checks | DCO sign-off, DCO checker tests, Secret scan, Repository file policy, configured project checks |
| Up-to-date branch before merging | Required |
| Force pushes and branch deletion | Blocked on the protected branch |
| Bypass actors | None in the managed ruleset |
| Linear history, verified commit signatures, merge queue | Not required by the managed ruleset |
| Code-owner approval | Off until explicitly configured with real owners |
| Actions token defaults | Read-only; workflow PR approval permission disabled |
| Private fork workflows | Write tokens and secrets/variables disabled; existing execution and approval policies preserved |
| Dependabot alerts | Enabled |
| Automatic Dependabot security-update PRs | Disabled initially, pending handling under the DCO policy |
| Secret scanning and push protection | Enabled where availability is established without activating a paid product |
| Private vulnerability reporting | Enabled for public repositories; email remains the route for private repositories |
| Issues and pull requests | Enabled |
| Discussions, Wiki, Projects | Preserved for existing projects; off with `new_repository: true` |
| Description and homepage | Preserved unless specified |

Public fork PR workflows already use GitHub's ordinary read-only/no-secrets
model. Review privileged workflows such as `pull_request_target` separately;
repository defaults are not a substitute for safe workflow code. The tool does
not change which outside contributors require approval to run public fork CI.

Dependabot **version-update** PRs come from `.github/dependabot.yml` or `.yaml`.
The tool reports and preserves an existing configuration; disabling automatic
security-update PRs does not disable that separate schedule. For a new project,
leave the optional Dependabot example uninstalled until bot PRs have an agreed
DCO process.

## Project overrides

Use `overrides` to change supported profile fields, for example:

```json
{
  "overrides": {
    "repository_settings": {
      "has_discussions": true,
      "homepage": "https://example.org/docs"
    },
    "reviews": {
      "required_approving_review_count": 2,
      "dismiss_stale_reviews_on_push": true
    }
  }
}
```

Merge overrides must leave at least one merge method enabled. If enabling squash,
define how final author attribution and DCO trailers will be preserved. Requiring
code-owner review also needs an active CODEOWNERS file on the default branch;
verify the named owners' access separately.

Supported fields are those in `solo.json`. `required_checks` cannot be replaced:
use `project_checks` to add checks. Security scanning fields accept
`"if_available"` or `"preserve"`. Null repository preferences mean preserve.
Unknown fields, paid-product activation fields, and visibility changes are
rejected. The tool does not create repositories, releases, or tags.

## Enforcement and existing configuration

The tool owns the repository ruleset named
`open-source-template/default-branch`. Reserve this name for the tool. A single
repository-owned ruleset with that exact name is treated as managed and updated
in place; a matching organization ruleset is not adopted. Duplicate local names
block setup. Put independently managed rules in other rulesets. Additional rule
types added manually to the managed ruleset block replacement until separated.

Other rulesets and classic branch protection are retained. They can impose
stricter requirements than the selected profile. Existing linear-history rules
that conflict with merge-commit-only settings, and existing merge queues, block
automatic setup instead of being silently removed.

New required-check bindings need a successful run within seven days, from the
configured GitHub App. Skipped, failed, stale, or wrong-provider runs do not count.
The resulting rules bind each check to the App's ID. Previously configured
bindings in the managed ruleset can be reused without rerunning idle workflows.
This is a readiness check, not proof that a job meaningfully tests the project;
maintainers still review workflow changes and required-check coverage.

For private repositories, the tool enables scanning only when an existing
enabled security product or scanning setting establishes availability. Otherwise
it reports the features as unavailable without trying to activate a paid product.
Public repositories can enable the free features. Permission, plan, and
organization-policy errors remain explicit failures, not successful configuration.

## Results, backups, and recovery

| Exit code | Meaning |
| --- | --- |
| `0` | Plan has no blockers/unavailable features, or apply/verify confirms the managed settings match |
| `1` | Invalid input, API/transport failure, or an apply operation failed |
| `2` | Prerequisites are blocked, a requested feature is unavailable, or apply/verify still finds differences |

When preflight has blockers, `apply` makes no writes. Unavailable scanning features
are reported separately: other eligible settings can be applied, but the final
result remains incomplete with exit code 2. Private vulnerability reporting on
a private repository is reported as inapplicable rather than as a failed setting.

Before writing, the tool saves a JSON backup in a private temporary directory
and includes its path in the final output. The backup records each setting's
before/after values and API endpoint, without storing authentication tokens.
The ruleset is applied last. If an operation fails partway through, the tool stops
and reports completed operations and the backup path. GitHub changes are not
atomic; it does not attempt to roll back other administrators' concurrent work.
Run `plan` again to inspect the actual state, correct the problem, and reapply.
Re-running a fully applied configuration makes no further writes. After a
visibility or plan change, rerun to configure newly available features.

The tool verifies settings it manages, not every policy in an organization.
API acceptance alone is insufficient: inspect the verification result and
confirm the rules work on a real PR. Check-source discovery currently supports
GitHub App check runs, not legacy commit-status contexts without an App binding.

References: [rulesets API](https://docs.github.com/en/rest/repos/rules),
[repository settings](https://docs.github.com/en/rest/repos/repos),
[Actions permissions](https://docs.github.com/en/rest/actions/permissions),
[check runs](https://docs.github.com/en/rest/checks/runs), and
[security availability](https://docs.github.com/en/code-security/getting-started/github-security-features).
