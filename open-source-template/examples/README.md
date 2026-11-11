# Choosing project-specific examples

The default copy set lives in `../files/`. These examples cover decisions that
need project-specific facts. Adopt the ones that serve the project, preserve
existing documents, replace every `{{UPPER_CASE}}` token, and remove editing
comments. Keep GitHub Actions expressions such as `${{ github.sha }}` intact.

## Project and development basics

| Example | Destination | Customize before adopting |
| --- | --- | --- |
| [README.md.example](README.md.example) | `README.md` | Purpose, status, supported environments, tested installation and quick start, development commands, accurate AI-use disclosure |
| [gitignore.example](gitignore.example) | `.gitignore` | Actual generated/local files; select ecosystem-specific patterns and preserve lockfiles as appropriate |
| [ci.yml.example](ci.yml.example) | `.github/workflows/ci.yml` | Runtime setup and meaningful build/test commands; remove the failing placeholder |
| [dependabot.yml.example](dependabot.yml.example) | `.github/dependabot.yml` | Ecosystems, manifest directories, schedules, and handling of bot PRs under DCO |
| [git-hooks/](git-hooks/README.md) | Hook configuration, runner requirements, commit-range checker, and quality workflow | Preserve existing hooks; choose project tests, formatter/linter commands, file limits, and commit conventions |

`files/` also supplies CHANGELOG.md, .editorconfig, and .gitattributes. Merge their
defaults with the project's existing release-note process, formatters, encodings,
and line-ending choices. They do not replace ecosystem-specific formatter or
linter configuration.

## Releases and licensing

| Example | Destination | Customize before adopting |
| --- | --- | --- |
| [RELEASING.md.example](RELEASING.md.example) | `docs/RELEASING.md` | Actual maintainers, version policy, verification and publishing procedure |
| [release.yml.example](release.yml.example) | `.github/release.yml` | Match categories to real PR labels; review the generated notes |
| [NOTICE.example](NOTICE.example) | `NOTICE` | Actual ownership and applicable third-party attribution |
| [license-review.yml.example](license-review.yml.example) | `.github/workflows/license-review.yml` | The project's actual dependency and distributed-notice checks; remove the failing placeholder |

The changelog records changes for users. The release guide records the publishing
procedure. `.github/release.yml` only configures generated notes. None of these
files creates tags, publishes packages, or establishes a release schedule.

## Project maintenance

| Example | Destination | Customize before adopting |
| --- | --- | --- |
| [MAINTAINERS.md.example](MAINTAINERS.md.example) | `MAINTAINERS.md` | Real maintainers, public identities, and responsibilities |
| [GOVERNANCE.md.example](GOVERNANCE.md.example) | `GOVERNANCE.md` | Actual decision authority and maintainer appointment process; also adopt or link a maintainer roster |
| [ROADMAP.md.example](ROADMAP.md.example) | `ROADMAP.md` | Current priorities and issue links; assign someone to keep it current |
| [CODEOWNERS.example](CODEOWNERS.example) | `.github/CODEOWNERS` | Actual users/teams with appropriate repository access |
| [open-source-settings.json.example](open-source-settings.json.example) | `.github/open-source-settings.json` | Target repository, profile, real required checks, and project preferences |

## Other files when the project needs them

Some useful files depend on information that a general template cannot supply:

- **CITATION.cff:** for projects that want a scholarly citation; use accurate
  authors, software metadata, and publication identifiers.
- **.github/FUNDING.yml:** when the project has confirmed funding or sponsorship
  accounts to publish.
- **AUTHORS / CONTRIBUTORS:** when maintaining a curated credit list; obtain
  consent for personal details and preserve existing attribution requirements.
- **docs/ARCHITECTURE.md and decision records:** when contributors need the
  project's actual components, boundaries, and design reasoning.
- **ACCESSIBILITY.md:** when the project has accessibility goals, tested support,
  known barriers, and a reporting process to document.
- **Formatter, linter, type-checker, and development-container configuration:**
  choose tools appropriate to the project's languages and development workflow;
  the Git-hook bundle provides integration points.

Keep these accurate and maintained when adopted. A longer file list is not a
substitute for working instructions, enforced checks, or responsive maintenance.

References: [EditorConfig](https://editorconfig.org/),
[Git attributes](https://git-scm.com/docs/gitattributes),
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
[GitHub release-note configuration](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes).
