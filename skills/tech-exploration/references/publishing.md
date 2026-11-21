# Publishing

The drafts in the work folder are the source. Publishing copies them to where reviewers read them, chosen at intake.

## Markdown in the repository (default)

- Copy `draft/attack-plan.md`, `draft/technical-solution.md` and `draft/evidence.md` to `docs/explorations/<slug>/`, or to the folder the author named. Replace links between drafts with relative links.
- For the product review, publish `attack-plan.md` alone, with the note in place of the technical part.
- Use plain Markdown: a `> **Scope**` block for the scope callout, tables with a header row, ```` ```mermaid ```` blocks for diagrams. Milestone colors become a `Milestone` column.
- Reviewers comment on a pull request or in the file. Read those comments in Stage 8.
- Commit or open a pull request only when the author asks.

## Notion

Use the Notion MCP server's fetch, create, update and comments tools, directly or through a gateway that fronts several servers: list its servers, turn Notion on, then search its tools by prefix. With no Notion tool, tell the author and publish as Markdown instead. Sessions expire: re-probe before a long write.

### Creating the pages

- Create the attack plan with no parent (a private page) unless the author gave a parent URL. Create the technical solution and evidence pages as its children.
- When the tool refuses the size, create the page with its first sections, then append each next section in order.
- Use `<table-of-contents />` for the TOC, `<callout>` for the scope and evidence callouts (a `>` quote at the top can swallow the page), and a ```` ```mermaid ```` code block for diagrams.
- Write tables as `<table header-row="true"><tr><td>…</td></tr></table>`, not pipe rows. Simple tables come back as pipe rows on the next fetch: that is not a failed write. Empty pipe cells shift columns when split naively.
- Color task-table rows with `<td color="blue_bg">` and the like. Colors also give anchors when several rows share the same text.
- Tab-indent nested list items when writing. Fetch returns them with two spaces.
- A cell starting with `+ ` can render as a bullet. Scan for ` • ` after writing.
- Keep backticks balanced. One stray backtick collapses the whole page into one block.

### Updating

- Re-fetch before every write. Never restore a block the author removed. Keep their wording.
- Prefer many small anchored `update_content` edits over `replace_content`. They keep mentions, tables and comment threads. A reply with only `{page_id}` means every `old_str` matched. A miss comes back as `warnings: no_match`.
- An `old_str` that contains a `<mention …>` often does not match: anchor on the text around it.
- Bold text containing inline code is split on save, so a verification search for the original string can miss an edit that landed.
- Replacing text can drop the `discussion-urls` spans that attach comment threads. Fetch with discussions first, and re-wrap the new text with the same discussion URLs.
- Never duplicate a page as a backup. Notion's page history is the fallback.
- A gateway's firewall can block a script with regex lookbehinds or unusual patterns. Split it into smaller, simpler calls.

### After each write

Re-fetch the page. Check the headings and their numbering, the table columns, the links between the three pages, and that no tag (`<callout`, `<table`) shows as text. Report what did not render.
