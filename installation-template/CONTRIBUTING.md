# Contributing to the installation template

Contributions, bug reports, and documentation improvements are welcome. Read
[README.md](README.md), [SETUP.md](SETUP.md), and [V1.md](V1.md) for the implemented
scope, adoption instructions, and remaining qualification work.

## Development and validation

Use Python 3.11 or newer and uv 0.12.7. From the repository root:

```sh
./dev.sh doctor
./dev.sh develop
./dev.sh check
./dev.sh test
```

`develop` synchronizes the locked development tools. `check` validates authored
files and links, renders profiles, checks schemas and workflow structure, and
runs Ruff. Tests use disposable projects and installation prefixes; they do not
publish packages. Follow [SETUP.md](SETUP.md#validate-and-maintain-this-template)
for workflow linting and temporary-directory requirements. Run the checks
appropriate to the change and report the results and any limitations accurately.

Keep changes focused, preserve existing project behavior and license notices,
and update documentation and tests when relevant. Record user-visible changes
under Unreleased in [CHANGELOG.md](CHANGELOG.md). Follow the
[repository file policy](REPOSITORY_FILES.md), including its per-clone commit
hook. Do not enable release publishing as part of an unrelated change.

## License and contribution rights

Original project contributions are accepted under the [Apache License 2.0](LICENSE).
Unless explicitly stated otherwise, contributions intentionally submitted for
inclusion are submitted under that license, as described in its Section 5.
Discuss any proposed exception with maintainers before submitting it.

You retain copyright in work you own. Contributing does not assign ownership to
Artificial Intelligence Advancement Initiative Inc., and this project does not
require a separate contributor license agreement (CLA). Apache-2.0 grants rights
to use, modify, and redistribute contributions subject to its terms; it is not
a promise to retain a particular contribution. Maintainers may edit, replace,
or remove code. A change of mind does not by itself revoke the license grants
already made under Apache-2.0.

Only submit material you have the right to contribute. Obtain any necessary
employer or other rights-holder permission. Identify copied or adapted material,
its source, and its license, and preserve required notices and attribution.
Third-party material remains subject to its applicable license; a project
license or sign-off does not erase those obligations.

## Ownership and licensing concerns

We respect third-party intellectual property rights and welcome good-faith
reports concerning code, documentation, images, or other material distributed
by this project.

Please send reports privately to
[corporate@aixand.org](mailto:corporate@aixand.org). Include, where available:

- The affected files, versions, or distribution URLs.
- The original work and its source.
- The rights or license conditions you believe are involved, and supporting
  evidence.
- Your relationship to the rights holder and a way to contact you.

Maintainers will review the available information and may request clarification.
When infringement or license noncompliance is substantiated, we will take
appropriate corrective action. Depending on the circumstances, this may include
correcting attribution or notices, satisfying license requirements, obtaining
permission, or replacing or removing the affected material.

We are willing to remove or replace material where we lack the necessary rights
to distribute it. Material used in compliance with a valid license does not
automatically require removal solely because a request is received. AI assistance
does not excuse infringement or failure to comply with an applicable license.

## AI-assisted contributions

AI assistance is permitted. The human contributor remains responsible for
reviewing and understanding the submission, checking its correctness and
security, and establishing the right to contribute it under the applicable
license. Do not submit generated material you cannot explain or adequately
assess.

When AI generates or substantially rewrites submitted code, documentation,
images, or other material, describe its role, the affected parts, and the review
and validation performed in the pull request. Routine spelling corrections and
trivial completions do not require separate disclosure unless relevant to a
licensing, security, or provenance concern.

Identify known copied or adapted material, including its source and license,
and preserve required attribution and notices. AI output is not evidence of
originality, ownership, permission, or license compatibility. If you cannot
establish sufficient permission to submit material, resolve the uncertainty
before submitting it.

Do not share credentials, private information, or material you lack permission
to disclose with an AI service. Public contribution descriptions must not expose
confidential prompts or other sensitive information.

AI-assisted and automated submissions require human review before acceptance.
Any required DCO certification must be supplied truthfully by the appropriate
contributor; an AI tool cannot provide that certification on someone's behalf.
Acceptance does not replace the contributor's obligations or the maintainers'
review responsibilities.

## Review

Use the pull request template to describe scope and validation. Maintainers may
request changes or decline a contribution based on correctness, security,
maintainability, project direction, or unresolved rights questions. Keep review
discussion constructive and allow time for community maintainers to respond.
