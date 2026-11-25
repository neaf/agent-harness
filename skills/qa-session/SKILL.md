---
name: qa-session
description: Builds, reworks and checks the QA session page for a feature milestone: the script a team walks through live on a deployed test environment with seeded users and data, one person driving and the others watching. Use when preparing, reworking, verifying or editing during a live session a QA script, walk-through or test-session page, or when a feature milestone needs a QA session before it merges.
---

# QA session

Before a milestone merges, the team walks through it together on a test environment (review app or staging) with seeded users and data. One person drives; the others watch. The page is the script: setup, a linear walk-through with checkboxes, product questions, and an empty findings table. The tester reads it with the app open, so every step must work without help.

[writing-craft](../writing-craft/SKILL.md) is mandatory before drafting and before any review of the page. This skill adds what is specific to QA pages and the process around them. It does not repeat the craft rules.

`<skill>` below is the folder holding this file. Run scripts with `/usr/bin/python3 -I`.

## Inputs

The page is derived from sources, never from the conversation. Each input is needed unless marked optional. Ask for a missing one, one question at a time, with its default.

1. **Spec or plan** of the milestone: what changes, for whom, what stays the same. Required.
2. **Code under test:** the branch or pull request, read at a recorded commit, with the permission and display code the checks depend on. Required.
3. **Seed:** the script or task that creates users, roles and data, and its printed output. Required: without it no check can be verified.
4. **Environment:** URL, deployed build, feature switch (its UI label and how to set it), how each seeded user signs in. Required.
5. **Personas and order.** Default: the most powerful persona first, then the new role, its edge cases, the roles that must see no change, and the feature switch off.
6. **Open product decisions.** Each becomes a product question on the page.
7. **Publishing target** (optional). Default: a markdown file at `docs/qa/<slug>/session.md` in the feature's repository. See "Publishing" below.

## Modes

Pick the mode from the state, then say which one runs in one line.

- **Create:** no page yet. Full derivation, verification, publish.
- **Rework:** the page exists and no session is running. The whole script is re-derived in fresh subagents that never see the previous page. Then the carry-over and a change report.
- **Live edit:** a session is running and the tester is on the page. Small targeted edits only, state preserved. No rebuild.

Never rebuild a page that has ticks or findings without asking the user first.

## Session folder

`.ai-notes/qa-<slug>/`, following the ai-notes skill (its README, its writing rules, one fact in one place):

- `README.md`: goal, links (test environment, feature, publishing target), files, to-do, open questions, lessons.
- `sources.md`: each source with its path, the code's commit, the seed command, the environment build, the publishing target and its page location, and "Tool notes".
- `decisions.md`: each decision the user made about the page, with the date and their reason. The rework reads it first; a decision in it survives every rework unless the user changes it.
- `rework-log.md`: one dated section per rework: what changed, and the source or decision behind each change.

The page never holds this history.

## Create

1. Check the required inputs. Stop and ask for any that is missing.
2. Record `sources.md`: commit SHAs, seed command, environment build, feature switch, publishing target.
3. Run the **Builder** brief (`references/briefs.md`) with the sources and `decisions.md`. It writes the page and a derivation file: each check and the source that settles it.
4. Run `check_page.py <page> -v` and fix every FAIL.
5. Run the **Verifier** brief: a fresh reader, given only the page and the sources, checks every fact and does a cold read as the tester. Fix each wrong check. Label each unverifiable check on the page with the check that would settle it.
6. Show the user the shape of the page (scenarios, checks, product questions, unverified checks) and the verifier's counts. Publish after the user's go-ahead ("Publishing" below).

Setup items come from `references/setup-checklist.md`. The page's section order and the writing of scenarios, checks and product questions come from `references/page-template.md`.

## Rework

1. Read `decisions.md`, `sources.md` and the last entry of `rework-log.md`.
2. Copy the current page, read from its publishing target, to `.ai-notes/qa-<slug>/previous.md`. It is kept for step 6 only. Never give its path to a subagent.
3. Run the **Builder** brief again with the sources, the decisions and the current version of this skill's references. Its page goes to a new working file, not over the current page.
4. Run `check_page.py` and the **Verifier** brief on the new page, as in Create.
5. Carry over the live state. Ticks and findings are matched by scenario title and check text. A tick carries over only when the check still means the same thing; otherwise it is removed and the reply says why. Findings the user asked to keep are copied with their original wording. Nothing else moves.
6. Compare the new page with `previous.md` and write the change report in `rework-log.md`: scenarios added, removed or reordered; checks changed, with old and new wording and the source or decision behind each; product questions changed; ticks removed. Show the user the report in one table.
7. Ask for review. Publish after the go-ahead. Keep `previous.md`.

## Live edit

- Change only what the tester asked for, or a check the session proved wrong. One edit per finding.
- Keep every tick and finding. When a check changes meaning, untick it and say in one line what changed and why.
- Record a decision the user makes in `decisions.md` with the date.
- Run `check_page.py` after the edit. No rebuild, no rework until the session is over. If a new fact is needed, verify it in one narrow fact check.

## Page rules

The full shape is in `references/page-template.md`. The rules a reviewer checks first:

- One linear story, persona after persona. Each scenario: a title that advances the story, "As <user>:", one sentence on what changed since the previous scenario, checkboxes with one observable fact each, then only the note lines that apply (why, caveat, product assumption).
- Show the data relationships in the UI before switching persona, so the next result is expected.
- Every expected result is derived from the code and the seed, verified before it is written. An unverified check is labelled, never written as a step.
- The seed makes every scenario possible. A seed gap is fixed in the seed, with a test.
- Every value the tester needs is resolved on the page before the session: real URLs, real ids, real emails.
- Surprises go in "Known limits, not bugs", before the walk-through.
- Product questions are written for a product person new to the project: the question as a heading, short context, option A (marked as what the test environment currently does, with the scenario where it shows) and option B, each with its consequence.
- Every on-screen word is the exact label that scenario's user sees, in their language, traced to the code that renders it for them. No UI element is paraphrased; when a screen differs by persona, each scenario uses its persona's labels.
- No internal reference ids, no bare "today", no history from earlier sessions. Each session starts with an empty Findings table.

`check_page.py` checks the mechanical part of these rules (ids, placeholders, emoji, scenario shape, the Findings section). It decides nothing about facts.

## Publishing

Follow [publishing.md](../harness-common/references/publishing.md). What is specific to this skill:

- Source of truth: the published page. `sources.md` records the target, the page URL and its id, and "Tool notes" for tool quirks.
- Markdown: links are relative to the file or absolute to the test environment. Findings are written into the same file during the session; commit the page after the session, not during it.
- Read-back also compares the scenario count.
- A published page with ticks or findings is never overwritten from a fresh build: the Rework carry-over decides what moves.
- No personal details on the page beyond the seeded emails.

## Subagents

- **Builder** and **Verifier**: `references/briefs.md`. Run them as general-purpose subagents on the strongest model tier, with the brief as the whole prompt. Never give them the conversation, a previous page, or the orchestrator's conclusions.
- Without subagents, run each brief yourself, say so in `README.md`, and keep the two passes separate: derive the page first, then check it as if you had not written it.

## Stopping and resuming

Stop when the user asks, when a required input is missing, or when a tool keeps failing. Write the state in the session `README.md`, then print:

```
Use the qa-session skill. Continue from .ai-notes/qa-<slug>/README.md.
Next: <mode, step>.
```

## Rules

- **Sources decide, the user decides.** Facts come from code, seed and environment. Choices come from the user and are recorded in `decisions.md`.
- **Fresh eyes are the point.** A rework starts from the sources, not from the previous page.
- **Test environments only.** Writes go to the test environment. Shared or production data is read-only, and read only when the user allows it.
- **Nothing is removed silently.** Old pages and notes are kept and marked as superseded.
- **A failed tool call is retried or reported,** never replaced by a guess.
