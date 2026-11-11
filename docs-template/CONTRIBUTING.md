# Change the documentation template

Keep the standard, templates, working example, and checks consistent. State the
reader problem and resulting behavior in the change description. Follow the
[shared standard](files/docs/_standards/standard.md) for this template's own docs.

Use original material or identify the source and preserve its applicable notices.
AI-assisted material needs the same factual and source review as other changes.
Do not invent authorship certifications, release history, or executed checks.

Run [the validation commands](checks/README.md). Changes to the checker or renderer
need meaningful regression cases for failure behavior and preservation of existing
files. Render changed diagrams and inspect both supported themes.

Update VERSION, the copied standard version, and CHANGELOG when the standard's
contract changes. Keep project-specific additions outside the common rules.
Follow [the repository file policy](REPOSITORY_FILES.md) before tracking files.
