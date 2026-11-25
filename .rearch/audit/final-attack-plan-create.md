# Final audit: attack-plan-create (APC)

Result: 23 mapped, 2 partial, 0 missing of 25 requirements. Tests: attack-plan-create 68 OK, harness-common 81 OK. No model name in the group (grep: 0 hits). `git status` clean after the runs.
Scope read in full: SKILL.md (183 lines), 5 references, gate.py (292), check_draft.py (331), both test files, markdown.py (125), test_markdown.py (116), 3 agents.
Dropped by Q13, so not counted: FR-APC-18, -19. grep for "Milestone specs", `reviews/`, `round-<n>`: 0 hits.
FR-APE-15 belongs to execute, not built here. One effect on this group: finding 3.

## 1. Traceability

| ID | file:line | Status |
|---|---|---|
| FR-APC-01 | SKILL.md:18; references/state.md:3-19 | mapped |
| FR-APC-02 | gate.py:24,152-160; SKILL.md:55-153 | mapped |
| FR-APC-03 | SKILL.md:37-53 | mapped |
| FR-APC-04 | SKILL.md:12,49,51; gate.py:113-119 | mapped |
| FR-APC-05 | gate.py:105,171-190; markdown.py:32-45,60-95 | mapped |
| FR-APC-06 | gate.py:121-132,152-160; SKILL.md:53 | mapped |
| FR-APC-07 | gate.py:27-31,146-148 | mapped |
| FR-APC-08 | gate.py:206-250,262-267; check_draft.py:282-327 | mapped |
| FR-APC-09 | agents/attack-plan-*.md; references/briefs.md:3-75 (every brief: path or "no file", word cap) | mapped |
| FR-APC-10 | SKILL.md:76,150; briefs.md:9 | mapped |
| FR-APC-11 | check_draft.py:19-49,76-169,175-224 | mapped |
| FR-APC-12 | SKILL.md:44; references/questions.md:1-58 | mapped |
| FR-APC-13 | references/executable-plan.md:22-47; check_draft.py:51-67,227-275 | mapped |
| FR-APC-14 | SKILL.md:135-143; harness-common/references/publishing.md:25,37 | mapped |
| FR-APC-15 | SKILL.md:145-152 | mapped |
| FR-APC-16 | document-template.md:24; check_draft.py:25; SKILL.md:131 | mapped |
| FR-APC-17 | SKILL.md:110; state.md:13; document-template.md:47 (internal, not published) | mapped |
| FR-APC-20 | state.md:29 reads "Stage: 4" | mapped |
| FR-XS-02 | markdown.py:32-57; check_draft.py:145 | mapped |
| FR-AGT-08 | whole group, 0 model names; agents use `tier:` (install.py:19) | mapped |
| NFR-01 | `#!/usr/bin/python3`, stdlib only, no 3.10+ syntax | mapped |
| NFR-03 | gate.py, check_draft.py: one line per result | mapped |
| NFR-04 | tests/test_gate.py, test_check_draft.py, test_markdown.py | mapped |
| NFR-05 | .gitignore:3 `__pycache__/`; tree clean after tests | mapped |
| NFR-09 | duplicated rules, finding 9 | partial |
| NFR-13 | agents inherit it from preamble.md:7; SKILL.md:24-35 does not say it | partial |

## 2. Leftovers

| # | file:line | Finding | Code change |
|---|---|---|---|
| 1 | SKILL.md:176 | "tracks verification, review and surprises" keeps the dropped Surprises idea (Q16) | yes, text |
| 2 | references/executable-plan.md:9 | "so its surprises show early", same word (Q16) | yes, text |
| 3 | references/executable-plan.md:97 | Human-only gates lists "replies to review bots". FR-APE-15 has the orchestrator post bot REPLY threads. Human threads stay human-only | yes, text |
| 4 | scripts/check_draft.py:246-247 | `TASK_TITLE.fullmatch(title)` run twice per task, one result unpacked two ways | optional cleanup |
| 5 | skills/attack-plan-create/scripts/__pycache__ | cpython-39 caches on disk, ignored by .gitignore, untracked | no |

No dead function, no import of a deleted file. `gate.section`, `gate.HEADING`, `check_draft.headings` are gone (grep: 0).

## 3. Doc and code mismatches

| # | file:line | Mismatch | Code change |
|---|---|---|---|
| 6 | skills/harness-common/scripts/markdown.py:4 | Docstring says "Used by attack-plan-create's gate.py and check_draft.py". qa-session/scripts/check_page.py:15 imports it too | yes, one line |
| 7 | skills/harness-common/SKILL.md:44 | Same "Used by `attack-plan-create`" in the Scripts row | yes, one line |
| 8 | .rearch/architecture.md:133 | gate.py row says `open <id> --stage S`. Real form is `open <work folder> <stage> <section>` (deviation Phase 7 no. 1) | doc only |
| 9 | .rearch/architecture.md:134 | check_draft.py row lacks `--milestone N` and the exit 1 on a bad command line | doc only |
| 10 | .rearch/architecture.md:269 | Promises B11 (a gate with no file is never drift-checked) is "documented in create state.md". state.md has no such line (grep "no file", "drift": 0) | yes, one line in state.md |
| 11 | .rearch/architecture.md:232-234 | Old-location table (`gate.section()`, `check_draft.headings()`) describes removed code; keep as history or drop | doc only |
| 12 | SKILL.md:94 vs check_draft.py:45 | SKILL.md says "no table, model, class, endpoint or query". The check warns only on controller, endpoint, serializer, migration, orm, sql (L6 dropped class, query, schema) | optional, reword SKILL.md |
| 13 | .rearch/baseline.md | Still lists 102 tests. Now 331 in 7 suites (deviations Phase 10 no. 6) | doc only |
| 14 | SKILL.md:24-35 | NFR-13: Spawns section does not say a subagent never spawns one. Link to subagents.md:7 exists at :34 | yes, one line |
| 15 | agents/attack-plan-critic.md:14, designer.md:37, reader.md:57 | The same "Evidence comes from our code... third-party internals" sentence three times. Also pinned-commit rule in 3 agents and SKILL.md:76 (NFR-09) | optional |
| 16 | README.md:16 | Row matches the skill. No stale text | no |

## 4. Model names (FR-AGT-08)

0 hits in skills/attack-plan-create/**, the 3 agents, markdown.py, test_markdown.py. Agent frontmatter holds `tier: strong|fast` only. state.md:49-52 uses `<value>` placeholders.

## Needs a code or text change

Findings 1, 2, 3, 6, 7, 10, 14 (7 edits, none in logic). Optional: 4, 12, 15. Doc-only in .rearch: 8, 9, 11, 13.
