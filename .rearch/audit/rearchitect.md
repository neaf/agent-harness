# Audit: rearchitect

## Coverage
| File | Lines | Read fully |
|---|---|---|
| README.md | 34 | yes |
| agents/rearch-architect.md | 41 | yes |
| agents/rearch-auditor.md | 68 | yes |
| agents/rearch-phase.md | 39 | yes |
| skills/rearchitect/SKILL.md | 115 | yes |
| skills/rearchitect/references/docs-style.md | 23 | yes |
| skills/rearchitect/references/state.md | 98 | yes |
Also read for checks: install.py:15-60, targets/models.json, .rearch/STATE.md, baseline.md head.

## Functional behavior
- F1: Resume from `.rearch/STATE.md`; no `.rearch/` means Stage 0. Evidence: SKILL.md:12-13. Status: active.
- F2: Announce the plan (3-8 lines) before each stage or phase; announce off-plan actions. Evidence: SKILL.md:15-16. Status: active.
- F3: Route models by subagent: auditor fast, architect strong, phase default. Evidence: SKILL.md:20-23, agents/*.md tier lines, targets/models.json. Status: active.
- F4: Fallback to general-purpose/general subagent with pasted agent body when agents are missing. Evidence: SKILL.md:25. Status: active.
- F5: Stage 0: clean-tree check, branch `rearch/<date>`, tag `rearch-base`, baseline.md with commands and M1..Mn, STATE.md, commit `rearch: setup`. Evidence: SKILL.md:30-34. Status: active.
- F6: Stage 1: inventory of every file with kind, lines, aspect(s); aspect budget about 8,000 lines; user gate; commit. Evidence: SKILL.md:38-43. Status: active.
- F7: Stage 2: parallel auditors, coverage check against inventory, then a `seams` auditor, commit `rearch: audits`. Evidence: SKILL.md:47-51. Status: active.
- F8: Stage 3: architect requirements mode, user gate on open/experimental/unclear items, commit. Evidence: SKILL.md:55-57, agents/rearch-architect.md:20-27. Status: active.
- F9: Architect verifies high-severity bugs, decision-driving facts, and dead/experimental claims against cited lines; lists refuted findings. Evidence: rearch-architect.md:16-18. Status: active.
- F10: Stage 4: architect writes architecture.md, docs-plan.md, phases.md; user gate. Evidence: SKILL.md:61-69. Status: active.
- F11: Stage 5: one fresh `rearch-phase` per phase; blocked/done handling; manual checks; commit per phase with FR IDs; orchestrator never reads source. Evidence: SKILL.md:73-84. Status: active.
- F12: Phase agent leaves tree uncommitted, never touches STATE, records deviations in deviations.md. Evidence: rearch-phase.md:26,28. Status: active.
- F13: Stage 6: per-module auditors, move requirements/architecture into docs/, delete `.rearch/`, update README/CLAUDE.md, final baseline, commit `rearch: complete`, ask before merge or tag delete. Evidence: SKILL.md:88-94. Status: active.
- F14: Stop at about 70% context and print a paste-able resume prompt. Evidence: SKILL.md:98-105. Status: active.
- F15: Topic docs: present tense, no history, four-part quirks, sourced facts, tables. Evidence: docs-style.md:11-18. Status: active.
- F16: install.py renders each `agents/*.md` per tool, tier mapped through models.json. Evidence: install.py:23-33. Status: active.

## External facts and quirks
- X1: A global git config can force annotated tags (here `tag.gpgSign=true` in ~/.gitconfig). Symptom: `git tag rearch-base` fails asking for a message. Workaround: `git tag -a rearch-base -m "rearchitect base"`. Location: SKILL.md:31 says only "tag the current commit". Source: test (observed in this run; `git tag -n` shows message "rearchitect base").
- X2: opencode agents get no `tools` field. install.py:30-35 renders only description, mode, model. Effect: the "tools:" lists in the three agent files (and "Auditor never edits project files", "architect writes only inside .rearch/") are not enforced in opencode. Source: code.
- X3: Claude `default` tier maps to `inherit`; opencode `default` maps to null and the model line is omitted. Matches SKILL.md:22 "default: main session's model". Source: code (targets/models.json:2-3, install.py:32-33).
- X4: Subagents cannot spawn subagents. SKILL.md:88 relies on it for Stage 6. No agent lists an Agent/task tool, so true in Claude Code. opencode with all tools open (X2) is not guaranteed. Source: unverified for opencode.
- X5: Model names in SKILL.md:20-21 say "DeepSeek Flash"/"DeepSeek Pro"; models.json:3 has `deepseek/deepseek-flash` and `deepseek/deepseek-v4-pro`. Naming differs. Source: code.

## Doc and code inconsistencies
- D1: SKILL.md:68 says phases.md ends with the last code phase and Stage 6 does cleanup. rearch-architect.md:40 says the architect adds a "final phase for cleanup and traceability audit". Two owners of the same work.
- D2: SKILL.md:64-65 fixes Phase 1 = topic docs, Phase 2 = test harness. rearch-architect.md:40 states the same order but adds "then modules" and the final phase. Consistent on 1-2, conflicting on the last phase (D1).
- D3: rearch-architect.md:18 outputs a "Refuted audit findings" section. state.md:50-71 requirements.md format has no such section.
- D4: state.md:57 evidence anchors `audit/sequencing.md#F3`. Audit report format (rearch-auditor.md:34-35) writes F-items as list bullets, not headings. No `#F3` anchor resolves. Works only as a text reference.
- D5: state.md:73 allows statuses kept/dropped/open. rearch-architect.md:23 uses "open" for experimental/unclear. SKILL.md:56 expects the user to resolve to keep/drop. Consistent, but the `Dropped` section (state.md:66) and status `dropped` overlap.
- D6: README.md:8 lists `tools` as a neutral field. Opencode output ignores it (X2). README does not say so.
- D7: SKILL.md:20 "cheap model: Sonnet". models.json:2 fast = sonnet. True. The strong tier is "opus". True.
- D8: SKILL.md:47 and rearch-auditor.md:16 define auditor input as aspect + file list. SKILL.md:90 asks auditors per new module "with the requirements file". The auditor report template has no section for FR mapping. Stage 6 prompt does not fit the agent.
- D9: README.md:16 summary "one fresh subagent per phase" true. SKILL.md description true.

## Assumptions to revalidate
- A1: Agent frontmatter is parsed by `line.split(": ", 1)` (install.py:18) and rendered unquoted. rearch-auditor.md:3 ("skill: reads") and rearch-phase.md:3 ("context: implements") contain `: ` inside the description. Strict YAML rejects an unquoted plain scalar with `: `. If Claude Code or opencode parse strictly, the agent fails to load or the description truncates. Unverified; check M1/M2.
- A2: Stage 0 assumes "clean tree" is achievable. `__pycache__/` is untracked and not ignored here (baseline.md:5); the skill has no rule for caches or untracked noise.
- A3: Stage 6.1 assumes subagents cannot spawn subagents (X4).
- A4: Orchestrator checks audit coverage (SKILL.md:49) without reading full reports (SKILL.md:48). Assumes a grep over coverage tables works. Tables use free-form "yes" and file paths; no stated command.
- A5: Skill text is audio/DAW-biased (Push 2, Bitwig, head unit, audio thread, real-time, DAW in Stage 0 step 4; rearch-architect.md:34 "Nothing blocking on real-time paths", state.md:61,64; docs-style.md:8). For a non-real-time project (this one) these prompts steer the architect toward irrelevant constraints.
- A6: Fixed 15-files-per-phase and 8,000-line aspect budgets assume a context size; not tied to model.
- A7: Phase agent context is "clean" but prompt asks it to read STATE, phases, architecture, requirements, baseline, source, audits (rearch-phase.md:20-21). A large requirements.md or audit can overflow a default-tier model. No size limit.

## Bugs
- B1 [high]: Stage 6 deletes `.rearch/` (SKILL.md:91) before step 4 runs "the full baseline and the manual checklist" (SKILL.md:93). baseline.md holds both and is gone, unless the orchestrator read it earlier. Scenario: Stage 6 reaches step 4 after a context restart -> commands and M1..Mn unrecoverable except from git history. Fix needs reorder or "read baseline first".
- B2 [medium]: Stage 0 tag command not specified. Annotated-tag configs fail (X1). SKILL.md:31.
- B3 [medium]: Description colons in agent frontmatter (A1). rearch-auditor.md:3, rearch-phase.md:3.
- B4 [medium]: No resume rule for a crash mid-phase. Stage 5 spawns a fresh phase agent and the previous attempt leaves an uncommitted dirty tree (rearch-phase.md:8,28). SKILL.md:77-79 covers blocked and failed replies, not a dead subagent or a restart with a dirty tree. The new agent then sees partial edits and half-deleted files.
- B5 [medium]: Stage 6 "extra phase" (SKILL.md:90) has no entry in phases.md, but rearch-phase.md:20 reads "your phase entry in phases.md". No instruction to append it.
- B6 [medium]: Mid-stage resume has no progress record. Stage 2 spawns N auditors; STATE records no per-aspect completion (state.md:18-39 shows only stage/phase). After a crash the orchestrator must infer from existing files in `.rearch/audit/`; a partial file looks complete. Coverage check (SKILL.md:49) catches missing files only if the tables exist.
- B7 [low]: STATE update vs commit order. Stage 2/3/4 say "Commit ... Update STATE" (SKILL.md:51,57,69); STATE then changes after the commit and sits dirty. Stage 5 says commit STATE with the phase (SKILL.md:81). Stages 0-1 commit order is not stated for STATE. Real STATE in this run: "Stage 2 (audit), not started" (STATE.md:5) was committed with inventory.
- B8 [low]: Stage 1.1 lists "untracked files that are not ignored" (SKILL.md:38) but caches that appear after running baseline tests count as such. baseline.md:5 works around with `PYTHONDONTWRITEBYTECODE=1`; skill does not say to.
- B9 [low]: Stage 0 step 2 does not handle an existing branch or tag (rerun same day, resumed after partial setup).
- B10 [low]: Stage 2 step 4 seams auditor input is "every report's Interfaces section plus boundary files"; the orchestrator is told not to read reports (SKILL.md:48) but must extract sections. No tool or method given; likely means passing the paths, unstated.

## Dead code, leftovers, stale comments
- L1: state.md:24 example `Branch: rearch/2026-10-29` and decisions dated 2026-10-29 (state.md:34,67): example data, harmless.
- L2: SKILL.md:33 and :40 hard-code domain examples (hardware, host DAW, head unit, Push 2). Leftover from the project that created the skill.
- L3: state.md:36-38 indents the Next prompt; SKILL.md:100-103 fences it. Two formats for the same block.
- L4: Fallback in SKILL.md:25 tells the user to run install.py but gives pasting instructions that duplicate agent bodies; nothing dead, but untested path.

## Improvement areas
- I1: Put exact git commands in Stage 0 (`git switch -c`, `git tag -a rearch-base -m ...`). Removes X1/B2/B9.
- I2: Add a `Progress` block to STATE (per-aspect audit done, per-phase attempt number, "phase in flight" marker with base commit). Fixes B4, B6.
- I3: Make Stage 6 order: read baseline, final audit, run checks, then delete `.rearch/` last. Fixes B1.
- I4: Make the architect's domain rules conditional ("if the project has a real-time path"). Fixes A5.
- I5: Enforce agent limits where possible: opencode permission/tools mapping in install.py (X2).
- I6: Provide a small script for coverage check (inventory vs audit tables) so orchestrator context stays small (A4). The other skills ship scripts with tests (README.md:17-21); rearchitect ships none.
- I7: Quote description values on render (install.py:27,33) or remove `: ` from descriptions. Fixes A1.
- I8: Remove duplicate cleanup ownership (D1).
- I9: The writing-rules line is copied in four places (SKILL.md:26, and top of each agent file); one source would avoid drift.

## Interfaces
- Exposes: skill `rearchitect`; subagents `rearch-auditor`, `rearch-architect`, `rearch-phase` (tier fast/strong/default); file formats in references/state.md (STATE, baseline, inventory, audit, requirements, architecture, docs-plan, phases, deviations); doc style in references/docs-style.md.
- Consumes: install.py agent parsing and tier mapping (install.py:15-33, targets/models.json); agent tool names from the host (Agent/task tool); git; `ai-notes` and `writing-craft` are not referenced.
- Threading: main session orchestrates serially; auditors run in parallel; architect and phase agents run one at a time.

## Open questions for the user
- Q1: Should Stage 0 mandate `git tag -a -m`, or detect the config? (X1)
- Q2: Should the skill ship scripts (coverage check, STATE progress) like the other skills, with tests?
- Q3: Is the audio/real-time bias intended to stay in the generic prompts (A5)?
- Q4: Who owns final cleanup: architect's last phase or Stage 6 (D1)?
- Q5: Do the agent descriptions load correctly in Claude Code and opencode with `: ` in them (A1)? M1/M2 would show it.
