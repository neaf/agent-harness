# Global working rules

- Prefer semantic tools (Serena MCP, when available) over sed, regex or Python-script edits for code navigation, renames and refactoring. Projects are Kotlin (Android), Swift (native Apple) and Java.
- Before reporting a code change as done, run the project's compile/test command and report the result.
- Never print, commit, or paste secrets, tokens, or credential files.
- Match the existing code style. Do not reformat files you did not otherwise need to change.
- If the project has its own `AGENTS.md`, follow it over these defaults.
- Delegate self-contained work (captures, long test runs, extraction, doc fixes) to subagents when it saves tokens or keeps the main context clear. Give each a full task spec, file ownership and the expected report format. Run independent tasks in parallel in the background.
- Do not run tests or commands after every small edit, and do not let them print long output. Trust the code, verify at larger milestones, and fix what fails. Filter output to the pass or fail line and the failing numbers.
- Write tools so their default output is minimal: one summary line or a short table, with details behind a flag.
- When work spans several sessions, subagents or PRs, keep notes in `.ai-notes/<area>/` (see the `ai-notes` skill). Read `.ai-notes/README.md` at the start of a session if it exists.
- "Do it in a fork" or "with a clean context" means a fresh subagent with a self-contained prompt, not a copy of the conversation.
- Compute is free, tokens are not. Always prefer spending machine time over spending tokens. When the logic of a system can be read from its binary or source, spend whatever machine time decompilation, emulation and batch extractors need to get the definitive source. Do not substitute many experiments, test runs, probe renders or long deliberation for that read. A measurement is a fallback for what the source leaves open. A measurement is fine when it is one scripted batch that runs for an hour and answers the question, in place of many small hand-driven runs.
- Do not re-run the full test suite after every step. One run per step burns tokens on output Claude has already seen pass. Run it at milestones, pipe through a filter for the pass/fail line and failure count, and trust green code in between.
- When the user asks for a deliverable they will review (an artifact, report, design, document), delegate it with a description that starts with `For review: `. When it finishes, tell the user it's ready: what it is, where it is, how to open it, and what to look at first. Then stop for their review instead of building on it. Subagents you start for your own steps don't get the prefix.
