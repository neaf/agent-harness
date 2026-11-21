# Global working rules

- Prefer semantic tools (Serena MCP, when available) over text replacement for code navigation and refactoring.
- Before reporting a code change as done, run the project's compile/test command and report the result.
- Never print, commit, or paste secrets, tokens, or credential files.
- Match the existing code style. Do not reformat files you did not otherwise need to change.
- If the project has its own `AGENTS.md`, follow it over these defaults.
- Delegate self-contained work (captures, long test runs, extraction, doc fixes) to subagents when it saves tokens or keeps the main context clear. Give each a full task spec, file ownership and the expected report format. Run independent tasks in parallel in the background.
- Do not run tests or commands after every small edit, and do not let them print long output. Trust the code, verify at larger milestones, and fix what fails. Filter output to the pass or fail line and the failing numbers.
- Write tools so their default output is minimal: one summary line or a short table, with details behind a flag.
- When work spans several sessions, subagents or PRs, keep notes in `.ai-notes/<area>/` (see the `ai-notes` skill). Read `.ai-notes/README.md` at the start of a session if it exists.
- "Do it in a fork" or "with a clean context" means a fresh subagent with a self-contained prompt, not a copy of the conversation.
