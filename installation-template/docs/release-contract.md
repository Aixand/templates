# Proposed release and GitHub Actions contract

Status: release specification with initial workflow examples in
`examples/workflows/`. Those examples require adoption and real registry setup;
no production publisher or remote workflow result is established by this file.

## Distribution destinations

| Profile/output | Destination | Typical consumption |
| --- | --- | --- |
| Python library wheel/source distribution | PyPI or selected Python index | pip/uv into an application environment |
| Python CLI wheel/source distribution | PyPI or selected Python index | pipx or uv tool installation |
| Python product wheelhouse | Aixand downloads or selected artifact storage | Product installer with verified, predetermined runtime wheels |
| Rust library or intentionally published CLI crate | crates.io or selected Cargo registry | Cargo dependency or `cargo install` |
| Rust CLI/native bundle | GitHub Releases and/or Aixand downloads | Verified binary/product installer |
| Hybrid product manifest and component packages | Explicit combination of destinations | Product installer resolving the compatible artifact set |
| Web assets/container | Project-selected hosting or registry | Explicit deployment |

PyPI and crates.io hold different package formats. pipx is an installation
client, not a publication destination. A project can support both an ecosystem
package and an Aixand product bundle without creating a new source implementation.

## Workflow responsibilities

### Normal CI

The proposed `.github/workflows/ci.yml` runs on pull requests and configured
default-branch changes. Its profile-specific jobs:

1. Install the pinned helper/runtime/toolchain prerequisites.
2. Prepare the project using locked dependencies through `develop`.
3. Run the project's declared `check` and `test` operations.
4. Validate its normal build and appropriate distribution formats.
5. Exercise disposable installation for installable products.
6. Retain useful reports with an appropriate retention period.

These jobs run without publication credentials and do not publish packages,
push tags, update stable pointers, or deploy services. Native Windows jobs use
`dev.ps1`; Unix jobs use `dev.sh`.

Fast PR jobs and broader compatibility jobs can be separate. Every platform and
runtime combination advertised for a release must have appropriate release
qualification. Declare actual check names before requiring them in repository
protection settings.

### Release orchestration

The proposed `.github/workflows/release.yml` accepts an intentional version tag
or explicit manual release request identifying a specific revision. It selects
profile-specific packaging and publishing jobs; it does not run every publisher
for every repository.

The workflow is separate from `.github/release.yml`, which only configures
generated GitHub release notes.

| Stage | Required result |
| --- | --- |
| Preflight | Valid version/tag mapping, intended clean source, allowed destinations, dependency readiness, declared target matrix |
| Check/test | Required project validation for that revision and variant |
| Build/package | Outputs with explicit source/toolchain/dependency/target identities |
| Verify | Package checks plus installation/runtime evidence on the declared targets |
| Attest | Provenance linked to the verified artifact hashes where supported |
| Publish | Upload to the explicitly configured destinations |
| Confirm | Verify the specific published version and required install route |
| Promote | Update a stable download pointer only after all required checks pass |

Calling an existing public installation endpoint without publishing the selected
version first cannot establish that the new release works. Conversely, a public
health endpoint does not establish package availability or installability.

## Shared workflow rules

- Use the same package and verification helpers locally and in Actions. YAML
  selects runners, installs declared tools, connects jobs, and handles credentials.
- Pin third-party actions and reusable workflows to immutable commits and record
  their intended upstream versions. Define maintenance for those pins.
- Use read-only repository permissions by default. Grant publication and OIDC
  permissions only to jobs that require them; attestation permissions belong to
  the attestation-producing job.
- Bind release jobs to the configured source/tag policy and registry publisher
  identity. A manual ref input must not bypass that policy or enter a shell as
  executable text.
- Keep privileged publication separate from executing pull-request code. Never
  call project helpers under `pull_request_target`; preserve the trusted-base
  metadata-only DCO workflow from the open-source template.
- Serialize publication for a product/version/destination. Do not cancel an
  in-progress publisher just because a newer run started.
- For Python and native bundles, publication consumes the verified artifact bytes
  from the same release run. Artifact transfer includes digest/identity checks;
  do not fetch an unrelated run's artifact using only a familiar filename.
- Fail a version/tag mismatch. Compare versions using the ecosystem adapter:
  Python prerelease normalization and Cargo SemVer are not identical string
  formats. Explicit product/component mappings are allowed and recorded.
- Stable and prerelease channels have separate promotion rules. Releasing a
  prerelease must not update stable latest.
- Preserve license texts and reviewed third-party notices in the actual shipped
  formats. Keep existing project-specific verification at least as strong.

## Python release profile

1. Read package identity and Python requirements from `pyproject.toml`.
2. Build wheel and source distribution with the declared backend; check that the
   build works without local development source overrides.
3. Check distribution metadata and required resources. Test installation from
   the wheel outside the source tree, including declared CLI commands/imports.
4. Check dependency resolution against the intended index or assembled release
   wheelhouse. A development lock and editable workspace do not establish that
   those dependencies exist on PyPI.
5. Publish internal packages in dependency order when the selected index route
   needs them. A dependent package waits for required versions to be available.
6. Transfer verified distributions to a dedicated publisher job and use PyPI
   Trusted Publishing when the project is configured for it.
7. Verify installation of the pinned published version in an isolated environment.
   For a CLI, test the advertised pipx/uv route without taking over normal user
   command directories. Libraries use a consumer environment.

PyPI installation normally resolves compatible runtime dependencies from package
metadata. It does not reproduce every version in a contributor's `uv.lock`.
An Aixand product wheelhouse is the route for a predetermined dependency set.

For that route, assemble a complete wheelhouse per supported OS/architecture,
Python implementation/minor version, and ABI where necessary. Native wheels
must be compatible with their target and declared OS/libc baseline. A universal
top-level wheel does not make all transitive dependencies universal.

The manifest binds every wheel and selected variant. Product installation uses
only verified wheels, performs no source compilation, validates dependencies,
and runs smoke checks before activation. Unexpected direct URL dependencies or
undeclared network resolution must fail the controlled wheelhouse route.

PyPA recommends separate build/publishing jobs and supports Trusted Publishing:
[GitHub Actions publication](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

## Cargo library and crate publication profile

1. Select the actual public crates from Cargo metadata, respecting `publish`
   restrictions. Do not automatically publish every workspace member.
2. Verify crate metadata, included files, licenses/resources, feature selection,
   and registry dependency requirements.
3. Run Cargo packaging verification for the selected source and target policy.
   Test a consuming project against the intended package surface.
4. Determine dependency release order. Crates needed from the registry must be
   available when Cargo's package verification resolves them.
5. Publish from the same clean release revision through the configured registry
   adapter, preserving Cargo's verification. Do not use `--no-verify` to conceal
   an incomplete dependency release or broken package.
6. Confirm the selected crate versions are available and the advertised consumer
   or `cargo install --locked` route works where supported.

Cargo's `publish` command creates and verifies its package; it is not a generic
uploader for an arbitrary `.crate` file from an earlier job. The implementation
must specify how it preserves source, package selection, lock inputs, and
verification across this step. Do not promise byte-identical re-packaging unless
the implemented workflow has demonstrated it.

For coordinated crate releases, run local validation before publication and
perform registry-dependent package verification in dependency order. A parent
crate's final registry verification may need to wait for a new prerequisite
crate to be published. Report that staged sequence accurately; if a later crate
fails, earlier published versions remain immutable and the release is partial.

Use crates.io Trusted Publishing where configured. Initial crate creation,
ownership, and publisher enrollment are explicit setup items governed by the
registry's current rules. Do not assume a namespace is available or pretend a
dry-run has published it.

Cargo documents [package verification](https://doc.rust-lang.org/cargo/commands/cargo-package.html)
and [publication](https://doc.rust-lang.org/cargo/commands/cargo-publish.html).
The Rust project confirms [crates.io Trusted Publishing support](https://blog.rust-lang.org/2026/01/21/crates-io-development-update/).

## Rust native application and bundle profile

1. Build selected binaries with the pinned toolchain, locked inputs, target, and
   declared feature set. Include the build source identity in the release record.
2. Assemble the full product payload: executables, required native libraries,
   schemas, resources, licenses/notices, and installation metadata.
3. Check the supported target and ABI, file set, permissions, hashes, dynamic
   runtime requirements, and the declared minimum OS/libc baseline.
4. Install into a disposable prefix on the target platform and run meaningful
   version/help/configuration or isolated service checks.
5. Verify replacement behavior, command ownership, multi-binary consistency,
   state preservation, and uninstall. Exercise a failed package/install attempt
   followed by a successful retry.
6. Publish the verified bundle bytes and manifests to the chosen destinations.
7. Test the pinned published installation and promote the stable pointer last.

An end user installing a native release does not need a Rust compiler. If the
selected target is unavailable, fail clearly. Building from source is a separate
intentional route, not an automatic fallback with hidden compiler installation.
Any installer/verifier runtime prerequisite must still be declared and supplied.

Registry distribution through `cargo install` is an additional source-build route
for an eligible published tool, not a substitute for target-specific binary
qualification. A Rust library can be public without shipping any executable.

## Hybrid, web, and service publication

A hybrid release records the compatible component set and builds it in declared
order. Include companion executables and the selected Python runtime/packages
when required. Verify startup outside the developer workspace with no accidental
fallback to sibling sources or cached developer executables.

For embedded Python, test native library loading and imports on the real target.
For speech/model resources, distinguish bundled assets, explicitly prepared
downloads, their licenses/hashes, and persistent caches.

Web/service publication selects its own build assets or container output and
destination. Deployment credentials, migrations, service activation, and health
verification belong to an explicit deployment profile. Packaging never deploys
or changes a production database implicitly.

## Release metadata and identity

The release schema should describe:

- product/release identity and ecosystem package/component versions;
- source revisions and cleanliness, including coordinated external sources;
- selected components, variants, features, target triples, OS/libc/ABI limits;
- interpreter/toolchain and dependency lock identities;
- complete artifact filenames, sizes, hashes, formats, and command exposure;
- required runtime companions and selected dependency wheel sets;
- license/notice references, verifier identity, and provenance references;
- static verification and executed installation qualification results.

Generated metadata derives values from the actual build. Unknown schema versions,
unsafe paths, duplicate/conflicting identities, missing required artifacts, and
unsupported targets fail validation. A manifest must not provide arbitrary
installation code to execute with publication privileges.

The installation receipt records the selected release and artifact hashes,
installed paths, runtime, activation selection, ownership, and installation route.
Schema evolution must preserve previously published pinned releases and matching
verifiers.

## Publication failures and promotion

Multiple registries and storage services do not provide one atomic transaction.
Record which uploads and confirmations succeeded. A retry checks the destination
and only resumes operations consistent with the immutable release identity.
Never overwrite an existing version with different bytes, use blanket
skip-existing to hide differences, or advance latest after a partial required
publication.

For Aixand downloads: publish immutable version files, verify their manifest and
real installation through the download service, then update the stable pointer.
Do not couple release publication to redeploying the download Worker for each
ordinary new version.

## Certification, provenance, and setup

DCO metadata checks preserve contributor certification. Hashes check byte
integrity. Provenance attestations connect an artifact to its source/workflow
identity. Runtime tests check behavior. None of those substitutes for the others.

Generate release attestations where the repository/platform supports them and
define how consumers verify the expected signer and source. Preserve actual
evidence; do not claim a supply-chain assurance level from the presence of a
signing step alone. See [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations).

Adoption must configure actual package ownership, registry Trusted Publishers,
GitHub environments and allowed refs, credentials for destinations needing them,
and any required release reviews. Follow existing project governance. These are
configuration prerequisites, not a requirement to ask for redundant approval
within an already authorized setup task.

Published-install verification remains separate from local fixture success and
from repository protection checks. Report each result accurately.
