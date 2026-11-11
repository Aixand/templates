# Project profiles

[Revision 2](../V2.md) implements the bundle, coordinated-package, hybrid, and
composed-application paths through the `workspace` profile and component
adapters. Use [its example](workspace/installation.toml.example) for those
products. The original profiles and their schema-1 behavior remain available.

The Python library/tool and Rust library/CLI directories contain
configuration examples; `custom/` supplies a generic command example. Follow
[SETUP.md](../SETUP.md) for adoption. The multi-binary, hybrid, and dedicated
web/service profiles below describe later adapters. [V1.md](../V1.md) records
the implemented surface and qualification limits.

All profiles share the [command contract](../docs/command-contract.md) and the
[release contract](../docs/release-contract.md). A project may combine profiles
through declared components and variants.

## Python library

- Identity/dependencies/build backend come from `pyproject.toml`.
- uv manages the contributor environment and checked-in validation lockfile.
- Produce a wheel and source distribution for index publication.
- Test a clean consuming environment, public imports, and required package data.
- Install into a selected consumer environment; no global command or private tool
  environment is required.
- Publication to PyPI or another index is explicitly configured.

Fixture: a small library with a resource file and an independent consumer.
Native runtime requirements must be declared independently from the Python SDK.

## Python tool

Add CLI entry-point verification, private tool environments, command ownership,
and the install/reinstall/uninstall lifecycle to the Python library requirements.

Support ecosystem installation through pipx/uv after publication and, where
selected, the Aixand product route with managed compatible Python and a complete
verified wheelhouse. The installed CLI environment is distinct from an SDK
environment used by a consuming application.

Python packages retain their runtime and platform constraints; packaging alone
does not establish Windows or macOS compatibility.

## Rust library

- Cargo owns crate identity, targets, dependencies, features, and publishing
  restrictions. Select public workspace members explicitly.
- Pin the tested project toolchain and keep a lockfile for project validation.
- Test chosen feature combinations; test minimum Rust separately if advertised.
- Use Cargo package verification and a real consuming crate.
- Registry publication requires registry-ready dependencies and dependency order.
- A global executable installation is unsupported when there is no executable.

Fixture: a small public API crate, a consumer, and a two-crate workspace
demonstrating path-plus-version dependency development and publication readiness.

## Rust CLI

Add selected binaries, locked optimized product builds, native archives, command
ownership, installation receipts, and target runtime checks.

Publish binary downloads without requiring crates.io publication. If a selected
CLI crate is also published, test the advertised Cargo installation route using
its actual registry package name; the executable name may differ.

Keep repository preparation and service registration separate from binary
installation.

## Rust bundle

Extend the Rust CLI profile with a complete compatible binary set, supporting
libraries/resources, product-specific structural verification, and coordinated
activation. Installation of one executable alone must not count as product
installation.

Preserve platform-specific bundle checks. Declare SDK bridges as runtime
components instead of inferring them from Python package installation.

## Hybrid product

Select component profiles, build order, complete source inputs, and a runtime
compatibility matrix. Generate one product manifest referring to the tested
component artifact set. Component versions can differ when the mapping is explicit.

Embedded Python requires coordinated interpreter, shared-library, and package
versions. A Python extension wheel uses its own build backend and distribution
contract.

## Web/service

Keep the existing package manager, lockfile, and application scripts. Adapt
`develop`, `check`, `test`, `build`, and `package` to those tools. A parent project
can assemble native and Python components through the same interface.

Define whether `install` has a meaningful local application installation. If it
does not, report that capability as unsupported. Containers, hosting, service
registration, migrations, and deployment are explicit extensions with selected
destinations and verification.

Declare resource preparation explicitly. A Python zip application still requires
a compatible interpreter unless the distribution includes one.

## Capability summary

| Profile | Local development/build | Package + verify | Managed product installation | Registry publishing | Other delivery |
| --- | --- | --- | --- | --- | --- |
| Python library | Required | Required | Consumer environment | Optional selected Python index | Optional wheel distribution |
| Python tool | Required | Required | Private tool environment | Optional selected Python index | Optional product wheelhouse |
| Rust library | Required | Required | Unsupported without executable | Optional selected Cargo registry | Optional source package |
| Rust CLI | Required | Required | Native command payload | Optional eligible Cargo package | Native downloads |
| Rust bundle | Required | Required | Complete native product | Optional selected public crates | Native downloads |
| Hybrid | Required per component | Required for assembled product | Declared component/runtime set | Selected component registries | Product downloads |
| Web/service | Required | Required for chosen output | Project-specific capability | Optional package/container registry | Explicit hosting/deployment |

“Optional” means publication is chosen during adoption, not that an enabled
publisher may omit its validation or authentication requirements.
