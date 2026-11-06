---
name: rearchitect
description: Full rearchitecture of a working but patched-together project. Inventories every file, runs parallel per-aspect audits on a cheap model, consolidates functional requirements, plans a new architecture on a strong model, then executes the refactor in committed phases with one fresh subagent per phase. Use when the user says the project works and wants a complete refactor, rearchitecture, cleanup of exploratory docs, or "rearchitect"; also use to continue one ("continue from .rearch/STATE.md").
---

# Rearchitect

Turns an exploratory codebase (reverse engineering notes, PoCs, workarounds, stale docs) into a clean architecture plus fact-only topic docs. One main session orchestrates the whole run and spawns subagents for the heavy work, so its own context stays small. All state lives in `.rearch/` in the target repo and is committed, so a new session in Claude Code or opencode can resume after a crash, a rate limit or a stop.

## Start of every session

1. Read `.rearch/STATE.md` if it exists. It names the current stage and the next step. Resume there.
2. No `.rearch/` means a new run: start at Stage 0.
3. Read `references/state.md` (next to this file) for the file formats.
4. Before the first tool call of each stage or phase, tell the user the plan in 3 to 8 lines. Name the steps, the commands that will run, the files that will be created, changed or deleted, the subagents that will be spawned, and the commit that ends it. Then proceed without waiting, unless the step is a gate.
5. Before any later action outside that plan (a deletion, a branch or tag operation, an extra subagent, a fix to a failing build), say what it is and why in one or two lines first. Reading files and running read-only commands need no announcement.

## Model routing

- Audits run in the `rearch-auditor` subagent (cheap model: Sonnet in Claude Code, DeepSeek Flash in opencode).
- Requirements and architecture run in the `rearch-architect` subagent (strong model: Opus in Claude Code, DeepSeek Pro in opencode).
- Each phase runs in a fresh `rearch-phase` subagent (model set at install, default: the main session's model).
- The main session orchestrates: it talks to the user, runs gates and manual checks, commits and updates STATE.
- Claude Code spawns them with the Agent tool (`subagent_type: rearch-auditor`). opencode spawns them with the task tool (agent `rearch-auditor`).
- Missing agent definitions: in Claude Code use `general-purpose` with `model: sonnet` or `model: opus`, and paste the matching `agents/*.body.md` as the prompt preamble. In opencode use the `general` subagent with the same preamble. Tell the user to run `install.sh`.
- Every subagent prompt carries the line: "No mannered prose. Answer first, short sentences, numbers and names, end on the result."

## Stage 0: Setup

1. Require a git repo with a clean tree. Ask the user to commit or stash otherwise.
2. Create branch `rearch/<YYYY-MM-DD>` and tag the current commit `rearch-base`. The tag keeps every old doc and experiment reachable after deletion.
3. Detect build, test, lint and run commands. Run build and tests. Record exact commands and results in `.rearch/baseline.md`.
4. Ask the user for behaviors only they can verify (hardware, host DAW, head unit, device pairing). Record them as a numbered manual checklist `M1..Mn` in `baseline.md`. Every later phase reuses this checklist.
5. Write `.rearch/STATE.md`. Commit `rearch: setup`. Continue to Stage 1 in the same session.

## Stage 1: Inventory

1. List every file: `git ls-files` plus untracked files that are not ignored. Record line counts.
2. Classify each file: source, test, doc, config, build, asset, generated, vendored. Generated and vendored files get one line each and no audit, unless the project patched them.
3. Propose aspects. Typical set: one per functional subsystem (UI, sequencing logic, MIDI handling, host wrapper), one per external system with quirks (Push 2, Bitwig, the head unit firmware), plus `build-and-tooling`. Docs join every aspect they discuss.
4. Budget: an aspect over about 8,000 lines of source plus docs gets split. Auditors must read every line, and a larger aspect overflows a cheap model's context.
5. Write `.rearch/inventory.md`: every file, its kind, line count and aspect(s). A file with no aspect is an error.
6. Gate: show the aspect list with file and line counts. Ask the user to confirm, merge or split. Commit `rearch: inventory`.

## Stage 2: Audit

1. Spawn one `rearch-auditor` per aspect, all in parallel. Prompt each with: aspect name, its file list from `inventory.md`, the output path `.rearch/audit/<aspect>.md`, the project one-liner, and the writing-rules line.
2. Each auditor returns a 150-word summary. Do not read full reports in the orchestrator session; context goes to the architect.
3. Check coverage: every file in `inventory.md` appears as fully read in some report's coverage table. Re-spawn an auditor for any gap.
4. Spawn one more `rearch-auditor` for the `seams` aspect. Input: every report's Interfaces section plus the boundary files they name. It audits contracts between aspects: threading, ownership, data formats, duplicated logic, circular dependencies.
5. Commit `rearch: audits`. Update STATE. Continue to Stage 3.

## Stage 3: Requirements

1. Spawn `rearch-architect` in requirements mode. It reads every audit and writes `.rearch/requirements.md` (format in `references/state.md`).
2. Gate: present the Open questions and every feature marked `experimental` or `unclear`. The user decides keep or drop for each. Write answers into `requirements.md` and log them in STATE Decisions. Experiments the user drops are deleted in the refactor.
3. Commit `rearch: requirements`. Update STATE. Continue to Stage 4.

## Stage 4: Architecture and phase plan

1. Spawn `rearch-architect` in architecture mode. It writes `.rearch/architecture.md`, `.rearch/docs-plan.md` and `.rearch/phases.md`.
2. Phase rules the architect follows:
   - Every phase leaves the build green and every kept requirement working.
   - Phase 1 writes the topic reference docs from the audits' External facts sections. Quirk knowledge lives in comments and old docs, and later phases delete both.
   - Phase 2 adds the test harness the new architecture needs (characterization tests on current behavior where practical).
   - One phase fits one subagent context: one module or one seam, roughly 15 files touched at most.
   - Removal of old code happens in the phase that replaces it. No dual implementations survive past their phase.
   - `phases.md` ends with the last code phase. Stage 6 does the cleanup and the traceability audit.
3. Gate: the user reviews the architecture and plan. Apply changes. Commit `rearch: architecture`. Update STATE. Continue to Stage 5.

## Stage 5: Phase execution (one subagent per phase)

Loop over the phases in `phases.md`, one at a time:

1. Tell the user the phase number, title and goal in 2 lines.
2. Spawn a new `rearch-phase` subagent. Prompt: phase number, this skill's directory, any user answers from a blocked attempt, and the writing-rules line. Never reuse a previous phase's subagent.
3. Blocked reply: show the questions to the user, record answers in STATE Decisions, and spawn a new `rearch-phase` for the same phase with the answers.
4. Done reply: show the user the summary. Run `git status` and the baseline build and test commands to confirm the subagent's results.
5. Manual checks: list the `M` items the subagent named, with what to look for. Wait for the user's result. A failure goes back to a new `rearch-phase` with the failure description.
6. Deviations recorded: tell the user which later phases changed.
7. Commit `rearch(phase N): <title>` with the requirement IDs in the body. Update STATE (phase done, commit hash, next phase, Next prompt). Commit STATE with the phase.
8. Continue with the next phase.

The orchestrator never reads source files or full audits during Stage 5. It works from subagent replies, `git diff --stat` and STATE. This keeps its context near constant across phases.

## Stage 6: Final cleanup (orchestrator)

The orchestrator runs this stage itself, because it spawns auditors and subagents cannot spawn subagents.

1. Spawn `rearch-auditor` per new module with the requirements file. Each confirms every FR maps to code and reports leftovers, stale comments and dead code. Findings that need code changes go to one more `rearch-phase` subagent as an extra phase.
2. Move `requirements.md` and `architecture.md` into `docs/`. Delete `.rearch/` and every exploratory doc that `docs-plan.md` marks for deletion. Git history and tag `rearch-base` keep them.
3. Update `README.md` and `CLAUDE.md` or `AGENTS.md` to point at the new docs.
4. Run the full baseline and the manual checklist. Commit `rearch: complete`.
5. Ask before merging the branch or deleting the tag.

## Stopping and resuming

The run continues in one session until it finishes. Stop when the user asks, when a rate limit or error ends progress, or when the context window is past about 70%. On a stop, print a fenced block the user pastes into a new session:

```
Use the rearchitect skill. Continue from .rearch/STATE.md.
Next: <stage or phase number and title>.
```

Keep the same block current in STATE under "Next prompt" after every stage and phase.

## Rules

- Use the file, search and shell tools directly. opencode's `execute` sandbox supports no `import`, `require` or filesystem access.
- Read every line of every file assigned to a step. Large files get read in chunks. A skim breaks the method: stale claims hide in the middle of files.
- Requirements come from current working behavior and user decisions. Old docs count as evidence only where code confirms them.
- The existing structure places no constraint on the new architecture.
- Facts about external systems need evidence: a code workaround, a capture, a test or a vendor doc. Unverified claims get marked `unverified` and land in Open questions.
- Never delete a workaround until its fact is in a topic doc.
- Commit at the end of every stage and phase. Never push or merge without asking.
