# Publishing

The drafts in the work folder are the source. Publishing copies them to where reviewers read them, chosen at intake.

## Markdown in the repository (default)

- Copy `draft/attack-plan.md`, `draft/technical-solution.md` and `draft/evidence.md` to `docs/attack-plans/<slug>/`, or to the folder the author named. Replace links between drafts with relative links.
- For the product review, publish `attack-plan.md` alone, with the note in place of the technical part.
- Use plain Markdown: a `> **Scope**` block for the scope callout, tables with a header row, ```` ```mermaid ```` blocks for diagrams. Milestone colors become a `Milestone` column.
- Reviewers comment on a pull request or in the file. Read those comments in Stage 8.
- Commit or open a pull request only when the author asks.

## Notion

Use the Notion MCP server's fetch, create, update and comments tools, directly or through a gateway that fronts several servers. With no Notion tool, tell the author and publish as Markdown instead. Before writing, read [Notion MCP](<../../harness-common/topics/Notion MCP.md>): it lists the tool quirks and the workaround for each.

### Creating the pages

- Create the attack plan with no parent (a private page) unless the author gave a parent URL. Create the technical solution and evidence pages as its children.
- Use `<table-of-contents />` for the TOC, `<callout>` for the scope and evidence callouts, `<table>` tags for tables, and a ```` ```mermaid ```` code block for diagrams.
- Color task-table rows with `<td color="blue_bg">` and the like.

### Updating

- Re-fetch before every write. Never restore a block the author removed. Keep their wording.
- Prefer many small anchored `update_content` edits over `replace_content`.
- Never duplicate a page as a backup. Notion's page history is the fallback.

### After each write

Re-fetch the page. Check the headings and their numbering, the table columns, the links between the three pages, and that no tag (`<callout`, `<table`) shows as text. Report what did not render.
