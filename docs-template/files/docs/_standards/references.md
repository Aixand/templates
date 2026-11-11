# Sources behind the standard

These references informed standard **0.1.0**. The selected rules and examples are
Aixand's software-documentation profile. Research does not establish formal STE
compliance or the correctness of an application project's documentation.

## Local precedent

Reusable documentation patterns include reader-goal navigation, package-local
contributor guides, diagrams of ownership and flows, exact references with source
links, and verification of reader outcomes.

The adjacent `open-source-template` and `installation-template` informed the
separation of reusable `files/`, adaptable examples, setup guidance, and local
checks. The open-source template supplies the reused repository-policy checker,
hook installer, tests, workflow, editor defaults, and Apache license text.

## Language and documentation design

| Source | Practice adopted |
| --- | --- |
| [ASD-STE100 FAQ](https://www.asd-ste100.org/faq.html) | Controlled meaning, concise instructions, consistent technical names; full compliance needs both rules and vocabulary review |
| [ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf) | Sentence discipline informs our software profile; the full specification is not bundled |
| [Diátaxis](https://diataxis.fr/start-here/) | Separate learning, task completion, exact lookup, and explanation |
| [Applying Diátaxis](https://diataxis.fr/how-to-use-diataxis/) | Improve useful content without forcing empty structures |
| [GitLab agent instructions](https://docs.gitlab.com/development/documentation/ai-instruction-files-documentation/) | One authoritative standard and specific agent rules |
| [Docker application tutorial](https://docs.docker.com/get-started/tutorials/run-an-app/) | Working example, visible result, and cleanup |
| [Kubernetes port-forwarding task](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/) | Prerequisites, commands, expected output, and verification |

## Validation and instruction loading

- [Mermaid accessibility](https://mermaid.js.org/config/accessibility.html): accessible titles and descriptions.
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli): local SVG/PNG rendering and themes.
- [GitLab documentation testing](https://docs.gitlab.com/development/documentation/testing/): prose, Markdown, link, diagram, and generated-reference checks.
- [Official OpenAI instruction guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md): project instruction discovery and scope.

External sources are references, not runtime dependencies. Recheck them when
updating the standard. The offline checker does not fetch external links.

[Standard index](README.md)
