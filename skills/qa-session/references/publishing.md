# Publishing

The page is published to one target, chosen at intake and recorded in `sources.md`. The skill's steps do not change with the target; only the mechanics below do.

## Markdown file (default)

- Path: `docs/qa/<slug>/session.md` in the repository of the feature, unless the team keeps QA pages elsewhere. Ask once at intake.
- Commit it only when the team commits docs of this kind. Otherwise keep it private with `.git/info/exclude`, as the ai-notes skill does. Never a `.gitignore` change without asking.
- The Findings table is written into the same file during the session. Commit the page after the session, not during it.
- Links inside the page are relative to the file or absolute to the test environment.

## Document tool through a connected MCP server (wiki, Notion, Confluence and the like)

1. Find the tool: use the tool search the session has, with the tool's name or "create page". Do not guess names.
2. Create the page from the markdown, mapping the template as follows:
   - the title is the first heading;
   - blockquotes become the tool's callout block, keeping the bold labels (Why, Caveat, Known limits);
   - checkboxes become the tool's to-do blocks, so the tester can tick them;
   - the Findings table becomes a table with exactly the template's columns.
3. Record the page id and its URL in `sources.md`. The page id is for the session's own use; the page itself shows the URL, not the id.
4. Read the page back once after publishing. Check that the checkbox count, the scenario count and the table columns match the markdown. Report any difference in one line.
5. Before every update of an existing page, fetch it first. A page with ticks or findings is never overwritten from a fresh build: the carry-over step decides what moves.
6. Tool quirks go into `sources.md` under "Tool notes" as they are found, one line each: for example a table cell limit, a mention syntax that needs escaping, or a block that the tool drops on update. Keep them out of this skill.

## Rules for every target

- The published page is the page. The notes folder keeps the decisions, sources and derivation, never a second copy of the script.
- The page has no tracking data, no personal details beyond the seeded emails, and no secrets.
- A reviewer's edit on the published page is kept. Compare it with the local page before the next rework and report it as a change, not a silent overwrite.
