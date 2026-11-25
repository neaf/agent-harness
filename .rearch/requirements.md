# Functional requirements

Source: 6 aspect audits plus seams.md in `.rearch/audit/`, checked against code at `rearch-base` (d4b56d4). Prompt files are product source: their stated workflow is current behavior unless a script or `install.py` contradicts it.

Status values: `kept` (current behavior, stays; a listed fix may apply), `open` (conflict or choice, see the question), `experimental` (stated but untested), `unclear` (spec with no producer or consumer). Evidence `audit/<aspect>.md F3` is a text reference to the bullet; audit bullets are not anchors.

## Install (INST)

- FR-INST-01: Render one Claude agent per `agents/*.md` into `~/.claude/agents/<file>`: `name`, `description`, `tools`, then the body. No `model` line (FR-AGT-02).
  Evidence: install.py:24-27,43. audit/install-and-config.md F1
  Status: kept, model line removed by user decision 2026-11-25
- FR-INST-02: Render one opencode agent per `agents/*.md` into `~/.config/opencode/agents/<file>`: `description`, `mode: subagent`. No `model` line (FR-AGT-02).
  Evidence: install.py:30-35,44. audit/install-and-config.md F2
  Status: kept, model line removed by user decision 2026-11-25
- FR-INST-03: Copy `instructions/global.md` verbatim to `~/.claude/CLAUDE.md` and `~/.config/opencode/AGENTS.md`.
  Evidence: install.py:45-47
  Status: kept. Local additions to those files: Q5.
- FR-INST-04: Symlink every directory in `skills/` into both tools' `skills/` folder.
  Evidence: install.py:48-51
  Status: kept
- FR-INST-05: Use a tool when its config folder exists or its binary is on PATH. `--claude 0|1` and `--opencode 0|1` override.
  Evidence: install.py:62-65, README.md:30,34
  Status: kept
- FR-INST-06: Plan first. Write only when content differs, link only when the link target differs. A second run is a no-op.
  Evidence: install.py:68-76
  Status: kept
- FR-INST-07: `--check` prints the plan and `<n> change(s) needed`, writes nothing, exits 1 on drift and 0 when clean.
  Evidence: install.py:81-83, README.md:11
  Status: kept
- FR-INST-08: Replacing any existing item needs `y` at the prompt or `--yes`. No TTY and no `--yes`: change nothing, exit 2. Declined: exit with a code distinct from drift (today both are 1, install.py:83,94).
  Evidence: install.py:84-94, README.md:32
  Status: kept, exit-code split is a fix (audit B8).
- FR-INST-09: Remove installed agents and skill links whose source was deleted or renamed; `--check` reports them.
  Evidence: absent today, install.py:41-51 only adds. audit/install-and-config.md B1
  Status: open, Q1
- FR-INST-10: Reject a malformed agent file with the file name and the bad key: missing fence, non `key: value` line, missing key, unknown tier.
  Evidence: install.py:17-21,25,31 raise bare ValueError/KeyError. audit B5, seams S1
  Status: kept (fix)
- FR-INST-11: Rendered frontmatter is valid YAML whatever the description holds (quote the value). Three descriptions contain `: ` today.
  Evidence: install.py:26,32; agents/attack-plan-critic.md:3, rearch-auditor.md:3, rearch-phase.md:3
  Status: kept (fix). Whether hosts load them today: Q4.
- FR-INST-12: When a destination is a symlink to a file, replace the link instead of writing through it. A destination that is a directory where a file goes is reported, not crashed on.
  Evidence: install.py:71,102. audit B3
  Status: kept (fix)
- FR-INST-13: Replacing a real (non-symlink) folder at a skill destination under `--yes`.
  Evidence: install.py:97-98 rmtree, no backup. audit B2
  Status: open, Q6
- FR-INST-14: Missing `agents/` or `skills/` folder gives a named error, not a traceback.
  Evidence: install.py:41,48. audit B6
  Status: kept (fix)

## Agents and tiers (AGT)

- FR-AGT-01: One neutral agent source format: frontmatter `name`, `description`, `tier`, `tools`, then the prompt body. README documents it.
  Evidence: README.md:8, agents/*.md:1-6
  Status: kept
- FR-AGT-02: Three abstract tiers `fast` (cheap), `default` (session model), `strong` (most capable). Agents declare a tier. Nothing in the repo maps a tier to a model: `targets/models.json` is deleted, and install.py writes no `model` line for either tool.
  Evidence: today targets/models.json:2-3, install.py:24-35. User decision 2026-11-25 (Q3).
  Status: kept, mapping removed
- FR-AGT-08: No model name, family or id appears anywhere in the repo: skills, agents, instructions, install.py, README or tests. Today targets/models.json:2-3 and rearchitect SKILL.md:20-21,25 have them (Sonnet, Opus, DeepSeek Flash, DeepSeek Pro, `model: sonnet`). A test greps the tree for model names and fails on any hit.
  Evidence: `git grep` 2026-11-25; user decision (Q3).
  Status: kept
- FR-AGT-07: Model resolution happens at run time, in the tool that runs the skill (Claude Code, opencode, or a later one). When a run starts (rearchitect Stage 0, and on resume), the orchestrator lists the models and versions that tool offers now, proposes a model for each tier (fast = cheapest that suits the auditor's job, strong = most capable), and asks the user to confirm before any tiered spawn. This is a gate. The user may override any tier or put every tier on one model (for example the most capable model everywhere on a work machine, or the cheapest everywhere on a personal one). The confirmed mapping is recorded in the run's state (`.rearch/baseline.md` for rearchitect). Every spawn then passes the resolved model for the agent's tier. How a run applies a model per spawn in each tool is an architecture question (Q37).
  Evidence: user decision 2026-11-25 (Q3).
  Status: kept
- FR-AGT-03: Six agents ship: attack-plan-critic (strong), attack-plan-designer (strong), attack-plan-reader (fast), rearch-architect (strong), rearch-auditor (fast), rearch-phase (default).
  Evidence: agents/*.md:4
  Status: kept
- FR-AGT-04: Agents whose prompt says read-only (auditor, critic, reader, designer) get no Edit tool. Claude enforces it through `tools`. opencode drops `tools`, so nothing enforces it there.
  Evidence: agents/*.md:5, install.py:30-35. seams S2, audit/rearchitect.md X2
  Status: open, Q2
- FR-AGT-05: A skill that names an agent that is not installed falls back to a general-purpose subagent with the agent body pasted. The skill does not say where the harness checkout is.
  Evidence: skills/rearchitect/SKILL.md:25, skills/attack-plan-create/SKILL.md:26. seams S4, S5
  Status: experimental (never exercised; M1/M2 cover only the installed path)
- FR-AGT-06: The writing-rules line and the opencode `execute` sandbox line appear in every agent body. The sandbox line is opencode-only and ships to Claude agents too.
  Evidence: agents/*.md:10-12. seams I3, D3
  Status: kept, one copy per fact (architect's call)

## Global instructions (GLB)

- FR-GLB-01: `instructions/global.md` is the one global instruction file for both tools.
  Evidence: install.py:45-47, README.md:9
  Status: kept
- FR-GLB-02: Code-change hygiene: semantic tools when available, run compile/test before reporting done, never expose secrets, match style, project `AGENTS.md` wins.
  Evidence: global.md:3-7
  Status: kept
- FR-GLB-03: Delegation: self-contained subagent briefs with task, file ownership and report format; parallel background runs; "fork"/"clean context" means a fresh subagent; review deliverables go to a background subagent whose description starts `For review: `, with a one-line start notice and a ready notice.
  Evidence: global.md:8,13,17; skills/ai-notes/SKILL.md:56-59
  Status: kept. Three overlapping copies: Q8.
- FR-GLB-04: Minimal output: tests at milestones only, output filtered to pass/fail line and failing numbers; tools default to one summary line.
  Evidence: global.md:9,10,16
  Status: kept. Lines 9 and 16 duplicate: Q8.
- FR-GLB-05: Multi-session, multi-subagent or multi-PR work keeps notes per the `ai-notes` skill; read `.ai-notes/README.md` at session start.
  Evidence: global.md:11
  Status: kept
- FR-GLB-06: After a push, a PR open, or a long local fix-and-test loop, arm `feedback-watch`, one watcher per PR set, re-arm on expiry.
  Evidence: global.md:12
  Status: kept
- FR-GLB-07: Machine time over tokens; reverse engineering reads the binary/source when the user starts such a task; external tools are understood from their documented surface, settled by one scripted check.
  Evidence: global.md:14-15
  Status: kept
- FR-GLB-08: Check available skills before a task and name a fitting skill in delegated briefs. Examples cite `frontend-design` and REA, which this repo does not ship.
  Evidence: global.md:18; skills/ has 7 dirs
  Status: open, Q9
- FR-GLB-09: PR, issue and ticket numbers in replies are markdown links.
  Evidence: global.md:19
  Status: kept
- FR-GLB-10: Follow `writing-craft` before any human-read text.
  Evidence: global.md:20
  Status: kept
- FR-GLB-11: Wording holds in both hosts. Today line 16 says "Claude".
  Evidence: global.md:16. audit/notes-and-writing.md A5, I4
  Status: open, Q8

## Notes (NOTES, skill ai-notes)

- FR-NOTES-01: On a new session read `.ai-notes/README.md`, then the area README, and resume from its to-do.
  Evidence: skills/ai-notes/SKILL.md:10-14
  Status: kept
- FR-NOTES-02: Create notes when work spans more than one session, subagent or PR. The skill description also triggers on any "multi-step piece of work".
  Evidence: ai-notes/SKILL.md:3 vs :14. audit/notes-and-writing.md B3
  Status: open, Q10
- FR-NOTES-03: Notes live at `<repo root>/.ai-notes/<area-slug>/`, committed by default; private use via `.git/info/exclude`, never `.gitignore`.
  Evidence: ai-notes/SKILL.md:18-20, README.md:15
  Status: kept
- FR-NOTES-04: Area README parts: goal, links, files, workstreams table, to do, open questions, lessons. Plus `findings.md`, `<topic>.md`, dated deliverables.
  Evidence: ai-notes/SKILL.md:26-38
  Status: kept. Other skills add "State (start here)" and extra files: Q11.
- FR-NOTES-05: Notes rules: summary first, reproducible evidence, absolute dates, verified vs inferred, retracted theories kept, dated user decisions with reason, one fact in one place, mark superseded instead of deleting.
  Evidence: ai-notes/SKILL.md:40-48
  Status: kept
- FR-NOTES-06: Lifecycle: update as work moves, a ticket per workstream, stop point at session end, tick after merge.
  Evidence: ai-notes/SKILL.md:50-55
  Status: kept
- FR-NOTES-07: One orchestrator owns the notes. Subagents get self-contained prompts pointing at notes. Worktree subagents return text and the orchestrator writes. Reports are claims.
  Evidence: ai-notes/SKILL.md:57-68
  Status: kept

## Writing (WRIT, skill writing-craft)

- FR-WRIT-01: Pre-writing check: reader, moment, one job, reader vocabulary.
  Evidence: writing-craft/SKILL.md:14-21
  Status: kept
- FR-WRIT-02: Form follows the reader's task (sequence, decision, reference, explanation). Precondition, warning and expected result sit beside the action.
  Evidence: writing-craft/SKILL.md:23-34
  Status: kept
- FR-WRIT-03: Word rules: exact word, reader vocabulary, one term per concept, no spec ids, no placeholders in live steps.
  Evidence: writing-craft/SKILL.md:36-44
  Status: kept
- FR-WRIT-04: Verify facts before writing; label the rest as assumptions with the check that settles them.
  Evidence: writing-craft/SKILL.md:46-50
  Status: kept
- FR-WRIT-05: Revision starts from the reader's specific failure, then cuts.
  Evidence: writing-craft/SKILL.md:61-74
  Status: kept
- FR-WRIT-06: Scope: human-read text only, or also agent-to-agent briefs and audit reports. Three style mechanisms coexist (writing-craft, "No mannered prose" line, docs-style.md). attack-plan skills and execute never cite writing-craft for plans, PR descriptions and tickets.
  Evidence: seams S10; notes-and-writing D6, D7, B5
  Status: open, Q12
- FR-WRIT-07: Section 7 restates sections 2-6; examples are QA-specific.
  Evidence: writing-craft/SKILL.md:76-87, :38, :50
  Status: open, Q12

## Attack plan create (APC)

- FR-APC-01: Work folder `.attack-plan/<slug>/` with STATE.md, gates.json, ledger.md, sources/, draft/, audit/; committed by default, `.git/info/exclude` for private.
  Evidence: create/SKILL.md:18, references/state.md:3-17
  Status: kept
- FR-APC-02: Eight stages gate opening: intake, sources, product, product-review, technical, milestones, audit, publish. A section cannot open while a gate of the same or an earlier stage is neither approved nor not reviewed.
  Evidence: gate.py:17-18,118-121; create/SKILL.md:50-136
  Status: kept
- FR-APC-03: Seven-step section loop: open, draft, challenge (fresh critic each round), grill one question at a time, record grilling, review in full, approve or skip. Three rounds with blocking findings go to the author.
  Evidence: create/SKILL.md:36-42
  Status: kept
- FR-APC-04: The author can speed up, skip reviews or draft ahead. Skipped sections are `not reviewed`; each stage end lists them.
  Evidence: create/SKILL.md:44-46; gate.py:80-86
  Status: kept
- FR-APC-05: Approval stores a SHA-256 of the section (file + heading). `status` and `verify` flag later edits. Section slicing ignores headings inside code fences, as check_draft does.
  Evidence: gate.py:66-78,132-162 (no fence handling). attack-plan B2, seams B1
  Status: kept (fence fix). Multi-location sections such as `tasks-m<n>`: Q22.
- FR-APC-06: `reopen` with a reason returns the gate to an openable state and marks every later approved gate stale; the loop then runs from step 1.
  Evidence: create/SKILL.md:48; gate.py:42-43 refuses `open` on `drafting`, gate.py:93 sets `drafting`. attack-plan B1
  Status: kept (fix). Staleness by list order, not stage order (gate.py:94): kept, document it.
- FR-APC-07: `verify` flags technical drafts written before the technical stage opened.
  Evidence: gate.py:20-24,112-114
  Status: kept
- FR-APC-08: Gate CLI rejects bad input with a named message: non-numeric `--rounds`, missing positionals.
  Evidence: gate.py:181 (uncaught ValueError), :196. attack-plan B6
  Status: kept (fix)
- FR-APC-09: Three subagents with role briefs: reader (fast), critic (strong), designer (strong). Each brief names its output path and return length.
  Evidence: agents/attack-plan-*.md, references/briefs.md. attack-plan D10 (three briefs name no path)
  Status: kept (fix D10)
- FR-APC-10: Stage 1 pins the SHA of `origin/<default>`; all code reads use that SHA, never the working tree. Stage 8 rechecks drift.
  Evidence: create/SKILL.md:63-76, briefs.md:7
  Status: kept
- FR-APC-11: `check_draft.py <draft> [--product]`: required sections in order, question format Q<n>/Context/Question/Recommendation, no estimates, no Option A-D, no decision log, balanced backticks, product-part code-term warnings, `--product` rejects early technical content. Output `PASS|WARN|FAIL file: msg`, exit 1 on FAIL.
  Evidence: check_draft.py:10-127
  Status: kept. Fixes: estimate check scoped to table headers (B7), catch template-banned "P1"/"risk 1"/"Proposed" (B8), milestones section by numbered heading (B9), code-term list without "class"/"query"/"schema" false positives (L6).
- FR-APC-12: Questions to the author follow references/questions.md: one at a time, each with recommendation and safe default.
  Evidence: create/SKILL.md:39, references/questions.md
  Status: kept
- FR-APC-13: Task block per PR: title `[<code> M<n>-<k>] ...`, base, files, rule everywhere, invariants and tests, edge cases, ordering, reviewers, context for an outside reviewer, rationale, QA, depends on, ticket.
  Evidence: references/executable-plan.md:22-38
  Status: kept. Machine-checkable format: Q20.
- FR-APC-14: Publish to repo Markdown (`docs/attack-plans/<slug>/`, default) or Notion; read back after each write; keep reviewers' edits; commit only when the author asks; drafts stay the source.
  Evidence: references/publishing.md:5-40, create/SKILL.md:130-134
  Status: kept
- FR-APC-15: Stage 8 refresh: re-read published pages, reopen each changed section, offer every later stale section for review.
  Evidence: create/SKILL.md:136-145
  Status: kept
- FR-APC-16: Risks live in the attack plan (template section 5, check_draft requires it) or in the evidence page (SKILL.md Stage 6).
  Evidence: document-template.md:24, check_draft.py; create/SKILL.md:126
  Status: open, Q14
- FR-APC-17: `draft/alternatives.md` is called an appendix of the technical solution but no step publishes it.
  Evidence: state.md:13, create/SKILL.md:105, publishing.md
  Status: open, Q15
- FR-APC-18: Template section "6. Milestone specs ... filled in Stage 7". Stage 7 is Publish; no stage fills it. Execute expects a milestone spec.
  Evidence: document-template.md:25, create/SKILL.md:130, execute/SKILL.md:16,29
  Status: unclear, Q13
- FR-APC-19: `reviews/round-<n>-<lens>.md` listed in the work folder; no step writes it.
  Evidence: references/state.md:16
  Status: unclear, Q13
- FR-APC-20: `references/state.md` example says "Stage: 3 (technical solution)"; technical is Stage 4.
  Evidence: state.md:25,42
  Status: kept (doc fix)

## Attack plan milestone execute (APE)

- FR-APE-01: Inputs: the approved plan, the milestone's task detail, tracker tickets (ticket wins on conflict), optional additional notes asked once.
  Evidence: execute/SKILL.md:24-31, subagent-rules-template.md
  Status: kept. What "milestone spec" means: Q13.
- FR-APE-02: Grade input readiness before any code; five blocking gaps stop the run and point to attack-plan-create.
  Evidence: resources/input-readiness.md:5-23,35
  Status: kept. Reuse create's gates instead: Q21.
- FR-APE-03: Read-only audit of tickets against `origin/<default>` by 2-3 parallel subagents; each surprise is written into the document that owns it before coding.
  Evidence: execute/SKILL.md:44-56
  Status: kept. The rules template tells PR agents to read a "Surprises" section no step creates (subagent-rules-template.md:8): Q16.
- FR-APE-04: One fresh subagent per PR, stacked draft PRs opened in number order so GitHub lists them M1-1 first after reversal, title prefix `[<code> M<n>-<k>]`.
  Evidence: execute/SKILL.md:52-70
  Status: kept
- FR-APE-05: A per-milestone `subagent-rules.md` built from the template, holding git rules, human-only gates and local environment quirks.
  Evidence: resources/subagent-rules-template.md
  Status: kept
- FR-APE-06: After each push arm `feedback-watch` in `pr` mode on the stack, `--reviewer` for the review bot. Execute instructs; it does not call watch.py itself.
  Evidence: execute/SKILL.md:76
  Status: kept
- FR-APE-07: A stack behind the default branch goes red in unrelated jobs; merge the default branch into the stack bottom.
  Evidence: execute/SKILL.md:78
  Status: kept
- FR-APE-08: `build_integration_branch.py --target --heads [--from --default --message --push --repo --remote]` merges heads with `git merge-tree --write-tree` + `commit-tree`, no checkout, plain fast-forward push only with `--push`, stops on conflict, last line `INTEGRATION_BRANCH_EVENT {json}`. It skips no-op merges, tells a conflict from other git failures, checks git >= 2.38, and does not infer target absence from a failed fetch.
  Evidence: build_integration_branch.py:55-95,113-114. attack-plan B3, B4, B5 (confirmed at :76-85)
  Status: kept (fixes)
- FR-APE-09: Review pass: collect unresolved threads, decide FIX or REPLY, one subagent per PR with FIX rows from the stack bottom, merge up, then resolve FIX threads; REPLY threads stay open for the user.
  Evidence: resources/review-pass.md:7-45
  Status: kept, except resolving threads as the user: Q17.
- FR-APE-10: Never post as the user, never mark ready, never merge, never rebase or force-push.
  Evidence: execute/SKILL.md:86,125; subagent-rules-template.md:9-12
  Status: kept
- FR-APE-11: Notes in `.ai-notes/<project>-<milestone>/`: README with PR table, pending items by owner, next step, dated "State (start here)"; `subagent-rules.md`; `review-pass-<date>.md`. Resume from "State".
  Evidence: execute/SKILL.md:32,63,106
  Status: kept. Section not in ai-notes shape: Q11.
- FR-APE-12: Step 9.4 writes the milestone QA page by hand, without qa-session.
  Evidence: execute/SKILL.md:99. seams B3, S16
  Status: open, Q18
- FR-APE-13: The task block's "Context for an outside reviewer" becomes the PR description opening. Execute's briefs never pass it.
  Evidence: executable-plan.md:34 vs execute/SKILL.md, subagent-rules-template.md
  Status: open, Q19
- FR-APE-14: `gh stack` optional; fallback is each PR targeting the branch below.
  Evidence: execute/SKILL.md:19
  Status: kept

## Feedback watch (FW)

- FR-FW-01: `watch.py pr N... [--repo]` polls every `--interval` s (default 120, must be > 0) and prints one line per PR when (sha7, pending, failing, missing reviewers, unresolved) changes. The first round prints every PR, so a re-armed watcher loses nothing.
  Evidence: watch.py:84-99,161-182. feedback-watch F1, D4; I9 (no interval check)
  Status: kept
- FR-FW-02: Data per PR: head and check rollup, reviews with commit id, review threads. All pages are read (today first 100 reviews and threads only).
  Evidence: watch.py:26,149-158. feedback-watch A1, A2
  Status: kept (pagination fix)
- FR-FW-03: Checks: newest run per (workflow, name) wins; cancelled reruns are superseded; non-completed = pending; FAILURE, TIMED_OUT, STARTUP_FAILURE = failing; status contexts PENDING/EXPECTED pending, FAILURE/ERROR failing. A check whose only run is cancelled reads as green today.
  Evidence: watch.py:21-23,50-76 (confirmed: cancelled dropped before grouping, :54)
  Status: kept; sole-cancelled outcome Q24.
- FR-FW-04: An empty rollup counts as pending unless `--allow-no-checks`. A partly registered rollup can read done early.
  Evidence: watch.py:88. feedback-watch B6
  Status: kept; partial-registration rule Q25.
- FR-FW-05: `--reviewer` (repeatable): a review on the head commit counts; login compare case-insensitive, `[bot]` stripped.
  Evidence: watch.py:79-97
  Status: kept; review state Q26.
- FR-FW-06: Stop rules: all PRs fetched and done -> `ALL DONE` (or `CI DONE` with `--until ci`), exit 0; `--once` not done -> `NOT DONE`, exit 1; `--timeout` minutes -> `TIMEOUT`, exit 3.
  Evidence: watch.py:173-181
  Status: kept
- FR-FW-07: A failed gh call skips that PR for the round. Repeated failures print a stdout line and end the watcher with a non-zero exit, since Monitor reads stdout only.
  Evidence: watch.py:166-169 (stderr only today). feedback-watch B3
  Status: kept (fix)
- FR-FW-08: A merged or closed PR.
  Evidence: watch.py:151 fetches no `state`. feedback-watch B1
  Status: open, Q23
- FR-FW-09: `watch.py local --cmd ... [--path] [--interval 2] [--debounce 1] [--once]`: run commands; print `PASS` or `FAIL (exit N)` plus the last 15 ANSI-stripped lines when pass/fail flips and on the first run.
  Evidence: watch.py:185-215,255-273
  Status: kept; FAIL-output change, `--timeout`, command timeout Q27.
- FR-FW-10: Change detection polls (mtime_ns, size) and skips build and cache dirs, `.ai-notes`, and the skills' own state dirs (`.attack-plan`, `.rearch`).
  Evidence: watch.py:16-20,218-252. seams B4
  Status: kept (add the two dirs)
- FR-FW-11: `local --once` prints `ALL PASS` (exit 0) or `FAILED: <labels>` (exit 1).
  Evidence: watch.py:256-263
  Status: kept
- FR-FW-12: Read-only toward GitHub and the repo.
  Evidence: watch.py:146-156
  Status: kept
- FR-FW-13: Host integration: Claude Code runs it under the Monitor tool with `timeout_ms` 1800000; opencode runs a background shell job logging to `/tmp/feedback-watch-*.log`.
  Evidence: feedback-watch/SKILL.md:55-63
  Status: kept (Claude); opencode path experimental. Facts: Q30d, Q30e.
- FR-FW-14: SKILL.md holds CI failure-reading advice (job logs mid-run, "runner lost communication", stacked CI).
  Evidence: feedback-watch/SKILL.md:74-81
  Status: open, Q28
- FR-FW-15: SKILL.md states exactly what the code does: first-run print, local runs until killed, which conclusions count as fine.
  Evidence: feedback-watch D2, D3, D6
  Status: kept (doc fix)

## QA session (QA)

- FR-QA-01: Three modes (Create, Rework, Live edit) chosen from state; never rebuild a page holding ticks or findings without asking.
  Evidence: qa-session/SKILL.md:26-34
  Status: kept
- FR-QA-02: Inputs: spec, code at a commit, seed, environment; optional publishing target; one question at a time.
  Evidence: qa-session/SKILL.md:14-24
  Status: kept
- FR-QA-03: Session folder `.ai-notes/qa-<slug>/`: README.md, sources.md, decisions.md, rework-log.md, previous.md. The page holds no history.
  Evidence: qa-session/SKILL.md:36-45,61
  Status: kept. `previous.md` sits where subagents are told to read: Q11.
- FR-QA-04: Create: sources, Builder subagent, check_page, Verifier subagent, show shape, publish after go-ahead.
  Evidence: qa-session/SKILL.md:47-56
  Status: kept
- FR-QA-05: Rework: a fresh Builder re-derives without the previous page; ticks and findings carry over by scenario title and check text; change report in rework-log.md.
  Evidence: qa-session/SKILL.md:58-66, briefs.md:69-71
  Status: kept
- FR-QA-06: Live edit: targeted edits, keep ticks, untick on meaning change, run check_page after.
  Evidence: qa-session/SKILL.md:68-73
  Status: kept
- FR-QA-07: Page shape, simplified by user decision 2026-11-25 (Q33). Three parts only:
  1. Setup for the lead developer, collapsed (a toggle or `<details>` block): seed, environment, users, values to check before the session.
  2. Scenarios, numbered, simple and easy to follow. Each scenario carries all the context its driver needs: persona, where to start, steps, expected results.
  3. Findings: an empty section with no table, filled during the session.
  Known limits, Product questions and After the session are dropped from the page.
  Evidence: references/page-template.md:5-77 (current shape); user decision 2026-11-25.
  Status: kept, reshaped. The skill needs more work later; this run only simplifies it.
- FR-QA-08: Exact-label rule: every on-screen word is the label that scenario's persona sees, in their UI language, traced to code; no paraphrase. The template and setup checklist state it too.
  Evidence: qa-session/SKILL.md:86, briefs.md:29,58; absent from page-template.md. qa D1
  Status: kept (add to template). Enforcement: Q31. Prose language: Q32.
- FR-QA-09: `check_page.py <page> [-v]`: emoji, internal ids, placeholders, TODO/TBD/FIXME/XXX, bare "today"/"now" (WARN), "(cont.)" (WARN), check before "As" line, scenario numbering, scenario without checks (WARN), Findings section present and empty (FAIL otherwise). Known limits and Product questions checks are removed with those sections (FR-QA-07). Summary line, exit 1 on FAIL. Fence-aware; `[...]` template placeholders caught; malformed `### 1 Title` flagged.
  Evidence: check_page.py:11-20,48-87,110. qa B2, B3, B4, D3, D6 (B1, B2 reproduced)
  Status: kept (fixes). Exemption for exact labels such as "Q4 Budget": Q31.
- FR-QA-10: Publishing: Markdown `docs/qa/<slug>/session.md` default, or an MCP document tool found by tool search; fetch before update; read back and compare counts; commit only where the team commits such docs; tool quirks go to `sources.md`.
  Evidence: references/publishing.md:5-25
  Status: kept. Shared publishing layer with attack-plan: Q29.
- FR-QA-11: Setup checklist: idempotent seed, one labeled line per check, "found N of N", values printed before the session, no passwords on the page.
  Evidence: references/setup-checklist.md:5-45
  Status: kept
- FR-QA-12: Builder and Verifier run as general-purpose subagents on the strongest tier with the brief as the whole prompt. Briefs give resolvable paths for `<skill>` and the references.
  Evidence: qa-session/SKILL.md:93, briefs.md:3,10-11,36. qa D9, D10
  Status: kept (path fix)
- FR-QA-13: Without subagents, run the briefs yourself in separate passes and note it in README.
  Evidence: qa-session/SKILL.md:94
  Status: experimental
- FR-QA-14: Stop/resume handoff text.
  Evidence: qa-session/SKILL.md:96-103
  Status: kept
- FR-QA-15: At Create the Findings section is empty and has no table. A non-empty Findings section at Create is a FAIL.
  Evidence: qa-session/SKILL.md:87; check_page.py:60-61 only counts. User decision 2026-11-25 (Q33, Q34).
  Status: kept

## Rearchitect (RA)

- FR-RA-01: Resume from `.rearch/STATE.md`; no `.rearch/` means Stage 0. Announce a 3-8 line plan before each stage or phase and any off-plan action.
  Evidence: rearchitect/SKILL.md:12-16
  Status: kept
- FR-RA-02: Model routing: auditor fast, architect strong, phase default.
  Evidence: rearchitect/SKILL.md:20-25
  Status: kept
- FR-RA-03: Stage 0: clean tree (ignoring caches the baseline creates), branch `rearch/<date>`, annotated tag `rearch-base`, baseline.md with commands and M1..Mn, STATE.md, commit `rearch: setup`. Exact git commands given; existing branch or tag handled.
  Evidence: rearchitect/SKILL.md:28-34. rearchitect X1 (tag.gpgSign observed), B2, B8, B9
  Status: kept (fixes)
- FR-RA-04: Stage 1: inventory of every file with kind, lines, aspects; about 8,000 lines per aspect; user gate; commit.
  Evidence: rearchitect/SKILL.md:36-43
  Status: kept
- FR-RA-05: Stage 2: parallel auditors, coverage check against inventory without reading full reports, then a seams auditor, commit `rearch: audits`. STATE records per-aspect completion.
  Evidence: rearchitect/SKILL.md:45-51. rearchitect B6, A4, B10
  Status: kept (progress fix)
- FR-RA-06: Stage 3: architect writes requirements, verifies high-severity bugs, decision-driving facts and dead/experimental claims, lists refuted findings; user gate; commit.
  Evidence: rearchitect/SKILL.md:53-57, agents/rearch-architect.md:16-27. state.md lacks the refuted section (D3)
  Status: kept
- FR-RA-07: Stage 4: architecture.md, docs-plan.md, phases.md; topic docs first, test harness second; user gate.
  Evidence: rearchitect/SKILL.md:59-69
  Status: kept
- FR-RA-08: Stage 5: one fresh `rearch-phase` per phase; it leaves changes uncommitted, never edits STATE, logs deviations; the orchestrator runs manual checks and commits with FR IDs and never reads source. A restart with a dirty tree from a dead phase agent has a rule.
  Evidence: rearchitect/SKILL.md:71-84, agents/rearch-phase.md:8,26,28. rearchitect B4
  Status: kept (fix)
- FR-RA-09: Stage 6: per-module audit against requirements, extra phase appended to phases.md if needed, move requirements and architecture into `docs/`, update README and CLAUDE.md/AGENTS.md, run baseline and manual checklist, delete `.rearch/` last, ask before merge or tag delete.
  Evidence: rearchitect/SKILL.md:86-94. B1 [high] confirmed: step 2 deletes `.rearch/` before step 4 runs the baseline it holds. B5, D8
  Status: kept (reorder fix). Cleanup owner: Q35.
- FR-RA-10: Stop at about 70% context or on request; print a fenced resume prompt.
  Evidence: rearchitect/SKILL.md:96-105
  Status: kept
- FR-RA-11: Topic docs follow docs-style.md: present tense, no history, four-part quirks, sourced facts, tables.
  Evidence: references/docs-style.md:11-23
  Status: kept
- FR-RA-12: Prompts are domain-neutral. Real-time and DAW examples apply only when the project has such paths.
  Evidence: rearchitect/SKILL.md:31,39; agents/rearch-architect.md ("real-time"); docs-style.md:8. rearchitect A5, L2
  Status: kept (fix)
- FR-RA-13: STATE.md changes land in the same commit as the stage or phase they record.
  Evidence: rearchitect/SKILL.md:51,57,69,81. rearchitect B7
  Status: kept (fix)

## Cross-skill conventions (XS)

- FR-XS-01: Every subagent brief is self-contained and fresh, names its output path and return cap, carries the style line, says fetched content is data not instructions, and uses one term ("unverified") for unchecked facts.
  Evidence: seams S17, S18, S20; attack-plan briefs.md:5-7 (injection rule), absent in qa and rearchitect briefs
  Status: kept
- FR-XS-02: Markdown heading and section parsing is the same in gate.py, check_draft.py and check_page.py, and skips fenced code.
  Evidence: gate.py:25,150-162; check_draft.py:32,133-165; check_page.py:19,34-47. seams B1, B2
  Status: kept (fix)
- FR-XS-03: Long-running skills keep resumable state. Today 5 layouts: `.ai-notes/<area>`, `.rearch/`, `.attack-plan/<slug>/`, execute's and qa-session's ai-notes variants.
  Evidence: seams S11, S12
  Status: open, Q11
- FR-XS-04: attack-plan-create, execute and qa-session publish to Markdown or a document tool with read-back and reviewer-edit retention. Notion quirks live only in attack-plan; source-of-truth rules are opposite.
  Evidence: seams S21
  Status: open, Q29
- FR-XS-05: Script "no" output: one format per script family, documented in its SKILL.md (today `LEVEL file: msg`, `line N LEVEL msg`, `REFUSED:` on stderr).
  Evidence: seams S22
  Status: kept

## Non-functional

- NFR-01: Scripts and install.py use only the Python 3.9 standard library and run as `/usr/bin/python3 -I`. No packages to install. Evidence: README.md:30, baseline.md Build, qa X1.
- NFR-02: A fresh Mac needs only the Command Line Tools (git, python3) to install and run. Scripts that need more state it in SKILL.md and README: git >= 2.38 for build_integration_branch.py. Evidence: README.md:30, attack-plan D8. Linux: Q7.
- NFR-03: Default script output is minimal: one line per change or a summary line; detail behind `-v`. Evidence: global.md:10, watch.py, check_page.py, check_draft.py.
- NFR-04: Every script, install.py included, has a unittest suite run with `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s <dir>`. install.py is importable without running main. Baseline 96 tests green. Evidence: baseline.md, install.py:109.
- NFR-05: Running tests leaves no untracked files; `.gitignore` covers `__pycache__/`. Evidence: git status (5 untracked caches), install B9.
- NFR-06: Install is idempotent and `--check` is read-only. Evidence: install.py:68-83.
- NFR-07: Skill edits take effect through symlinks at once; agent and global.md edits need `install.py`. README says so, including new skill dirs. Evidence: README.md:34, install D8, seams S6.
- NFR-08: Everything installed works in Claude Code and opencode (M1, M2). Evidence: README.md:3.
- NFR-09: Prompt size is a per-session and per-subagent cost. One fact in one place across SKILL.md, references, briefs and agent bodies. No requirement adds duplicated prose. Evidence: seams S8, S17; notes-and-writing I5; attack-plan I1, I2.
- NFR-10: Orchestrator context: long skills stop near 70% with a resume prompt; subagent reports are word-capped; orchestrators read summaries, not full reports. Evidence: rearchitect/SKILL.md:48,98; create/SKILL.md.
- NFR-11: Watcher load: PR mode default 120 s, at most 3 gh calls per PR per round; local mode 2 s poll, 1 s debounce. Evidence: watch.py:284, SKILL.md.
- NFR-12: Only build_integration_branch.py with `--push` writes to a remote. All other scripts are read-only toward GitHub. Evidence: watch.py:146-156, build_integration_branch.py:88-93.
- NFR-13: Two layers at most: the orchestrator session spawns subagents, and subagents never spawn subagents. Every skill and agent body says so where it delegates. Evidence: user decision 2026-11-25 (Q30f); rearchitect SKILL.md Stage 6 already relies on it.

## Constraints from external systems

- CON-CC-01: Claude Code agent frontmatter: `name`, `description`, `model` (sonnet, opus, inherit), `tools` as a restriction list. Source: install.py:26-27, installed agents load. Vendor doc unverified.
- CON-CC-02: Claude Code Monitor turns stdout lines into notifications; max `timeout_ms` 1800000. Source: feedback-watch/SKILL.md:58-61, unverified (Q30d).
- CON-CC-03: Subagents cannot spawn subagents in Claude Code. Source: rearchitect/SKILL.md:88, no agent lists an Agent tool. opencode unverified (Q30f).
- CON-OC-01: opencode agent frontmatter: `description`, `mode`, `model` as `provider/model`; name from file name; no `tools` key used. Source: install.py:30-35, unverified vs vendor doc.
- CON-OC-02: opencode has no Monitor tool; background shell job plus log file instead. Source: feedback-watch/SKILL.md:63, unverified (Q30e).
- CON-GH-01: Check rollup mixes CheckRun (`status`, `conclusion`, `name`) and StatusContext (`state`, `context`). Source: watch.py:42-47, tests.
- CON-GH-02: Reruns leave old runs in the rollup; newest by `startedAt`/`createdAt` wins. A queued rerun may carry an empty start stamp (unverified, feedback-watch X12). Source: watch.py:50-60.
- CON-GH-03: Checks appear seconds after a push; an empty rollup is not done. Source: watch.py:88, test.
- CON-GH-04: Bot logins differ: REST `claude[bot]`, GraphQL `claude`. Source: watch.py:79-81, tests.
- CON-GH-05: GitHub lists PRs newest first; open a milestone's PRs in number order. Source: execute/SKILL.md:54.
- CON-GH-06: A stack behind the default branch runs current default-branch workflows against old files and goes red together. Source: execute/SKILL.md:78, capture; mechanism wording imprecise (feedback-watch X9).
- CON-GIT-01: `git merge-tree --write-tree` needs git 2.38+. Source: build_integration_branch.py:11.
- CON-GIT-02: `commit-tree` needs a configured identity. Source: build_integration_branch.py:82.
- CON-GIT-03: `tag.gpgSign=true` makes `git tag <name>` fail without a message; use `git tag -a -m`. Source: observed in this run.
- CON-GIT-04: `git fetch <remote> <branch>` updates `<remote>/<branch>` only when the fetch refspec covers it. Source: git docs; untested in a single-branch clone.
- CON-GIT-05: `.git/info/exclude` lives in the common git dir and covers every worktree. Source: git docs.
- CON-NOTION-01: Notion MCP quirks (pipe-row tables, `+ ` cells as bullets, stray backtick collapses the page, `<mention>` match failures, dropped `discussion-urls` spans, no regex lookbehind, session expiry, top `>` quote swallows the page). Source: create/references/publishing.md:13-37, earlier projects, unverified now (Q30g).

## Known defects (confirmed at rearch-base)

Each is fixed under the FR named. Line numbers here are verified; some audit citations are not (see Refuted).

- gate.py:42-43,93: `open` refuses a reopened gate (FR-APC-06).
- gate.py:150-162: section hash stops at a `#` line inside a code fence (FR-APC-05, FR-XS-02).
- gate.py:181: `--rounds abc` raises an uncaught ValueError (FR-APC-08).
- build_integration_branch.py:76-85: no-op merges create empty two-parent commits; any merge-tree failure is reported as a conflict (FR-APE-08).
- watch.py:54: a sole cancelled check reads green (FR-FW-03, Q24).
- watch.py:151: merged or closed PRs poll forever (FR-FW-08).
- watch.py:166-169: persistent gh failure is silent on stdout (FR-FW-07).
- watch.py:209 area (report_results): FAIL to FAIL with new output prints nothing (FR-FW-09).
- check_page.py:12: "Q4 Budget" fails as an internal id (reproduced) (FR-QA-09, Q31).
- check_page.py:13: `[Next fact.]` placeholder passes (reproduced) (FR-QA-09).
- install.py:26,32: unquoted descriptions with `: ` (FR-INST-11).
- install.py:41-51: no pruning (FR-INST-09).
- install.py:71,102: write through a symlinked destination (FR-INST-12).
- rearchitect/SKILL.md:91 vs :93: `.rearch/` deleted before the baseline run [high] (FR-RA-09).

## Refuted audit findings

- seams L1: "README lists 6 skills". README.md:15-21 has 7 rows, one per skills/ dir. Refuted (install-and-config D9 is right).
- attack-plan audit citations for gate.py (`:195`, `:220`, `:250-254`, `:258-276`, `:296-322`, `:328-340`, `:359`, `:374-376`) exceed the 203-line file. Behaviors B1, B2, B6, F4-F7 are confirmed at gate.py:42-43, 93-98, 118-121, 132-162, 181, 196. Citations refuted, findings stand. Seams caught this first.
- attack-plan citations create/SKILL.md `:176`, `:181`, `:192`, `:201`, `:205-222` exceed the 164-line file. D1 (Stage 7 is Publish, SKILL.md:130) and D14 (risks in evidence page, SKILL.md:126) are confirmed at the real lines.
- attack-plan D7 cites review-pass.md:209; the file has 45 lines. The thread-resolve mutation is at review-pass.md:43. Finding stands.
- attack-plan D3 says execute "creates the Surprises section itself in Step 3.3/4.6". execute/SKILL.md:46,56 writes surprises into the owning documents (spec, plan, tickets); no step creates a "Surprises" section. The gap is larger than stated: the section the rules template names (subagent-rules-template.md:8) has no producer at all.
- install-and-config B2 title "broken symlink detection" does not match its content; dangling links are handled (install.py:77,99). The real defect is rmtree under `--yes` (install.py:97-98), kept as FR-INST-13.
- feedback-watch Q6 (does execute call watch.py?) is answered: execute/SKILL.md:76 only instructs arming the skill.

## Dropped

None yet.

## Open questions

Answer each with the choice in brackets.

- Q1: Should install.py remove agents and skill links whose source was deleted or renamed, limited to items that point into this repo? [yes / no]
- Q2: opencode ignores `tools`, so read-only agents can edit there. [map `tools` to opencode permissions / document as prose-only]
- Q3: Are the opencode ids `deepseek/deepseek-flash` and `deepseek/deepseek-v4-pro` exact? Unverified. [confirm / give ids]
  Answer (2026-11-25): no model ids or names anywhere in the repo, not even as defaults. models.json is deleted, and install writes no model lines. The orchestrator resolves tiers to the current tool's available models when a run starts (FR-AGT-02, -07, -08).
- Q4: Do Claude Code and opencode load the 3 agents whose description holds `: ` today? Unverified, M1/M2 show it. [confirm / unverified]
- Q5: `~/.claude/CLAUDE.md` and opencode `AGENTS.md` are overwritten by global.md. [keep full overwrite / support a local include file]
- Q6: Under `--yes`, an existing real skill folder is deleted with no backup. [keep / move to a backup path / refuse and ask]
- Q7: Platform. [macOS only (`/usr/bin/python3`) / also Linux]
  Answer (2026-11-25): macOS only.
- Q8: Clean up global.md: merge the duplicate delegation (lines 8, 13, 17) and test-output (9, 16) rules, and drop "Claude" from line 16 so it reads right in opencode. [yes / no]
- Q9: global.md names `frontend-design` and REA, which the harness does not ship. [keep as examples / drop / ship them in skills/]
- Q10: ai-notes trigger. Its description fires on any multi-step task, its body only on work spanning sessions, subagents or PRs. [body rule wins / description wins]
- Q11: State layouts. [one shared convention: resume file, "Next" line, exclude rule, for `.ai-notes`, `.rearch`, `.attack-plan` / keep separate layouts but add "State (start here)" to the ai-notes README shape and keep qa `previous.md` outside the notes area]
- Q12: writing-craft scope. [human-read text only, with agent-to-agent text exempt and named / all text]. Also: attack-plan-create and execute cite it explicitly [yes / no]; neutralise QA examples and fold section 7 [yes / no].
- Q13: Milestone specs. The template's "6. Milestone specs" has no producer, execute expects a "milestone spec", and `reviews/` is never written. [drop both; execute reads the milestone's task blocks in technical-solution.md / have create fill Milestone specs in Stage 5]
- Q14: Where do risks live? [attack plan section 5 / evidence page]
- Q15: `alternatives.md`. [publish as appendix of the technical solution / keep internal and drop the "appendix" wording]
- Q16: The PR rules template names a plan "Surprises" section that nobody writes. [create's template defines it / execute writes it in Step 3 / drop the reference]
- Q17: May the execute orchestrator resolve FIX review threads through GraphQL as the user? [allowed / forbidden, user resolves]
  Answer (2026-11-25): allowed only for threads started by a bot account (review bots, CI bots). Threads started by a human stay open for the user to resolve. Exit goal of execute: every PR in every stack has green CI and every bot review thread is addressed and resolved.
- Q18: Execute Step 9.4 QA page. [delegate to qa-session / keep the hand-written page]
- Q19: Task block "Context for an outside reviewer" as the PR description opening. [execute passes it to PR subagents / drop the claim]
- Q20: Give task blocks a fixed heading schema checked by script, shared by create Stage 5 and execute input readiness? [yes / no]
- Q21: Execute gates its input on create's `gate.py status` when gates.json exists, else grades by hand? [yes / no, stay format-agnostic]
- Q22: Let a gate hash several (file, heading) pairs, so `tasks-m<n>` covers both technical-solution.md and the attack-plan table? [yes / no]
- Q23: Watcher on a merged or closed PR. [print a line and stop watching it / keep current]
- Q24: A check whose only run was cancelled. [failing / pending / done]
- Q25: Early `ALL DONE` when only some checks have registered. [require 2 identical polls / accept]
- Q26: A dismissed or changes-requested review on the head commit. [counts as reviewed / does not]
- Q27: Local mode: print when FAIL output changes [yes / no]; add `--timeout` and a per-command timeout [yes / no].
- Q28: CI failure-reading advice in feedback-watch SKILL.md (job logs, runner lost, stacked CI). [keep there / move to execute]
- Q29: One publishing reference shared by attack-plan-create, execute and qa-session (Notion quirks, read-back, commit policy)? [yes / no]
- Q30: Unverified external facts. Confirm each or it stays marked `unverified` and is checked in M1/M2/M4. [confirm / unverified]
  Answer (2026-11-25): the user knows none of them. All stay `unverified` and are checked in M2 (opencode) and M4 (feedback-watch); Notion quirks are checked in M5/M7. c is replaced by Q37, f is moot (NFR-13).
  c. opencode with no `model` line inherits the session model.
  d. Monitor `timeout_ms` max is 1800000.
  e. opencode has no Monitor tool; the background-job path works.
  f. opencode subagents cannot spawn subagents.
     Answer (2026-11-25): moot. No skill nests more than two layers (NFR-13), so the fact stays unverified and nothing depends on it.
  g. The Notion MCP quirks in create/references/publishing.md still hold.
- Q31: Exact UI labels that trip check_page (Q4, S3, Today). [exempt inside backticks / inside quotes / inside bold / no exemption]. Also: script checks labels against a Builder-written labels file [yes / no, Verifier only].
- Q32: Page prose is US English and labels follow the UI language? [yes / other]
- Q33: Is "After the session" a required page section checked by script? [yes / no]
  Answer (2026-11-25): no. The page is collapsed setup for the lead developer, then scenarios, then an empty Findings section with no table (FR-QA-07).
- Q34: A non-empty Findings table at Create. [FAIL / WARN / nothing]
  Answer (2026-11-25): Findings has no table and starts empty; non-empty at Create is a FAIL (FR-QA-15).
- Q35: Who owns final cleanup in rearchitect? [architect's last phase / Stage 6 only]
- Q36: `.rearch/` lifecycle. [commit on the branch and delete in Stage 6, as now / keep in repo after / gitignore]
- Q37 (architecture, not for the user): how does each tool apply the confirmed per-run model to a spawn, and how does the orchestrator list available models? Claude Code: the Agent tool's `model` parameter (documented). opencode: unverified; candidates are a model argument on the task tool, or project-local agent files written at run start under the run's state folder. Settle it with one scripted check against opencode's docs and `opencode models`, and keep the code in one place. Also replaces Q30c (opencode `null` = inherit).

## Answers accepted at the Stage 3 gate (2026-11-25)

The user accepted the orchestrator's recommendation for every question not answered above. These answers override the Status lines that point at the questions.

- Q1: yes, prune installed agents and skill links that point into this repo and whose source is gone.
- Q2: map `tools` to opencode permissions.
- Q4: moot, install.py quotes descriptions (FR-INST-11).
- Q5: keep the full overwrite of CLAUDE.md and AGENTS.md.
- Q6: under `--yes`, move a real skill folder to a backup path, never delete it.
- Q8: yes, merge the duplicate rules in global.md and drop "Claude".
- Q9: keep `frontend-design` and REA as examples marked "when available".
- Q10: the ai-notes body rule wins (work spanning sessions, subagents or PRs).
- Q11: a shared minimum (one resume file with a "Next" line, one private-exclude rule); layouts stay per skill.
- Q12: writing-craft covers human-read text only, with agent-to-agent briefs named as exempt; both attack-plan skills cite it; examples made neutral; section 7 folded in.
- Q13: drop Milestone specs and `reviews/`; execute reads the milestone's task blocks in technical-solution.md. FR-APC-18 and FR-APC-19 dropped.
- Q14: risks live in attack plan section 5.
- Q15: `alternatives.md` stays internal; drop the "appendix" wording.
- Q16: drop the "Surprises" reference.
- Q18: execute Step 9 QA page delegates to qa-session.
- Q19: execute passes "Context for an outside reviewer" to PR subagents as the PR description opening.
- Q20: yes, a fixed task-block heading schema checked by script, shared by create Stage 5 and execute input readiness.
- Q21: yes, execute gates its input on create's `gate.py status` when gates.json exists, else grades by hand.
- Q22: yes, one gate may hash several (file, heading) pairs.
- Q23: merged or closed PR: print one line and stop watching it.
- Q24: a check whose only run was cancelled counts as failing, labeled "cancelled".
- Q25: require 2 identical polls before ALL DONE.
- Q26: a changes-requested review on the head commit counts as reviewed; a dismissed one does not.
- Q27: local mode prints when FAIL output changes; add `--timeout` and a per-command timeout.
- Q28: keep the CI failure advice in feedback-watch.
- Q29: yes, one publishing reference shared by attack-plan-create, execute and qa-session.
- Q31: exact UI labels inside backticks are exempt from check_page id and word checks; no labels file, the Verifier checks labels.
- Q32: page prose is US English; labels follow the UI language.
- Q35: Stage 6 alone owns the final cleanup; the architect's plan ends with the last code phase.
- Q36: `.rearch/` is committed on the branch; Stage 6 runs the baseline and manual checklist first, then deletes it (fixes rearchitect B1).
- Experimental FR-AGT-05, FR-QA-13, FR-FW-13: kept.
