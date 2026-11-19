# Global working rules

- Prefer semantic tools (Serena MCP, when available) over text replacement for code navigation and refactoring.
- Before reporting a code change as done, run the project's compile/test command and report the result.
- Never print, commit, or paste secrets, tokens, or credential files.
- Match the existing code style. Do not reformat files you did not otherwise need to change.
- If the project has its own `AGENTS.md`, follow it over these defaults.
- When work spans several sessions, subagents or PRs, keep notes in `.ai-notes/<area>/` (see the `ai-notes` skill). Read `.ai-notes/README.md` at the start of a session if it exists.
- "Do it in a fork" or "with a clean context" means a fresh subagent with a self-contained prompt, not a copy of the conversation.
