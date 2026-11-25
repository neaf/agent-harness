# Audit: notes-and-writing

## Coverage
| File | Lines | Read fully |
|---|---|---|
| README.md | 34 | yes |
| instructions/global.md | 20 | yes |
| skills/ai-notes/SKILL.md | 68 | yes |
| skills/writing-craft/SKILL.md | 87 | yes |

Also grepped all of skills/, agents/, install.py for references to both skills.

## Functional behavior
- F1: Before writing any human-read text (pages, QA scripts, runbooks, plans, PR descriptions, tickets, long replies) the agent follows writing-craft. Evidence: instructions/global.md:20, skills/writing-craft/SKILL.md:3. Status: active.
- F2: writing-craft prescribes a pre-writing check (reader, moment, one job, reader vocabulary). Evidence: writing-craft/SKILL.md:14-21. Status: active.
- F3: Form follows the reader's task: sequence, decision, reference, explanation. Precondition, warning and expected result sit beside the action. Evidence: writing-craft/SKILL.md:23-34. Status: active.
- F4: Word rules: exact word, reader vocabulary, one term per concept, no spec ids, no placeholders in live steps. Evidence: writing-craft/SKILL.md:36-44. Status: active.
- F5: Facts are verified before writing. Unverifiable points are labelled as assumptions with the check that settles them. Evidence: writing-craft/SKILL.md:46-50. Status: active.
- F6: Revision starts from the specific failure (order, word, missing fact, layout), then cuts. Evidence: writing-craft/SKILL.md:61-74. Status: active.
- F7: On a new session the agent reads `.ai-notes/README.md`, then the area README, and resumes from its to-do. Evidence: ai-notes/SKILL.md:10-14, global.md:11. Status: active.
- F8: The agent creates `.ai-notes/` when work spans more than one session, subagent or PR. Evidence: ai-notes/SKILL.md:14. Status: active.
- F9: Notes live at `<repo root>/.ai-notes/<area-slug>/`, committed by default. Private use goes through `.git/info/exclude`, never `.gitignore`. Evidence: ai-notes/SKILL.md:18-20, README.md:15. Status: active.
- F10: Area README has fixed parts: goal, links, files, workstreams table, to do, open questions, lessons. Plus `findings.md`, `<topic>.md`, dated deliverables. Evidence: ai-notes/SKILL.md:26-38. Status: active.
- F11: Notes writing rules: summary first, reproducible evidence, absolute dates, verified vs inferred, retracted theories kept, user decisions dated with reason, one fact in one place, mark superseded instead of deleting. Evidence: ai-notes/SKILL.md:40-48. Status: active.
- F12: Lifecycle: update README as work moves, ticket per workstream, write stop point at session end, tick after merge. Evidence: ai-notes/SKILL.md:50-55. Status: active.
- F13: Orchestrator spawns fresh subagents with self-contained prompts pointing at notes. Worktree subagents return text and the orchestrator writes notes. Reports are treated as claims. Evidence: ai-notes/SKILL.md:57-68. Status: active.
- F14: README documents the repo layout, the skill table and the install flags. Evidence: README.md:5-34. Status: active.
- F15: global.md is the single global instruction file, copied unchanged to both tools. Evidence: install.py:45-47, README.md:9. Status: active.

## External facts and quirks
- X1: Worktree subagents "cannot write the notes of the main checkout". Cause stated nowhere. It is a convention (shell starts in the main checkout, ai-notes/SKILL.md:68), not a hard limit. Source: unverified.
- X2: "Every shell command starts in the main checkout" (cwd resets per call). Matches the Claude Code Bash behaviour. Not checked for opencode. Source: unverified for opencode.
- X3: `.git/info/exclude` covers every worktree and is not shared (ai-notes/SKILL.md:20). Source: git docs (info/exclude lives in the common git dir). True.
- X4: global.md is installed verbatim into `~/.claude/CLAUDE.md` and `~/.config/opencode/AGENTS.md`, so wording must hold in both tools. Source: code (install.py:45-47).

## Doc and code inconsistencies
- D1: attack-plan-milestone-execute/SKILL.md:32 tells the agent to resume from the notes README's "State" section. ai-notes/SKILL.md:26-35 defines no "State" section (it has Workstreams table, To do, Open questions, Lessons). The milestone skill's README (SKILL.md:62) lists a PR table and next step instead. Same notes area, two README shapes.
- D2: qa-session/SKILL.md:38-43 defines area files `sources.md`, `decisions.md`, `rework-log.md`. ai-notes defines `findings.md` and `<topic>.md`. Compatible but unregistered in ai-notes. ai-notes README rule "one line per file" is the only link.
- D3: ai-notes/SKILL.md:20 says private notes go in `.git/info/exclude`. attack-plan-create/SKILL.md:18 repeats the same rule for `.attack-plan/`. qa-session/references/publishing.md:8 repeats it by reference. Rule is restated in 3 places.
- D4: README.md:15 says ai-notes lets a session "hand work to fresh subagents and later sessions". Matches the skill. No inconsistency found in README rows 13-21 against `skills/` (7 dirs, 7 rows).
- D5: global.md:11 points to `.ai-notes/` but rearchitect uses `.rearch/` with `STATE.md` (rearchitect/SKILL.md:12) and attack-plan-create uses `.attack-plan/<slug>/STATE.md` (SKILL.md:18). Three state conventions, one global rule that names only one. ai-notes line 14 ("create it when work spans more than one session") also applies to those runs but they do not use it.
- D6: rearchitect/SKILL.md:47 tells the orchestrator to send "the writing-rules line" to auditors. The writing-craft skill is not named there. Auditor output is read by a human-facing architect, not by a person, so this is compact style (system prompt "no mannered prose"), not writing-craft. Two writing standards coexist, unlabelled.
- D7: writing-craft is referenced by name in qa-session/SKILL.md:10 and qa-session/references/briefs.md:11 only. attack-plan-create (plans, ticket text, three pages, per document-template.md:3) and its agents never cite it. global.md:20 covers them only through the global rule.

## Assumptions to revalidate
- A1: A tracker exists ("Create a ticket when a workstream starts", ai-notes/SKILL.md:53). Without one the rule has no target.
- A2: Repo root is writable and the work has a single repo. `.ai-notes/` at `<repo root>` (ai-notes/SKILL.md:18). Cross-repo work has no home.
- A3: The agent has skills named `frontend-design` and REA (global.md:18). Neither ships in this repo (`skills/` has 7 dirs). Instruction is dead on a machine without them.
- A4: Serena MCP exists (global.md:3). It is worded "when available", so safe.
- A5: global.md:16 says "output Claude has already seen pass". The file is also installed as opencode AGENTS.md, where the model is not Claude.
- A6: Model follows a "see the X skill" pointer. global.md:11 and :20 rely on the skill description triggering. M9 and M10 in baseline.md are manual only, so this is unproven.
- A7: Notes are read by an LLM, so absolute dates and file:line evidence (ai-notes/SKILL.md:43-44) go stale when code moves. Commit SHA is the only stable anchor, and it is listed last.

## Bugs
- B1 [low]: global.md:8 and :17 both govern delegation and overlap with ai-notes/SKILL.md:59 ("fork" = fresh subagent) and global.md:13 (same rule again). The same rule is stated 3 times, with slightly different wording. Scenario: a later edit of one copy leaves the others stale.
- B2 [low]: global.md:9 and :16 both say "do not run tests after every step". Scenario: same drift risk as B1.
- B3 [low]: ai-notes/SKILL.md:3 description says "One orchestrator session owns the notes and delegates". For a single-session task with no subagent the trigger "when an investigation or multi-step piece of work starts" (line 3) contradicts line 14 ("spans more than one session, one subagent or one PR"). Scenario: a multi-step single-session task triggers the skill by description but line 14 says do not create notes.
- B4 [low]: writing-craft/SKILL.md:78 says use "numbered sequence with checkboxes" for walk-throughs, line 27 says add checkboxes "when progress matters". Scenario: a non-QA runbook gets checkboxes it does not need.
- B5 [low]: writing-craft/SKILL.md:36-40 uses "R4", "D1" as bad-example ids and section 7 line 80 bans such ids. The audit template (rearchitect auditor) requires ids like F1, D1 in files an agent reads. Scope of the ban (human-facing pages only) is not stated in writing-craft.

## Dead code, leftovers, stale comments
- L1: writing-craft/SKILL.md:12 manuals/poster/Swiss typography paragraph. Motivation text, no action. Candidate to cut.
- L2: writing-craft/SKILL.md:76-87 section 7 restates sections 2-6 (10 bullets). Examples are QA-specific ("persona", "reviewer", "R4"), which shows its origin in qa-session.
- L3: writing-craft examples at :38, :50 ("reviewer", "assigned to 4 files", "review app") are QA-session leftovers. A generic reader sees product-specific scenarios.
- L4: global.md:18 names `frontend-design` and REA, absent from the repo.
- L5: ai-notes/SKILL.md:44 example date `2026-11-19` is a hard-coded sample.
- L6: README.md:17-21 repeat the test commands that exist in each skill. Three of the six tests lines would break if the path changes. Duplicated.

## Improvement areas
- I1: One state/notes convention. ai-notes, `.rearch/STATE.md` and `.attack-plan/<slug>/STATE.md` solve the same resume problem with three layouts and three exclusion paragraphs. A shared contract (resume file name, "Next" line, exclude rule) would remove D3, D5 and D1.
- I2: Define the README sections that other skills rely on ("State", "Next step", "Workstreams") in one place, and make milestone-execute and qa-session cite it (fixes D1, D2).
- I3: Dedupe global.md: merge lines 8+17 (delegation) and 9+16 (test output), drop line 13 (it duplicates ai-notes:59). Saves about 4 lines and one drift path each.
- I4: Make global.md tool-neutral: line 16 "Claude", line 3 "Serena MCP", line 18 skill names. It is shipped to opencode too (X4).
- I5: Shrink writing-craft: cut section 7 into the sections it repeats, replace QA-only examples with neutral ones. Target about 55 lines. The skill is loaded in full by every QA brief (qa-session/references/briefs.md:11), so size costs tokens per subagent.
- I6: Name the exempt class in writing-craft: machine-read and agent-to-agent text (audits, briefs) follows other rules (fix B5, D6).
- I7: Trigger text. global.md:20 and the skill description both carry the same trigger list. Keep the list in one place and have the other point to it.
- I8: Add a minimal notes template (README skeleton) beside ai-notes so subagents copy it. Currently the shape is prose at :26-38.
- I9: attack-plan-create and its agents should cite writing-craft explicitly, as qa-session does (D7).

## Interfaces
- Exposes: skill `ai-notes` (file layout `.ai-notes/<area>/README.md`, `findings.md`, `<topic>.md`, dated deliverables; rules for git exclusion, dated decisions, "one fact in one place"). Skill `writing-craft` (rules loaded in full by qa-session briefs). `instructions/global.md` (installed to both tools). README.md as the human index.
- Consumes: install.py (copies global.md, symlinks skills, install.py:45-50). feedback-watch skips `.ai-notes` when watching files (feedback-watch/scripts/watch.py:17). milestone-execute and qa-session create notes areas under ai-notes rules (milestone-execute/SKILL.md:32,61, resources/review-pass.md:15, qa-session/SKILL.md:38,61,101). qa-session/references/publishing.md:8 cites ai-notes for the exclude rule. The rearch-auditor/rearchitect skills reference neither skill.
- Threading: none. Prompt text only. Loaded at session start (global.md) or on skill trigger.

## Open questions for the user
- Q1: Should `.rearch/` and `.attack-plan/` move under `.ai-notes/` (one convention), or stay separate?
- Q2: Is `global.md` meant to be tool-neutral for opencode (drop "Claude", Serena, `frontend-design`, REA)?
- Q3: Should writing-craft apply to agent-to-agent briefs and audit reports, or only to human-read text?
- Q4: Keep the QA-flavoured examples in writing-craft, or neutralise them?
- Q5: Is a skill that exists only outside this repo (`frontend-design`, REA) supposed to be installed by the harness?
