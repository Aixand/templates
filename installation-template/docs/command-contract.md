# Proposed command contract

Status: shared behavioral specification. The first helper implements a subset
of the broader option/profile surface; [V1.md](../V1.md) and [SETUP.md](../SETUP.md)
define the actual capabilities and fail explicitly for unsupported operations.

## Entry points and capabilities

Every independently maintained project root supplies `dev.sh`. Native Windows
projects also supply `dev.ps1`. A workspace root may select and coordinate
components; each library module or internal Cargo crate does not need a wrapper.

Both wrappers expose the same operations and forward arguments consistently.
They locate the project from their own path, preserve the caller's environment
unless a documented operation requires an isolated one, and work from other
working directories. Support paths containing spaces and Unicode.

The project declares supported operations, components, variants, host platforms,
and release targets. All standard command names are recognized. An unsupported
command returns an explanatory nonzero result. CI selects declared capabilities
instead of invoking an unavailable operation and treating a skipped result as a
passing check.

Use existing tool implementations through adapters. The specification does not
require projects to implement identically named internal shell functions.

## Commands

| Command | Behavior | Changes allowed |
| --- | --- | --- |
| `help` | Describe operations, capabilities, requirements, and applicable options | None |
| `doctor` | Inspect manifests, available tools, versions, sources, runtime companions, and command selection | None; no dependency fetch or repair |
| `develop` | Prepare the contributor environment from declared locked inputs | Local environments, configured tool/dependency downloads, build caches |
| `check` | Run configured formatting checks, linting, type checks, and static checks | Disposable files and tool caches; no source rewriting |
| `test` | Run the documented default deterministic test suite | Disposable test data and declared local test artifacts |
| `build` | Produce local outputs without installation | Build directories and caches |
| `package` | Build if needed, assemble, and statically validate distribution outputs | Build/package directories and generated manifests |
| `verify` | Check supplied package identity, hashes, contents, metadata, and compatibility | Temporary inspection files; does not install into a user's prefix |
| `install` | Install a new source-built or explicitly supplied verified artifact | Selected managed software prefix and receipt |
| `reinstall` | Prepare and verify a replacement for an owned installation, then activate it | Owned software payload and receipt; preserve state |
| `uninstall` | Remove only the selected managed installation | Owned software paths and command links/shims; preserve state |
| `publish` | Publish a selected release through an explicitly configured adapter | Chosen registry/release destination; no implicit enablement |

No arguments, `help`, and `--help` display help. Help does not provision tools.
`publish` is optional, has no default destination, and is never called by a
normal build, install, package operation, or pull-request workflow.

`doctor` reports a missing requirement without repairing it. Its suggestions can
include the explicit preparation or tool-install command. It checks whether a
selected command on PATH refers to this installation and reports competing
installations without deleting them.

`develop` can download explicitly declared developer tools and dependencies.
It must not update the dependency lock, use administrator privileges, silently
change the user's default toolchain, or start application services. Missing
system compilers/libraries produce actionable setup instructions.

`check` never performs formatting fixes. Formatting can have a separate explicit
project command. Projects without a relevant checker disclose that fact during
adoption instead of claiming a check exists.

`test` excludes paid/provider/model-network tests by default. Projects may name
additional suites through `test --suite NAME`. Integration suites use isolated
homes, ports, and owned processes and document external requirements.

## Build and package defaults

- Rust `build` uses the normal development profile. `build --release` uses the
  selected optimized profile. Python builds use the declared package backend.
- `package` produces distributable outputs with release settings. It records
  selected components/features and performs static package verification.
- For Python, release settings mean the distribution policy and independent
  build checks; they do not imply a special native optimization mode or a version
  bump for pure Python.
- Packages are written to a documented output directory and identified by a
  generated manifest. They never appear in an installation prefix as a side
  effect of building or packaging.
- Reuse configured ecosystem caches and respect relevant overrides such as
  `CARGO_TARGET_DIR`. Do not force unrelated projects into one unqualified build
  output directory or a machine-specific absolute cache path.
- Native build success and native runtime qualification are recorded separately.

## Verification and installation tests

`verify --artifact PATH` performs structural and integrity verification. It must
not execute downloaded project hooks or an arbitrary verifier named by an
untrusted manifest. Format-specific verifiers are part of the trusted adapter
or are pinned by the authenticated release policy.

`verify --artifact PATH --install` additionally creates a disposable prefix or
environment, installs the artifact, and executes the project's declared smoke
checks. The project explicitly opts into the checks it runs. Generated reports
distinguish static verification from executed installation/runtime checks.

Release validation requires the installation mode for installable products.
Library profiles verify installation into a fresh consuming environment and
their public API/package resources. Compile and run a consumer for a Rust
library where applicable. These checks must not depend on the original checkout
being importable or available on the target machine.

## Common options

Options exist only where meaningful, but use the same spelling and meaning
where supported. Unknown or inapplicable options are errors.

| Option | Meaning |
| --- | --- |
| `--help` | Show command-specific help |
| `--release` | Select release build settings; does not publish |
| `--component NAME` | Select a declared component of a multi-component project |
| `--variant NAME` | Select a declared feature/runtime variant, such as base or SDK |
| `--target TARGET` | Select a declared build/release target, with an explicit mapping to ecosystem target identifiers |
| `--artifact PATH` | Use a prebuilt package or package manifest instead of implicitly building source |
| `--install` | For `verify`, additionally exercise installation and smoke checks in a disposable location |
| `--prefix PATH` | Select the managed product software prefix |
| `--environment PATH` | Select an existing or explicitly created consumer environment for a Python library |
| `--python EXECUTABLE` | Select an explicit compatible interpreter for an applicable Python operation |
| `--editable` | Explicit Python source linkage, only for supported development/source-install operations |
| `--dry-run` | Describe a planned mutation without building, installing, updating pointers, or publishing |
| `--json` | Produce the declared machine-readable result for metadata/lifecycle commands |

Document the supported option matrix for each backend. Reject unsupported flags
instead of silently ignoring them.

V1 also provides artifact `upgrade`, stateless `rollback`, and explicit `prune`.
See [the lifecycle defaults](lifecycle-decisions.md) for their semantics and the
required stopped-process declaration before destructive software removal.

Dry-run may resolve remote metadata when documented, but cannot provision tools
or download/install product payloads. It must explain which checks would still
need execution; a plan is not an installation proof.

Machine-readable results go to stdout; progress and subprocess logs go to stderr.
Receipts and reports include schema versions. Never dump credentials, full
environment contents, or authenticated URLs into reports.

Recommended exit codes are 0 for successful completion, 1 for a failed operation,
2 for invalid usage or an unsupported capability, and the platform-appropriate
interruption status. Forward failed subprocess results as a nonzero outcome.

## Source installation

`install` defaults to a standalone, non-editable installation from the current
checkout. Native source installations use release settings. `--editable` is an
explicit exception supported by appropriate Python profiles.

New installation fails when the selected command or software root is owned by
another route or project. Updating an owned installation uses `reinstall`.
Repeated identical installs may return an explicitly reported verified no-op;
they must still validate ownership and recorded identity.

A local source receipt records package versions, source origin, revisions,
whether inputs were dirty, a digest of the actual selected source inputs,
lockfile identities, features, and installed artifact hashes. Two different
source builds with the same package version must remain distinguishable.

If a source install selects local dependency overrides, build or otherwise
identify those exact dependency inputs as well. An index package with the same
version string must not silently substitute for a selected changed local package.

Local source install and public install should use compatible payload semantics,
but have distinct recorded origins. An installation from one route must not be
silently adopted or removed by another. Migration/takeover needs an explicit,
documented operation rather than a blanket force flag.

## Prefixes, activation, and replacement

Use a private user installation by default. The exact default paths are platform
specific and documented; existing product state paths are preserved. Separate:

- versioned software payloads and their receipts;
- command links or shims;
- build/download caches;
- product configuration and persistent state.

Installed command launchers must let the product finish its own shutdown.
On POSIX, replace the launcher process so terminal and termination signals reach
the product directly. Windows console wrappers must remain alive while the
product handles Ctrl-C or Ctrl-Break in the same process group, then return its
exit status. Qualification must exercise shutdown through the public command.

Create and verify a new payload before changing the active installation. Lock
mutations so concurrent installers cannot mix versions. A multi-binary product
activates the complete compatible set through a common selection mechanism, or
requires stopped processes if the platform cannot provide the needed transition.
Do not describe a sequence of unrelated file copies as an atomic bundle switch.

Python environments must be created at their final versioned location. Their
launchers can embed absolute interpreter paths; moving a populated environment
as an ordinary directory rename is not a portable activation mechanism. Switch
the active reference or shim instead.

If preparation fails, retain the previous active payload. If activation partly
fails, restore the previous selection or leave a clear recoverable state. Keep
the evidence needed to distinguish those outcomes.

Running processes may keep old binaries or imports after a successful switch.
Apply project-specific stop/restart policy and report what remains running.
Never kill processes using a broad name match. An automatic restart, if offered,
must be an explicit option limited to processes the project owns.

Retention of an older software payload does not establish that rollback of a
database migration is safe. Stateful upgrades need their own documented migration
and backup compatibility policy.

## Uninstall and independent operations

Uninstall removes paths only after validating the ownership receipt. Refuse
unexpected directories, redirected paths, or changed commands. A version string
alone is not proof of ownership. An absent installation can return an explicit
successful already-absent result.

Preserve databases, models, indexes, credentials, projects, and integration
configuration. Destructive data removal, if ever offered, is a separate command
with a clearly stated scope.

Services and resource setup can expose project-specific operations such as
`run`, `stop`, `prepare`, or `register`. Their help must describe effects. The common
contributor command is `develop`; preserve an existing `setup` command when it
already performs project-specific preparation.

Shell PATH modification is explicit and reversible. Otherwise print the exact
directory to add. Provisioning a managed interpreter must not silently replace
the user's default Python or Rust toolchain.

See the [profile definitions](../profiles/README.md) for ecosystem differences
and [validation entry points](../V1.md#validation-entry-points) for the lifecycle tests.
