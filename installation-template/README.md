# Installation template

Revision 2 adds [workspace products and portable installation](V2.md):
independent hierarchical products, collection installers, component adapters,
artifact-only lifecycle operations, runtime bootstrap, and release export.
The [product contract](docs/product-contract.md) defines the new schema-2 surface.
Schema-1 profiles remain supported. Native Windows/macOS jobs are provided;
their actual successful execution remains required for platform qualification.

A standard under development for developing, building, installing, packaging, and
publishing projects across Python, Rust/Cargo, web, and mixed stacks.

The template includes a shared helper, Python/Cargo profiles, schemas, fixtures,
and workflow examples. Validate native platforms and installer integration for
your project, and configure publishing authority before enabling releases.

Start with [SETUP.md](SETUP.md) to try or adopt the helper, and [V1.md](V1.md) for
the exact supported surface.

## Documentation

- [Accepted lifecycle defaults](docs/lifecycle-decisions.md): first-version scope,
  explicit updates, pinning, rollback, retention, and broken releases.
- [Command contract](docs/command-contract.md): what each project command means.
- [Release contract](docs/release-contract.md): GitHub Actions, package formats,
  registry publication, native downloads, and verification.
- [Project profiles](profiles/README.md): Python, Cargo, native bundles, hybrid
  products, and web applications.
- [Changelog](CHANGELOG.md): changes to this template.

The central rule is: **the same command has the same meaning in every project**.
The underlying tool remains appropriate to the project: uv and its declared
build backend for Python, Cargo for Rust, and the existing package manager for
web projects.

## Intended project interface

An adopting project root exposes the supported operations through:

```sh
./dev.sh help
./dev.sh doctor
./dev.sh develop
./dev.sh check
./dev.sh test
./dev.sh build --release
./dev.sh package
./dev.sh verify --artifact PATH
./dev.sh install
./dev.sh reinstall
./dev.sh uninstall
```

Native Windows projects have a `dev.ps1` wrapper to qualify. The
[command contract](docs/command-contract.md) defines capabilities and unsupported
operations; a library does not need a global command installation.

Publishing is a separate, explicitly enabled capability. A local build,
package operation, or ordinary CI run would never publish a release.

## Relationship to adjacent projects

| Project | Responsibility |
| --- | --- |
| `open-source-template` | Policies, contribution certification, community files, baseline security checks, and GitHub repository settings |
| `installation-template` | Local command interface, packaging rules, installation behavior, and delivery workflows |
| `installer` | Existing public bootstrap, release delivery, and download infrastructure for `install.aixand.org` and `downloads.aixand.org` |

An adopting project would merge the relevant pieces. Existing policy checks,
license requirements, protection settings, and working project commands remain
authoritative until deliberately reconciled during adoption.

The [repository file policy](REPOSITORY_FILES.md) excludes tracked coding-assistant
instructions and configuration. Install the per-clone commit hook; CI enforces
the same rule across introduced commits. Product skill/prompt assets remain valid.

## AI-assisted development

AI tools have been used during the
project's development. Otherwise remove or revise this section accurately. -->

AI tools have been used during development of this template. All contributions,
including AI-assisted contributions, must meet the project's contribution,
review, and licensing requirements.

AI-generated output must not be assumed to be original or free of third-party
restrictions. Contributors must review their submissions, have the right to
contribute them, identify known third-party sources, and preserve applicable
licenses and notices.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution requirements and
instructions for reporting ownership or licensing concerns.

Original template material uses [Apache-2.0](LICENSE). Fixture package versions
are synthetic test data, not published releases.
