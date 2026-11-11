# Try and adopt the first implementation

For product collections, native bundles, hybrid applications, or artifact-only
installation, start with [Revision 2](V2.md) and its
[product contract](docs/product-contract.md). The original schema-1 adoption
instructions below remain valid for their selected ecosystem profiles.

Read [V1.md](V1.md) for actual capabilities and remaining work. These instructions
do not configure a production publisher or modify another project automatically.

This repository follows [REPOSITORY_FILES.md](REPOSITORY_FILES.md). Coding-assistant
instructions and configuration must stay out of tracked files. Install the local
guard with `python3 scripts/checks/install-file-policy-hook.py`, or integrate it
with an existing hook manager. Use the open-source template's baseline for the
same policy when adopting installation helpers in another project.

## Try a disposable project

The developer helper requires Python 3.11+. Python profiles use uv, tested here
with 0.12.7. Cargo source operations use rustup to honor the declared toolchain
even when the host has a different default or environment override. Cargo
fixtures pin Rust 1.98.0. Normal Rust projects select their own
exact tested toolchain in `rust-toolchain.toml`.

From this template checkout on Linux, choose a new destination outside it:

```sh
python3 scripts/render_fixture.py python-tool /tmp/installation-python-example
cd /tmp/installation-python-example
./dev.sh doctor
./dev.sh develop
./dev.sh check
./dev.sh test
./dev.sh package --output /tmp/installation-python-package
./dev.sh verify --artifact /tmp/installation-python-package --install
./dev.sh install --artifact /tmp/installation-python-package --prefix /tmp/installation-python-prefix
/tmp/installation-python-prefix/bin/fixture-tool --self-test
./dev.sh uninstall --prefix /tmp/installation-python-prefix --stopped
```

The three `/tmp/installation-python-*` destinations must be unused. Pick another
name when retrying a package build: package outputs are not overwritten. The
fixture renderer refuses an existing destination and copies synthetic test
application code; it is a playground, not the adoption procedure for a real app.

Repeat with `rust-cli`, `rust-library`, `rust-workspace`, or `python-library`.
Library profiles use `verify --install` for independent consumption; normal
library installation belongs in a selected consumer's package manager.

## Adopt in an existing project

1. Inspect its agent instructions, working changes, manifests, toolchains,
   lockfiles, helpers, workflows, state paths, and release procedures. Preserve
   unrelated changes and existing platform support.
2. Select one initial profile, or the generic custom command profile. Keep the
   project root around the whole source set needed for packaging. For a Cargo
   workspace, point `manifest` at the selected member's `Cargo.toml`.
3. Merge `files/dev.sh`, `files/dev.ps1` where applicable, and
   `files/scripts/dev/` into the corresponding project paths. Preserve executable
   permission on `dev.sh`. Do not copy fixture application code or this template's
   own README/agent instructions over the project's documents.
4. Adapt the selected `profiles/<profile>/installation.toml.example` as
   `installation.toml`. Fill its tokens, replace editing comments, and use actual
   commands. Merge `files/gitignore.example` with existing ignore rules.
5. Preserve the declared Python build backend or Cargo package boundaries.
   Include required licenses/resources through the backend's package rules;
   native CLI resource files are copied under `share/` in its payload.
6. Establish the checked-in lockfile through an intentional `uv lock` or
   `cargo generate-lockfile` operation. For Python, include actual check/test tools
   in its locked development group. For Cargo, retain or adapt the existing exact
   `rust-toolchain.toml`; the example is under `profiles/`.
   Pin isolated Python build requirements in `build-system.requires` as well:
   the runtime uv lockfile does not freeze an independently resolved build backend.
7. Run doctor, develop, checks/tests, package, static verification, and independent
   install verification. Exercise rejected input and a successful retry in a
   disposable prefix before managing an existing daily-use installation.
8. Merge the CI/release examples with existing workflows. Preserve DCO, secret
   scanning, license checks, pins, hook integration, and repository protections.

Merge the current contribution and PR policies from
[the open-source template](https://github.com/Aixand/open-source-template) when
standardizing an adopting project, including human review, substantial AI-use
and third-party source disclosures, and private ownership/licensing reports.
Include the README's AI-development disclosure only when it accurately describes
the project. Preserve existing project policies and development instructions.

Token choices in the profile examples are `PYTHON_VERSION`, `IMPORT_NAME`,
`LIBRARY_ASSERTION`, `COMMAND_NAME`, `RUST_CONSUMER_MAIN`, `RUST_VERSION`, and
`PROJECT_NAME`. Use the ones present in the adopted file, with real project
values. Preserve helper placeholders such as `{python}`, `{root}`,
`{venv-python}`, `{payload}`, `{output}`, and `{command:your-command}`. These
single-brace placeholders are expanded as arguments, never shell code.

The configuration examples use Ruff and unittest as actual starting commands;
replace them when the project uses other tools. Rust defaults run rustfmt,
Clippy, and Cargo tests for the selected package/features. Custom argv hooks can
run npm, other languages, or a reviewed project script. Shell operators in an
argv array are literal; use a project script for multi-step shell behavior.

## Actual option and installation behavior

- `build --release` selects Cargo release settings; Python builds use their
  backend. Cargo output location uses `CARGO_TARGET_DIR`; `--output` is for
  package and Python/custom build outputs.
- `package --output PATH` creates a new immutable artifact directory. The default
  is `dist/package`. `verify --artifact PATH` checks its local integrity;
  `--install` adds an independent consumer/smoke test.
- V1 Python wheelhouses use a specific `python.version`, pure-Python project
  wheels, and locked registry dependencies. Local/Git overrides, extras/variant
  packaging, and native project wheels need later adapters.
  Release manifests record the actual helper/compiler/uv and wheel generator
  versions, plus the selected Python implementation/minor/platform/SOABI.
- V1 Cargo native packaging selects one binary. `--target` applies to native
  builds/packages; execution verification requires the matching host. Cargo
  library packaging performs native Cargo verification and requires
  `verification.consumer` for the consuming application.
- `install` builds a standalone source package by default. `--artifact PATH`
  selects an existing verified package. `reinstall` replaces an owned selection;
  `upgrade --artifact PATH` explicitly selects another packaged version.
- Managed prefixes are Unix-only initially. The default is
  `$XDG_DATA_HOME/aixand/source/<package>` or
  `~/.local/share/aixand/source/<package>`, with commands in its `bin/` directory.
  Print/add that directory to PATH explicitly. Existing unrelated prefixes and
  commands are refused. Product state should live outside this software prefix.
- `rollback` requires `install.stateful = false`. `prune --dry-run` lists retired
  payloads; actual pruning and uninstall require `--stopped` after users of that
  software have stopped. Shared runtimes and user data are preserved. Ownership
  metadata and the lock remain so repeated operations retain provenance.
- Supported lifecycle results are JSON on stdout, with subprocess logs on stderr.
  `--json` documents that format. Dry-run mutations do not build/install software.
  Unknown or inapplicable options fail; editable global installs, component/variant
  selection, direct consumer-environment installs, and generic publish are
  explicitly unsupported in the first helper.

## Enable CI and publishing deliberately

Adopt `examples/workflows/ci.yml.example` for an initial Python/Cargo profile.
It uses the real project helpers and installs selected tools. A custom pipeline
must adapt the packaging/verification steps to its declared capabilities.

Choose only the relevant release example:

| Example | Destination filename | Required setup |
| --- | --- | --- |
| `publish-python.yml.example` | `.github/workflows/publish-python.yml` | PyPI project ownership, Trusted Publisher for this filename, `pypi` environment/ref policy |
| `publish-crate.yml.example` | `.github/workflows/publish-crate.yml` | Selected public crate, available registry dependencies, crates.io ownership/Trusted Publisher, `crates-io` environment/ref policy |
| `publish-native.yml.example` | `.github/workflows/publish-native.yml` | Qualified native target, GitHub Releases, attestation availability, `native-release` environment/ref policy |

Keep each example's filename or update matching registry/provenance identities.
The examples use version tags `v<canonical-package-version>` and checkout the
event commit. Source must be clean and the tag must identify that commit. They
do not create tags. Monorepo component tags require a deliberate adaptation.

Python publication transfers verified wheel/sdist bytes to a dedicated OIDC job.
Cargo publication deliberately re-packages/verifies the same clean source,
compares package file inventories, publishes the selected crate, then confirms
the registry contents. It is not a prebuilt arbitrary-archive upload.

Native publication stages exact verified files with latest disabled, confirms
the public manifest against the verified run, verifies provenance identity, and
executes an isolated installation. Only a newer stable version is then promoted.
The example covers one Linux target; choose the actual supported OS/libc baseline
and add native target jobs before promising more. Prereleases do not become stable.

Use existing governance for any required reviewers. Copying files does not
register publishers, grant registry ownership, configure protections, upload to
Aixand storage, or qualify a platform. Authorized repository setup/releasing is
a separate task from local template implementation.

## Validate and maintain this template

```sh
./dev.sh develop
./dev.sh check
./dev.sh test
actionlint .github/workflows/*.yml examples/workflows/*.yml.example
```

For Linux x86_64 without actionlint, install the checksum-pinned tool into a new
temporary path and invoke that path:

```sh
python3 scripts/install_actionlint.py --output /tmp/installation-actionlint
/tmp/installation-actionlint .github/workflows/*.yml examples/workflows/*.yml.example
```

Other platforms should install actionlint through their normal tool setup.
Tests use disposable projects/prefixes outside this repository. They publish
nothing. Record helper revision 1 when adopting; review updates explicitly.

If the default temporary filesystem has a small quota, set `TMPDIR` to a writable
temporary directory on a larger filesystem before running tests or packaging.
The helper honors `TMPDIR` and `CARGO_TARGET_DIR`; neither requires moving or
deleting an application's existing build cache.
