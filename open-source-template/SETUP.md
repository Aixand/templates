# Set up an open-source project

## 1. Review the project and copy the baseline

Start from an up-to-date branch and review any existing policies, workflows,
copyright notices, and dependency licenses. These defaults assume a GitHub.com
repository, a `main` branch, and maintenance by Artificial Intelligence
Advancement Initiative Inc.

Copy the **contents** of `files/` to the project root, including hidden files.
For example, from a terminal:

```sh
cp -R -i /path/to/open-source-template/files/. /path/to/project/
```

The `-i` option prompts before overwriting files. When a destination file already
exists, merge it deliberately rather than accepting an overwrite. Keep the
project's README, installation guide, existing tests, release process, changelog
history, and third-party notices. If an older issue template overlaps a new form,
consolidate them so users do not see duplicate choices.

Merge `.editorconfig` with existing formatters and indentation conventions.
Review `.gitattributes` against the project's encodings, line endings, binary
formats, and any existing Git LFS rules. Its defaults normalize detected text
to LF in Git and use CRLF working copies for Windows batch scripts. Adopting it
can affect later checkouts and staging; do not run a bulk renormalization as
part of copying the template. Review any intended normalization separately.

Keep an existing changelog or news-fragment process if it already works. Otherwise,
start `CHANGELOG.md` with Unreleased and add useful changes as they happen. Do not
invent past releases, version numbers, publication dates, or comparison links.

Merge the assistant-file ignore defaults with the project's `.gitignore`. Remove
currently tracked coding-assistant instructions/configuration, including
`AGENTS.md`, `CLAUDE.md`, and recognized variants, following
[REPOSITORY_FILES.md](files/REPOSITORY_FILES.md). Preserve actual product assets
such as native skill packages and ordinary prompt packs. Do not rewrite existing
Git history as part of adoption. Install or integrate the per-clone commit hook;
an existing hook manager must be preserved.

The template does not change repository visibility or create a remote. Review
files and Git history for credentials and private material before publishing.
A fresh repository avoids importing old history, but its initial contents still
need that review.

## 2. Customize the policies and links

Replace these exact tokens in the copied files:

| Token | Value |
| --- | --- |
| `{{PROJECT_NAME}}` | Public project name, such as `Example Project` |
| `{{REPOSITORY_URL}}` | GitHub HTTPS URL without a trailing slash, such as `https://github.com/example-org/example-project` |
| `{{DOCS_URL}}` | Working documentation URL, or the repository README URL if there is no separate docs site |

Use a text editor and preserve YAML quoting and indentation. There should be no
unreplaced tokens in the installed files. Optional examples have additional
descriptive tokens for their project-specific content; replace those too and
remove editing comments. Do not replace GitHub Actions expressions such as
`${{ github.sha }}`.

- Confirm `corporate@aixand.org` is monitored and the named organization really
  maintains the project. Use the same contact in conduct and security policies.
- Review the security support policy: by default fixes target current `main`
  and the latest stable release, if one exists. Document any maintained older
  releases or different support commitments.
- If the default branch is not `main`, update the workflows and security policy.
- Add project-specific development and test commands to CONTRIBUTING or link to
  an existing development guide. Test installation and quick-start instructions.
- Add the README's AI-development disclosure only when it accurately describes
  the project. Preserve the contribution policy's human review and substantial
  AI-use disclosure requirements, and the PR template's source and review fields.
- Link CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, LICENSE, and the changelog
  from the project's README. Update package metadata to match the actual license,
  using the ecosystem's supported fields, and include necessary notices in artifacts.

## 3. Preserve license and contribution terms

Keep `LICENSE` and `DCO` verbatim. The `[yyyy]` and `[name of copyright owner]`
fields in the Apache appendix are examples, not unfinished project metadata.
Actual copyright notices belong in appropriate source headers or notice files;
use accurate years and owners. Name Artificial Intelligence Advancement
Initiative Inc. only for rights it actually owns. Contributors retain their
copyright; the template does not require assignment or a separate CLA.

An Apache-2.0 project license does not relicense third-party material. Before
copying code, assets, models, documentation, or dependencies into a distribution,
record the source and license and preserve required notices. Existing employer
rights and third-party restrictions still matter. A DCO sign-off records a
contributor's certification; it cannot independently prove ownership or cure a
missing permission.

Do not copy another project's dependency inventory. Create a project-specific
inventory and any required notices based on what this project ships. See
`examples/NOTICE.example` if a NOTICE file is useful or required by included
material. A NOTICE file is not mandatory merely because the project uses Apache.

The contribution policy explains how to report ownership and licensing concerns
privately to `corporate@aixand.org`, including affected files, original sources,
the concern and supporting evidence, and reporter contact information. Keep the
report and provenance, review the affected work, and address substantiated
infringement or noncompliance. Appropriate action may include correcting notices,
satisfying license requirements, obtaining permission, or replacing or removing
material. A request alone does not require removal of properly licensed work.
Removal alone does not resolve every possible dispute; seek qualified advice for
a concrete claim.

## 4. Adapt the optional examples

See the [examples catalog](examples/README.md) for guidance, including other
files that are useful only when the project has the relevant information.

| Example | Destination after customization | Decisions required |
| --- | --- | --- |
| `README.md.example` | `README.md` | Purpose, compatibility, tested installation, quick start, and development commands |
| `gitignore.example` | `.gitignore` | Actual generated and local files; ecosystem and lockfile conventions |
| `RELEASING.md.example` | `docs/RELEASING.md` | Actual version policy, maintainers, verification, and publishing commands |
| `release.yml.example` | `.github/release.yml` | Generated release-note categories matching actual PR labels |
| `MAINTAINERS.md.example` | `MAINTAINERS.md` | Public maintainer roster and responsibilities |
| `GOVERNANCE.md.example` | `GOVERNANCE.md` | Real decision authority and appointment process; link the actual maintainer roster |
| `ROADMAP.md.example` | `ROADMAP.md` | Current priorities and issue links, maintained as plans change |
| `NOTICE.example` | `NOTICE` | Actual owners, years, and applicable attribution notices |
| `CODEOWNERS.example` | `.github/CODEOWNERS` | Real GitHub users or teams with repository access |
| `dependabot.yml.example` | `.github/dependabot.yml` | Ecosystems, manifest directories, update schedule |
| `ci.yml.example` | `.github/workflows/ci.yml` | Runtime setup, build, tests, lint, packaging |
| `license-review.yml.example` | `.github/workflows/license-review.yml` | Inventory, dependency policy, shipped notices, verification command |
| `open-source-settings.json.example` | `.github/open-source-settings.json` | Repository, solo/team profile, actual required checks, project preferences |
| `git-hooks/` | See the [bundle guide](examples/git-hooks/README.md) | Existing hook manager, formatter/linter/type-check/test commands, commit conventions, CI, and per-clone installation |

Replace the explicit failing steps in both workflow examples before enabling
them. Do not count a placeholder workflow as a successful project check.
Dependency license metadata can be missing or wrong; automated review should
support review of the actual licenses and distributed material.

The CODEOWNERS example has commented placeholders. Uncomment rules only after
replacing the owners. Dependabot's active example covers GitHub Actions; select
the additional ecosystems that the project actually uses.

The release-note configuration is not an Actions workflow. It groups generated
notes and needs labels that the project actually uses. Review generated notes
before publishing and maintain user-facing changelog entries separately.
Adopting a release guide or configuration does not create tags or releases.

Preserve existing README content and release history. Use actual project facts
for maintainers, governance, and roadmap entries. Install only examples the
project will maintain, and adjust their relative links if you change destinations.

For checks during `git commit` and `git push`, adopt the optional
[Git-hook bundle](examples/git-hooks/README.md). Its defaults check staged files,
Conventional Commit messages, and files/tests before push. Add actual application
tests and connect the project's formatter, linter, and applicable type checker;
the generic file checks do not format source code. Follow the guide's
[stage mapping and examples](examples/git-hooks/README.md#connect-the-projects-formatters-and-checks):
use staged formatting/lint checks before commit and fast whole-project checks
before push. Reuse existing configuration and locked tool versions, install the
project tools in CI, and explicitly cover pre-push checks there as well.
Document exact installation and manual check commands, plus any omitted or
CI-only checks, in CONTRIBUTING. Hooks are local and are not installed merely
by cloning. Preserve existing hooks and `core.hooksPath`; do not install
competing hook managers.
Keep DCO certifications explicit and truthful. Require the matching CI checks
after their first successful PR run, since local hooks can be bypassed.
Verify that formatting errors and failing tests reject a commit or push as
appropriate, that corrected changes pass, and that matching CI checks enforce
the same rules. Keep this validation in a disposable branch or clone.

## 5. Validate the installed files

From the destination repository:

```sh
python3 tests/tooling/checks/dco_test.py
python3 tests/tooling/checks/repository_files_test.py
python3 scripts/checks/check-repository-files.py
git diff --check
rg -n '\{\{[A-Z][A-Z_]*\}\}' README.md CHANGELOG.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md SUPPORT.md .github
```

The placeholder search should produce no matches (exit status 1 means no
matches). Include any additional adopted documents in that search; substitute
the existing changelog path if the project uses another location. Run `actionlint`
on installed GitHub workflows, run the project's real tests, and preview the issue
forms, PR template, and links on GitHub. Parse `.github/release.yml` as YAML if
adopted; it is not an input to `actionlint`.

Check editor settings with the project's formatter and check intended Git
attributes with `git check-attr`. Use `git check-ignore` to confirm ignore rules
exclude local/generated files while allowing source, sanitized configuration
examples, and the lockfiles the project tracks.

The DCO checker requires Git and Python 3. It runs from the trusted base commit
for PR events and reads PR metadata with a read-only token. Never change that
`pull_request_target` workflow to execute a contributor's code or install their
dependencies. When changing the checker, run its proposed tests locally and in
ordinary unprivileged project CI as well.

The secret scan uses a checksum-verified Gitleaks CLI, read-only permissions,
full redaction, and all fetched Git history. It uses workflow-controlled default
rules and an empty ignore file; repository `.gitleaks.toml`, `.gitleaksignore`,
and inline `gitleaks:allow` comments do not suppress findings. It does not execute
project code or upload scan reports. Review any workflow changes carefully:
ordinary `pull_request` workflows can themselves be changed by a PR.

For a finding, privately determine whether it is a real credential. Revoke or
rotate exposed credentials before cleaning up files or history. Review any
necessary false-positive exception narrowly; do not disable scanning wholesale.
The scan cannot establish that all sensitive information has been removed.

## 6. Configure GitHub enforcement

Repository files do not enable these settings automatically:

The [GitHub setup tool](github/README.md) automates the supported settings below.
Install and run the workflows first, customize the project's settings JSON, then
run `plan`, `apply`, and `verify` against its checkout. The tool defaults to merge
commits, PRs with passing checks, and zero mandatory approvals for solo projects;
the team profile requires one independent approval. Existing protections remain
in effect. Check the tool's result for unavailable features or remaining setup.

1. Enable Actions with read-only default token permissions. Allow the pinned
   actions needed by these workflows.
2. Land the baseline on `main` before testing DCO enforcement: its PR workflow
   deliberately uses the checker and tests already on the base branch.
3. Open a small signed test PR and confirm the checks run. After their first run,
   add **DCO sign-off**, **DCO checker tests**, **Secret scan**,
   **Repository file policy**, and the project's
   real test/build checks to the `main` ruleset's required status checks. Select
   the actual check names shown by GitHub and bind to GitHub Actions where the
   settings support it.
4. Require PRs, an appropriate number of reviews, resolved review conversations,
   and checks on the latest base before merging. Block force pushes and branch
   deletion. Limit bypass permissions. Enable required code-owner review only
   after configuring real owners. Availability depends on repository visibility
   and the GitHub plan; confirm which controls are actually enforced.
5. Enable private vulnerability reporting where available, and keep the email
   route working regardless. Enable available secret scanning, push protection,
   dependency graph, and Dependabot alerts. Confirm the security policy appears
   on the repository's Security tab.
6. Confirm the Issues and Actions tabs, forms, support links, and maintainer
   access work for an outside contributor. Do not enable unused support channels.

The DCO checker requires a matching sign-off for every PR commit author and
declared co-author. It has no automatic bot or merge-commit exemption and rejects
PRs above the API's 250-commit limit. Split oversized PRs. For bot updates, a human
may review and resubmit the work as a new commit under their own identity if they
can truthfully certify it; do not manufacture another person's or a bot's
certification. Preserve accurate attribution and genuine co-author sign-offs.

Check the final commit message when squash-merging, including its author and
sign-off trailers. A GitHub “Verified” signature and a DCO sign-off serve different
purposes; one does not substitute for the other. Require new PR checks after
rewriting commits. These workflows assume direct PR merges; a merge queue needs
separate `merge_group` workflow support before it can be enabled.

## 7. Maintain the baseline

Periodically review the reporting mailbox, support policy, owners, required
checks, dependency notices, and pinned actions/tools. Gitleaks updates require
reviewing the release and updating both its version and archive checksum.
Keep changelog entries useful to users, verify release instructions when the
publishing process changes, and keep adopted maintainer/roadmap documents current.
Repeat project checks when adapting the template; each repository owns its
resulting policy and configuration.

References: [branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
[private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository),
[Dependabot configuration](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference),
and [Apache-2.0 terms](https://www.apache.org/licenses/LICENSE-2.0.txt).
