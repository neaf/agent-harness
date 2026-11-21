---
name: ai-notes
description: Keep investigation and project notes as markdown files in `.ai-notes/<area>/`, so work can be split across sessions and subagents and picked up later without the conversation history. One orchestrator session owns the notes and delegates to fresh subagents. Use when an investigation or multi-step piece of work starts, when the user asks to note or persist findings, to hand work to another session or subagent, or to continue an area ("continue from .ai-notes/<area>").
---

# AI notes

Markdown notes per area of work. They are the shared memory between sessions and subagents. The agent reads, creates and updates them on its own: the user never has to run a command or ask for an update. One orchestrator session keeps the overview, talks to the user and owns the notes. Subagents get the heavy work with a clean context and read the notes for background.

## Start of every session

1. Read `.ai-notes/README.md` if it exists: conventions and the index of areas.
2. When the task belongs to an area, read its `README.md` before anything else and resume from its to-do list.
3. No `.ai-notes/` and the work spans more than one session, one subagent or one PR: create it.

## Location and git

- `<repo root>/.ai-notes/`, one subdirectory per area: `.ai-notes/<area-slug>/`.
- Committed by default.
- If the user wants them private for a repo (work repos, shared repos), ignore them for that repo only with `.git/info/exclude`. It covers every worktree of the repo and is not shared. Never use the repo's `.gitignore` or the global gitignore for this unless the user asks.

## Files

`.ai-notes/README.md`: what the notes are for, these conventions in a few lines, one line per area.

In each area:

- `README.md`, mandatory, the entry point:
  - Goal in one or two lines.
  - Links: dashboards, ticket project (with its id when lookups by name are fragile).
  - Files: one line per file of the area.
  - Workstreams table: `# | workstream | state | notes`. State carries ticket, PR, branch and worktree path.
  - To do: checklist of follow-ups (post-deploy checks, cleanups, pending decisions).
  - Open questions: what is not verified yet.
  - Lessons for the next session: pitfalls hit, commands that worked, user corrections.
- `findings.md`: the first analysis, with raw numbers.
- One file per workstream or topic, `<topic>.md`: summary, evidence, proposed fix, status.
- Deliverables for humans (a stakeholder message, a proposal for another team): their own file, marked with the date they were sent.

## Writing rules

- Summary first, then evidence, then proposal.
- Evidence must be reproducible: exact queries and filters, time ranges, IDs (traces, requests, users), file paths with line numbers, commit SHAs.
- Absolute dates (`2026-11-19`), never "today" or "last week".
- Mark what is verified and what is inferred. Keep a wrong theory as retracted, with the evidence that killed it.
- Record user decisions with the date and their reason.
- One fact in one place. Other files link to it.
- Mark superseded files and sections instead of deleting them.

## Lifecycle

- Update the area README as the work moves, not only at the end.
- Create a ticket when a workstream starts, not for every finding. Link it in the workstreams table.
- When a session stops, write where it stopped and what comes next in the area README.
- After a PR merges or a worktree is removed, update the row and tick the to-do.

## Orchestrator and subagents

- "Fork", "in a fork", "clean context": spawn a fresh subagent with a self-contained prompt, not a copy of the conversation.
- The prompt points at the notes (`.ai-notes/README.md`, the area README, the relevant files) instead of retyping them, and states:
  - the goal and what is already ruled out;
  - scope and stop points (investigate only, or fix and open a PR);
  - every decision the subagent may need, since it cannot ask the user: isolation (worktree or not), what it may push, what it must never do;
  - the shape of its final report.
- A subagent working in a separate checkout (worktree) cannot write the notes of the main checkout. It returns the text, the orchestrator writes it.
- Treat a report as claims. Check the key code claim yourself. Challenge any explanation that dismisses a failure ("flaky", "unrelated", "stale state") without a passing run to compare against.
- After each report, update the area README, then answer the user.
- Worktrees: tell the subagent that every shell command starts in the main checkout, so it must `cd <worktree> && ...` or use absolute paths.
