# Open-source template

Reusable open-source policies, repository basics, and GitHub checks for projects
maintained by **Artificial Intelligence Advancement Initiative Inc.**

The defaults are Apache-2.0, Developer Certificate of Origin (DCO) sign-offs,
permission to use AI tools with human accountability, and private security and
conduct reporting to **corporate@aixand.org**.

## Use this template

1. Follow [SETUP.md](SETUP.md) to review and copy the contents of `files/` into a
   project. Merge with existing policies and workflows instead of overwriting them.
2. Replace `{{PROJECT_NAME}}`, `{{REPOSITORY_URL}}`, and `{{DOCS_URL}}` in the copied
   files. Keep the standard `LICENSE` and `DCO` texts unchanged.
3. Choose from the [optional examples](examples/README.md) for project
   documentation, releases, owners, dependencies, checks, and third-party notices.
   Replace their additional placeholders with real project information.
4. Run the checks and configure the repository settings described in the setup
   guide before relying on enforcement.

For GitHub configuration, use the [setup tool](github/README.md) to plan, apply,
and verify rulesets, merge preferences, Actions permissions, and available
security features. It detects the destination from its Git remote and supports
solo and team profiles with project-specific settings.

Copy **the contents of `files/`**, including hidden files, into the project root.
Preserve existing changelog history and merge editor and Git settings with the
project's conventions. This README and SETUP describe the template; retain the
project's own README or adapt `examples/README.md.example` if it needs one.

The [repository file policy](REPOSITORY_FILES.md) keeps coding-assistant
instructions and local configuration out of tracked files. Install its commit
hook in each clone; the same policy runs in CI. Product skill and prompt assets
remain allowed.

## AI-assisted development

AI tools have been used during development of this template. All contributions,
including AI-assisted contributions, must meet the template's contribution,
review, and licensing requirements.

AI-generated output must not be assumed to be original or free of third-party
restrictions. Contributors must review their submissions, have the right to
contribute them, identify known third-party sources, and preserve applicable
licenses and notices.

See the [contribution requirements](files/CONTRIBUTING.md) for details and
instructions for reporting ownership or licensing concerns.

## Included files

| Path under `files/` | Purpose |
| --- | --- |
| `LICENSE` | Unmodified Apache License 2.0, including its example appendix |
| `DCO` | Unmodified Developer Certificate of Origin 1.1 |
| `CONTRIBUTING.md` | Contribution rights, sign-offs, AI disclosure and review, and licensing reports |
| `CODE_OF_CONDUCT.md` | Participation standards, reporting, and enforcement |
| `SECURITY.md` | Private vulnerability reporting and supported versions |
| `SUPPORT.md` | Public support channels and safe diagnostics |
| `CHANGELOG.md` | User-visible changes, starting with an Unreleased section |
| `.editorconfig` | Encoding, line endings, whitespace, and common indentation defaults |
| `.gitattributes` | Git text normalization, batch-script line endings, and binary handling |
| `.gitignore` | Assistant-file ignore defaults to merge with project rules |
| `REPOSITORY_FILES.md` | Tracked-file policy and per-clone commit-hook setup |
| `.github/PULL_REQUEST_TEMPLATE.md` | Validation, AI assistance and source disclosures, and contributor checklist |
| `.github/ISSUE_TEMPLATE/` | Bug, documentation, feature, and usage forms; private-report links |
| `.github/workflows/dco.yml` | Trusted-base DCO validation and checker tests |
| `.github/workflows/secret-scan.yml` | Pinned Gitleaks scan of fetched Git history |
| `.github/workflows/repository-files.yml` | Assistant-file checks on the index and introduced commits |
| `scripts/checks/check-dco.py` | Author/co-author sign-off and PR metadata validation |
| `scripts/checks/check-repository-files.py` | Case-insensitive index and commit-range file checks |
| `scripts/checks/install-file-policy-hook.py` | Safe per-clone pre-commit hook installation |
| `tests/tooling/checks/dco_test.py` | Regression tests for the DCO checker |
| `tests/tooling/checks/repository_files_test.py` | Real-index, history, and commit-hook regression tests |

The [examples catalog](examples/README.md) includes a project README, ignore
rules, release procedures and notes, maintainer roster, governance, roadmap,
NOTICE, CODEOWNERS, Dependabot, CI, license review, and GitHub settings. These
need project-specific choices before adoption. The CI and license review
examples fail until their placeholder steps are replaced with real checks.

The optional [Git-hook bundle](examples/git-hooks/README.md) adds checks during
`git commit` and `git push`, Conventional Commit message linting, and matching
CI enforcement. Install it in each clone and add the project's actual test and
formatter commands. Preserve any existing hook manager.

This template supplies policies and baseline checks. Each project still needs
working installation instructions, meaningful tests, accurate support promises,
and an inventory of any third-party material it distributes.

The template's own `.github/workflows/template-checks.yml` tests the setup tool
and bundled DCO checker and lints workflow examples. It belongs to this template;
destination workflows are under `files/` and `examples/`.

## Maintenance and sources

Review this template when GitHub behavior, pinned tools, or organization policies
change. The root [CHANGELOG.md](CHANGELOG.md) records template changes;
`files/CHANGELOG.md` is the starter for adopting projects. Changes here do not
automatically update projects that copied it.

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt)
- [Developer Certificate of Origin 1.1](https://developercertificate.org/)
- [GitHub community health files](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
- [Gitleaks](https://github.com/gitleaks/gitleaks)

Original template material is licensed under [Apache-2.0](LICENSE). The bundled
DCO document retains its own copyright and verbatim-copy terms.
