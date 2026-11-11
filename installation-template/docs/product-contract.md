# Revision-2 product contract

Workspace configuration describes source builds. Release manifests describe
immutable artifacts. Store receipts describe installed ownership. Artifact
operations never load source build commands.

## Topology and adapters

A workspace declares components, independent products, and product groups.
Product IDs are stable paths such as `example-suite/tool`. The
`example-suite` group selects its independently installable members. Missing
references and dependency cycles fail.

| Component adapter | Result |
| --- | --- |
| `payload` | Declared files and/or structured build argv output |
| `python` | Backend-built wheel and declared dependency wheels |
| `cargo` | Selected locked binaries, resources, features, and toolchain |
| `legacy` | Existing schema-1 ecosystem packaging |

Build hooks are trusted project code, executed only by explicit source
operations. They receive `{root}`, `{source}`, `{output}`, `{target}`, `{python}`,
`{profile}`, and already-built `{component:ID}` paths. Cargo build defaults to
debug; package selects release. Python keeps its build backend.

Python components build on the selected native target. Cargo cross-builds
require the selected target toolchain; runtime proof still needs the target
host. External source roots are explicit and recorded. Source mutation during
packaging fails the release.

Product adapters `native`, `python`, `hybrid`, and `application` compose outputs.
Python installation resolves only the enumerated wheelhouse offline and rejects
missing/conflicting dependencies. Product `extras` maps distribution names to
selected extras. Variants declare alternative component/runtime/dependency and
command sets.

`version-from` derives a version from ecosystem metadata. Explicit group/product
versions identify assemblies. The helper never invents or bumps versions.

## Artifact identities

Product content identities bind versions, commands, files, runtimes, variants,
and installation behavior. Source provenance is bound by the containing
manifest digest. Provenance alone does not change an identical child's content
identity when an unrelated collection member changes.

The complete inventory records sizes/hashes. Product payloads reference
content-addressed objects; repeated content is stored once. Group manifests bind
exact child releases. Static verification does not execute verification hooks.

Schema-1 meanings remain stable. Schema 2 has separate release, store,
descriptor, and event schemas. The umbrella configuration schema accepts both
versions. `scripts/update_v2_schemas.py --write` regenerates the new schemas;
normal checks detect drift.

## Installation ownership

An explicitly marked store contains `installation-receipt.json`, `bin/`,
`helpers/`, `payloads/<product-id>/<selection>/`, and
`runtimes/<archive-sha256>/`. Private scope records its application owner.

Each product has current/previous selections. Python environments are created
at final versioned paths and are never moved to activate them. Installed
launchers use owned helper copies without depending on the source checkout.
Windows commands use native launchers with adjacent descriptors, preserving
arguments without shell parsing.

Source-built and supplied-artifact routes record different product origins.
Ordinary operations cannot adopt another origin or edit shell configuration.
Persistent state is separate from replaceable software.

Products may declare `license-acceptance = "LICENSE"`. Packaging binds the exact
license text and digest into that product's identity. Planning lists its path,
SHA-256, and whether the store already accepted that text. Installation requires
`--accept-license <sha256>` before creating a store; collections accept repeated
flags. An existing product keeps acceptance of unchanged text, while a changed
license needs new acceptance before replacement. Explicit `verify --install`
accepts declared texts for its disposable technical qualification only; it does
not record consent for another user's installation.

## Batch and lifecycle behavior

Planning inspects dependency closure and ownership without creating stores or
fetching product payloads. Conflicts prevent activation.

Each product prepares and verifies before activation. Journals recover the old
selection after interrupted activation. Batches retain completed work and
record interrupted requests; cross-product installation is not a single atomic
transaction. Groups become complete only after all required products succeed.

Direct installation marks a child explicitly selected. Group removal preserves
explicit children and products referenced by other products/groups. Upgrades
never run at application startup or query a moving latest endpoint.
Coordinated updates must preserve installed consumers' exact dependency pins.

Stateless rollback checks those pins. Stateful upgrades/rollback need declared
migration and backup policy. Prune/uninstall requires a stopped-process
declaration and removes owned software only. User data, shared runtimes,
helper caches, and retained current/previous selections are preserved as
applicable.

## Runtime and operation interfaces

Runtime definitions bind archive identity, target, executable, role, and layout.
Archives can be bundled or downloaded from HTTPS during explicit installation.
Extraction rejects escapes/special files and resolves supported internal tar
links without requiring Windows symlink privileges. Reuse checks inventories.

One runtime ID can declare a `targets` table, for example
`[runtimes.python.targets."windows-x86_64-msvc"]`, with a shared role/version and
target-specific URL or local archive, checksum, executable, and layout. Package
selection binds only the matching target's record.

Python products select a tested interpreter. A declared uv runtime can install
their wheelhouse; otherwise a compatible interpreter with venv/ensurepip can
perform offline installation. Embedding receives Python home/library and
site-packages placeholders.

`--events jsonl` emits checking, runtime preparation, download measurements when
available, installation, verification, reuse, activation, interruption, and
completion records plus a final result. Logs remain on stderr. A request ID
binds its inputs and completed-product journal.

## Publication and platform boundary

`export-release` emits a validated descriptor and exact artifact bytes without
publishing. Public catalog resolution and hosted endpoints are later
integrations. Local packaging does not require them.

`verify --report` writes evidence for the exact manifest digest, target, helper
interpreter, and selected checks. `export-release --report` binds and copies that
evidence; its descriptor distinguishes static validation from installation
proof. Reports are local evidence, not publisher signatures. Build records
capture actual tool versions. Declared and discovered first-party LICENSE/NOTICE
files travel in product payloads; projects remain responsible for their complete
third-party notice set.

Every advertised OS/architecture needs native installation/runtime evidence and
a declared system baseline. A generated script, cross-build, or CI workflow
file alone is not qualification.
