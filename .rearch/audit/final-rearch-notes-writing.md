# Final audit: rearch-notes-writing

Files read in full: skills/rearchitect/SKILL.md (144), references/docs-style.md (23), references/state.md (138), agents/rearch-architect.md (48), rearch-auditor.md (85), rearch-phase.md (37), skills/ai-notes/SKILL.md (83), skills/writing-craft/SKILL.md (78), topics/Claude Code.md (98), topics/opencode.md (160), topics/macOS Python.md (44). Total 938 lines.

Result: 34 group requirements: 33 mapped, 1 partial, 0 missing. FR-AGT-08: mapped (no model name in the group). FR-APE-15: not in this group, not built (see 5).

## 1. Traceability

| ID | Location | Status |
|---|---|---|
| FR-RA-01 | rearchitect/SKILL.md:10-16 | mapped |
| FR-RA-02 | SKILL.md:18-24 (Spawns table; routing moved from prose) | mapped |
| FR-RA-03 | SKILL.md:34-46 (annotated tag :39, existing branch/tag :41, `compile()` :42) | mapped |
| FR-RA-04 | SKILL.md:48-55 (8,000 lines :53, gate :55) | mapped |
| FR-RA-05 | SKILL.md:57-63 (coverage grep :61, seams :62, Progress :60) | mapped |
| FR-RA-06 | SKILL.md:65-69; rearch-architect.md:12-14,16-24 | mapped |
| FR-RA-07 | SKILL.md:71-81 | mapped |
| FR-RA-08 | SKILL.md:91-105,122; rearch-phase.md:23,25 | mapped |
| FR-RA-09 | SKILL.md:107-117 (order fixed: baseline :114, delete :116) | partial: no step reconciles requirements.md and architecture.md with deviations.md before the move at :112 (finding 3a, 3b) |
| FR-RA-10 | SKILL.md:125-134 | mapped |
| FR-RA-11 | docs-style.md:11-18 | mapped |
| FR-RA-12 | rearch-architect.md:21,31 (conditional); state.md:111; docs-style.md:8 | mapped |
| FR-RA-13 | SKILL.md:46,55,63,69,81,89,102; state.md:48 | mapped |
| FR-RA-14 | SKILL.md:32,43-45,100; README row | mapped (last sentence "go straight to daily use" has no prompt text, needs none) |
| FR-NOTES-01 | ai-notes/SKILL.md:10-14 | mapped |
| FR-NOTES-02 | ai-notes/SKILL.md:3,14 (description and body agree, Q10) | mapped |
| FR-NOTES-03 | ai-notes/SKILL.md:16-19 -> harness-common state.md:38 "Private state" | mapped |
| FR-NOTES-04 | ai-notes/SKILL.md:21-38 | mapped |
| FR-NOTES-05 | ai-notes/SKILL.md:40-48 | mapped |
| FR-NOTES-06 | ai-notes/SKILL.md:50-55 | mapped |
| FR-NOTES-07 | ai-notes/SKILL.md:73-83 | mapped |
| FR-WRIT-01 | writing-craft/SKILL.md:18-25 | mapped |
| FR-WRIT-02 | writing-craft/SKILL.md:27-38 | mapped |
| FR-WRIT-03 | writing-craft/SKILL.md:40-48 | mapped |
| FR-WRIT-04 | writing-craft/SKILL.md:50-54 | mapped |
| FR-WRIT-05 | writing-craft/SKILL.md:65-78 | mapped |
| FR-WRIT-06 | writing-craft/SKILL.md:3,14-16 (Scope names exempt text); citations in attack-plan skills are outside this group | mapped |
| FR-WRIT-07 | section 7 gone; QA examples now deploy/export (:42,:54) | mapped |
| CON-CC-01 | Claude Code.md:13-15 | mapped |
| CON-CC-02 | Claude Code.md:65-70 | mapped |
| CON-CC-03 | Claude Code.md:43-52 (corrected: nesting is on by default) | mapped |
| CON-CC-04 | Claude Code.md:96-98 | mapped |
| CON-OC-01 | opencode.md:16-19,24-29 (V2 keys, no `tools`) | mapped |
| CON-OC-02 | opencode.md:113-126 | mapped |
| FR-AGT-08 | grep for model names over the 11 files: 0 hits | mapped |

Code line references checked and correct: Claude Code.md:19,26,52,82; opencode.md:22,29,56,63,89-111,135,160; macOS Python.md:29 (install.py:15).

## 2. Leftovers

Counts per file.

- skills/harness-common/topics/Claude Code.md (3):
  - :23 cites `.rearch/STATE.md`, deleted in Stage 6.
  - :34 cites `.rearch/baseline.md`, deleted in Stage 6.
  - :23,:34,:88 say "this run" / "of this run": history wording, breaks docs-style.md:14. Needs a doc change.
- skills/harness-common/topics/macOS Python.md (3):
  - :14 cites "`skills/qa-session` audit X1", an audit file that is deleted.
  - :43 "Phase 2 also adds `__pycache__/` ... to `.gitignore`": history. .gitignore is the fact.
  - :44 cites `.rearch/phases.md` and `.rearch/baseline.md`: deleted.
- skills/harness-common/topics/opencode.md (3):
  - :91 a stray line "`override files`" after the answer paragraph. Dead text.
  - :89 "(A2)" is a `.rearch` answer id, meaningless after Stage 6.
  - :5 "not installed on the maintainer's Mac" is a time-bound statement, not a fact about opencode. Keep, low priority.
- skills/rearchitect/SKILL.md (1):
  - :26,:115 call `opencode.py` without a path. From a skill the file is `skills/harness-common/scripts/opencode.py`, run as `/usr/bin/python3 -I`. Needs a doc change.
- agents/*: 0. skills/ai-notes: 0 leftovers. skills/writing-craft: 0. docs-style.md, state.md: 0.

## 3. Doc and code mismatches

a. rearchitect/SKILL.md:112 moves requirements.md and architecture.md to `docs/` as they are. Deviations make them stale (needs a code change in the skill, one added step):
   - CON-CC-03 (requirements.md:517) is wrong, deviations.md Phase 1 item 1.
   - NFR-12 (requirements.md:508) is broken by `review_threads.py resolve`, Phase 9 item 7.
   - architecture.md CLI table: check_page `--live`, review_threads signature, gate.py `open` form (Phase 7 item 1, Phase 8 item 1, Phase 9 item 5).
   - architecture.md:52 "plus apply-tiers/clear-tiers if Phase 1 finds no per-spawn model" and :93,:96 "Phase 1 settles it": settled, override files.
   - architecture.md:201 traceability row says FR-RA-01..13: FR-RA-14 is unmapped there.
   - baseline.md lists the old parse command (deviations Phase 1 item 7; baseline.md:13 now shows `compile()`, so this one is already fixed).
b. FR-AGT-08 trap: requirements.md:60 (model names in the FR text), :515 (`sonnet, opus`), :591 (`deepseek/...`) hold model names. After the move to `docs/` the repo test (tests/test_repo_rules.py, skips only `.rearch/`, `.attack-plan/`, `.ai-notes/`) fails on them. Needs a code change: SKILL.md:112 must say to scrub model names when moving.
c. ai-notes/SKILL.md:57-71 "Handing off to a new session" (15 lines) has no FR. Not in requirements.md, not in the README row (README.md:14), overlaps the global `handoff` skill, names the host tool `mcp__synopia__start_session`. Needs a decision: add FR-NOTES-08 and a README mention, or drop. No model name.
d. requirements.md evidence lines for NOTES, WRIT and RA cite old line numbers (for example ai-notes SKILL.md:26-38, writing-craft :14-21, rearchitect :86-94). They describe the pre-rewrite files. Stage 6 move: refresh or drop evidence lines. Doc only.
e. rearch-auditor.md:64-81 final report has Coverage, Requirements, Leftovers, Bugs. It lacks a section for doc/code mismatches and for model names, which Stage 6 step 2 (SKILL.md:110) implies ("stale comments") and FR-AGT-08 needs. Needs a code change (add two sections), low priority.
f. README rows for ai-notes, rearchitect, writing-craft match the files, apart from c.

## 4. Model names or ids (FR-AGT-08)

0 hits in the 11 files. Placeholders `<provider>/<model>` (state.md:65-67) and `<value>` (harness-common state.md) are not names. `claude-plugins-official` (Claude Code.md:96) is a path. Outside the group, 3 hits in requirements.md (3b) and 5 in .rearch/baseline.md (skipped by the test, deleted in Stage 6).

## 5. FR-APE-15 (outside this group)

Not built. skills/attack-plan-milestone-execute/resources/review-pass.md:28 ("REPLY = ... the user posts the text"), :52 (resolve only after the user says it is posted), :54 ("never post a reply as the user"), :55 (pass ends with a bot REPLY waiting). Needs a code change in that skill. Nothing in this group depends on it.

## Needs a code change

1. rearchitect/SKILL.md:112 (3a, 3b): add a step to fix stale requirements/architecture text and scrub model names before moving to `docs/`.
2. rearchitect/SKILL.md:26,115: path for `opencode.py`.
3. ai-notes/SKILL.md:57-71 (3c): decide FR or drop.
4. Topic docs (2): Claude Code.md:23,34,88; macOS Python.md:14,43,44; opencode.md:89,91.
5. rearch-auditor.md:64-81 (3e): optional.
