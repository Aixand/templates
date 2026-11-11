# Accepted defaults and first-version boundary

The schema-1 capabilities and limits are listed
in [V1.md](../V1.md); this document does not confer publication authority.

## First version

The shared interface, Python library/tool profiles, Rust library/CLI profiles,
selected Cargo workspace packages, and profile-specific CI/release examples are
the first implementation scope. A custom profile exposes real commands for
other languages without pretending to provide an ecosystem packager.

Multi-binary products, coordinated external source repositories, embedded Python,
native Python extension wheels, model preparation, installer-managed interpreter
bootstrap, and full application collection deployment remain later adapters. Existing project
helpers remain in place until their supported behavior is qualified through a
deliberate migration.

## Updates and pinning

- `reinstall` rebuilds the selected source checkout or uses an explicitly supplied
  artifact. The receipt identifies the exact input set.
- `upgrade --artifact PATH` selects a verified packaged version. The first helper
  does not query a remote latest endpoint. The public installer will own remote
  resolution when its integration is implemented.
- An installation stays on its exact selected payload until an explicit operation
  changes it. Application startup never triggers an update.
- Keep current and previous selections. Replacing software does not restart old
  processes automatically; report restart requirements and retain old payloads.
- Rollback requires an explicit `stateful = false` declaration in the initial
  helper. Stateful products require an adapter that understands their migration
  and backup compatibility; retaining old software alone is insufficient.
- `prune --dry-run` lists payloads outside the current/previous selections.
  Actual pruning and uninstall require `--stopped`, an explicit operator statement
  that users of the removed software have stopped. V1 does not claim to discover
  every Python process or prove runtime liveness automatically.
- Cleanup removes only receipt-owned payloads. Shared uv interpreters/caches and
  persistent product data are never collected by this helper. A future shared
  runtime collector needs its own complete ownership/reference policy.

## Broken published releases

1. Failed qualification blocks publication/promotion. Failure after a destination
   accepted an upload records a partial release and leaves stable unchanged.
2. If a broken version was already promoted, explicitly restore a compatible
   known-good stable pointer, or pause that channel if no suitable version exists.
   Changing discovery metadata does not downgrade existing installations.
3. Record the affected identity, reason, recommended replacement, and any state
   recovery constraints. Keep historical artifact identities and verification
   evidence; do not replace bytes under the same version.
4. Publish a corrected version. Withdraw the broken registry version when
   warranted using the registry's supported procedure, with an explicit
   maintainer action. Tests do not automatically yank production packages.
5. Warn consumers of pinned/locked versions as part of the release advisory;
   registry withdrawal is not an automatic repair mechanism.

PyPI yanking leaves releases available for qualifying exact pins. Cargo yanking
does not invalidate existing lockfiles or remove downloadable bytes. Follow the
actual registry behavior: [PyPI yanking](https://docs.pypi.org/project-management/yanking/)
and [Cargo yanking](https://doc.rust-lang.org/cargo/commands/cargo-yank.html).

## Configuration and qualification

Use `installation.toml` for the helper's selected profile, runtime, verification
and command hooks. Ecosystem manifests remain authoritative for package identity
and dependency metadata. Generate JSON release manifests and selection receipts;
the schemas are versioned and reject unknown formats.

Run the [template checks and tests](../V1.md#validation-entry-points) in disposable
directories. Validate each adopting project on its supported platforms. Local
tests do not establish registry publishing or production installer integration.
