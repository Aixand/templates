# Contributing to {{PROJECT_NAME}}

Contributions, bug reports, documentation improvements, and questions are
welcome. Please follow the [code of conduct](CODE_OF_CONDUCT.md). Report suspected
vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## Getting started

Read the project's [README](README.md) and [documentation]({{DOCS_URL}}) for
installation, development setup, and test commands. Use the
[issue forms]({{REPOSITORY_URL}}/issues/new/choose) to report a reproducible bug or
discuss a substantial change before investing in implementation.

Keep changes focused, explain the problem and resulting behavior, and update
relevant documentation. Add or update tests when needed to verify behavior.
Run the relevant checks and state exactly what was tested and any limitations.
Remove credentials and private information from examples, logs, and screenshots.

For user-visible changes, add a concise entry under Unreleased in
[CHANGELOG.md](CHANGELOG.md), including migration steps when needed. Follow an
existing project release-note process if it replaces the single-file changelog.
Editor defaults are in `.editorconfig`; use the project's actual formatter and
lint commands, and keep unrelated formatting changes out of focused fixes.

Follow the [repository file policy](REPOSITORY_FILES.md): coding-assistant
instructions and configuration are not tracked. Install its per-clone commit
hook with `python3 scripts/checks/install-file-policy-hook.py`, or integrate the
checker with the existing hook manager. The same rule runs in CI and checks
every introduced commit. Product skill and prompt assets remain allowed.

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

## Developer Certificate of Origin

Read the [Developer Certificate of Origin 1.1](DCO). Every commit submitted in a
pull request must contain a `Signed-off-by` trailer matching the commit author's
name and email. Each declared co-author must also provide their matching sign-off.
Sign only if you can truthfully make the DCO certification.

For your own new commit:

```sh
git commit -s -m "Describe the change"
```

For your own most recent commit, after reading and agreeing to the DCO:

```sh
git commit --amend --no-edit --signoff
```

This uses the identity in your Git configuration. A trailer looks like:

```text
Signed-off-by: Example Contributor <contributor@example.com>
```

Use your own identity. Do not copy this example or certify for someone else.
Coordinate with collaborators before rewriting shared commits; rewriting changes
commit IDs. A sign-off is a certification, not a cryptographic signature or an
independent verification of ownership. Your commit identity and sign-off become
part of the public contribution record described in the DCO.

The automated check validates all PR commits, including merge and bot commits;
there are no automatic bot exemptions. PRs with more than 250 commits must be
split. If the check reports missing certification, correct only work you can
truthfully certify, or ask the actual contributor to supply their certification.

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
