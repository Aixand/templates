# Verify documentation and examples

Run commands from the template root with Python 3.11 or newer. The offline checker
has no third-party Python dependencies. Optional rendering needs Node 22.13 or
newer, npm, and a working Chromium installation managed by Puppeteer.

## Run the offline checks

```sh
python3 files/scripts/checks/check-docs.py --root .
python3 files/tests/tooling/checks/docs_test.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/tooling/checks/repository_files_test.py
python3 examples/project/tools/status.py
```

Expected result: each command exits zero. The final command prints `ready`.

The checker validates a plain-Markdown subset: selected pages, local inline/reference links and
images, GitHub-style heading anchors, heading levels, closed code fences, final
newlines, and unresolved uppercase template tokens. Mermaid blocks need accessible
titles and descriptions. Links inside code blocks and inline code are examples.
External URLs are not fetched. Unsupported Markdown extensions, prose quality,
orphan pages, and technical correctness need review or the project's own tools.
Use ATX headings (`#` markers), flat link labels, same-line reference definitions,
and fences indented by at most three spaces. Raw HTML links, setext headings,
site-root URLs, and static-site extensions need the destination's own checks.

The checker never executes documentation commands or installs dependencies.
Run the project's real examples and existing Markdown/prose tools separately.

## Render the Mermaid blocks

Install the exact locked Node dependencies:

```sh
npm ci --prefix tools
python3 files/scripts/checks/check-docs.py --root . --render-mermaid build/diagrams --mmdc tools/node_modules/.bin/mmdc
```

The checker targets Mermaid CLI 12 and renders each selected block as PNG in the
default and dark themes with matching backgrounds.
Review every changed diagram for labels, arrows, clipping, contrast, and scale.
Use `--puppeteer-config PATH` if the environment requires an explicit browser
executable or existing browser configuration. The tool never disables the browser
sandbox automatically. Review any environment-specific launch settings yourself.

For extraction without rendering:

```sh
python3 files/scripts/checks/check-docs.py --root . --extract-mermaid build/mermaid
```

These commands create a new preview directory and refuse an existing one.
The preview manifest maps each artifact to its Markdown source and line. Keep
build output ignored. A local render does not validate a hosting platform's
Mermaid version or the behavior described by the diagram.

## Adopt the checks

Copy the contents of `files/` selectively, then run from the adopting project:

```sh
python3 scripts/checks/check-docs.py --root .
python3 tests/tooling/checks/docs_test.py
```

Adapt the copied `docs-checks.json` include/exclude paths. Only version 1 and its
listed keys are supported; invalid configuration fails. A pattern that matches
no files fails, so adapt optional paths before using the configuration.
Use [the CI example](../examples/workflows/docs.yml.example) to add offline checks.
Keep the project's renderer and prose checks alongside them.
