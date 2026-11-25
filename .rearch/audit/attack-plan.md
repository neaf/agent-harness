# Audit: attack-plan

Tests at audit time: attack-plan-create 33 OK, attack-plan-milestone-execute 6 OK (git 2.56).

## Coverage
| File | Lines | Read fully |
|---|---|---|
| README.md | 34 | yes |
| agents/attack-plan-critic.md | 25 | yes |
| agents/attack-plan-designer.md | 25 | yes |
| agents/attack-plan-reader.md | 25 | yes |
| skills/attack-plan-create/SKILL.md | 164 | yes |
| create/references/briefs.md | 71 | yes |
| create/references/document-template.md | 53 | yes |
| create/references/executable-plan.md | 48 | yes |
| create/references/publishing.md | 40 | yes |
| create/references/questions.md | 58 | yes |
| create/references/state.md | 60 | yes |
| create/scripts/check_draft.py | 178 | yes |
| create/scripts/gate.py | 203 | yes |
| create/tests/test_check_draft.py | 122 | yes |
| create/tests/test_gate.py | 123 | yes |
| skills/attack-plan-milestone-execute/SKILL.md | 128 | yes |
| execute/resources/input-readiness.md | 38 | yes |
| execute/resources/review-pass.md | 45 | yes |
| execute/resources/subagent-rules-template.md | 46 | yes |
| execute/scripts/build_integration_branch.py | 145 | yes |
| execute/tests/test_build_integration_branch.py | 105 | yes |
| Total | 1736 | |

## Functional behavior
- F1: Work folder `.attack-plan/<slug>/` holds STATE.md, gates.json, ledger.md, sources/, draft/, audit/, reviews/; committed by default. Evidence: create/SKILL.md:93, references/state.md:3-17. Status: active (reviews/ unused, see L2).
- F2: The plan is written one section at a time through a 7-step loop: open, draft, challenge, grill, record, review, approve or skip. Evidence: create/SKILL.md:107-117. Status: active.
- F3: Author may speed up, skip reviews or draft ahead without warning; skipped sections are recorded "not reviewed". Evidence: create/SKILL.md:87,119; gate.py:258-264. Status: active.
- F4: 8 stages (intake, sources, product, product-review, technical, milestones, audit, publish) gate opening: a section cannot open while any gate of the same or an earlier stage is not approved or not reviewed. Evidence: gate.py:195,296-299. Status: active.
- F5: Approval stores a SHA-256 of the section text (file + heading); `verify` and `status` flag later edits. Evidence: gate.py:250-254,310-322. Status: active. Only for gates opened with --file.
- F6: `reopen` turns every later approved gate (by list order) stale. Evidence: gate.py:266-276. Status: active.
- F7: `verify` also flags technical drafts written before the technical stage opened. Evidence: gate.py:290-292. Status: active.
- F8: Three subagents: reader (fast), critic (strong), designer (strong); briefs in references/briefs.md. Evidence: agents/*.md, briefs.md. Status: active.
- F9: check_draft.py: required sections, order (Open questions between Product and Technical), question format Q<n>/Context/Question/Recommendation, no effort estimates, no estimate column, no Option A-D, no decision log, balanced backticks, code-term warnings in product part, `--product` stage rejects early technical content. Evidence: check_draft.py:10-127. Status: active.
- F10: Stage 1 readers pin the SHA on `origin/<default>`; all code reads at the SHA, never the working tree. Evidence: SKILL.md:146, agents/*.md, briefs.md:7. Status: active.
- F11: Publishing to repo Markdown (default) or Notion; reviewers' edits kept; Stage 8 refresh. Evidence: publishing.md, SKILL.md:205-218. Status: active.
- F12: Task block spec per PR (title `[<code> M<n>-<k>] ...`, base, files, rule everywhere, invariants+tests, edge cases, ordering, reviewers, context, rationale, QA, depends on, ticket). Evidence: executable-plan.md:22-38. Status: active (consumed by milestone-execute only by prose).
- F13: milestone-execute: Steps 1-11, one fresh subagent per PR, stacked draft PRs, state in `.ai-notes/<project>-<milestone>/`. Evidence: execute/SKILL.md:24-121. Status: active.
- F14: Input-readiness grading with 5 blocking gaps before any code. Evidence: input-readiness.md:5-23. Status: active.
- F15: build_integration_branch.py merges heads with `git merge-tree --write-tree` + `commit-tree`, no checkout, plain push, stops on conflict, final line `INTEGRATION_BRANCH_EVENT {json}`. Evidence: build_integration_branch.py:76-95,113-114. Status: active (QA branch, Step 9; PR-branch sync, Step 7.3).
- F16: Review pass: collect unresolved threads, decide FIX or REPLY, subagent per PR from stack bottom, merge up, resolve FIX threads. Evidence: review-pass.md. Status: active.
- F17: Orchestrator never posts as the user, never marks ready, never merges, never rebases or force-pushes. Evidence: execute/SKILL.md:86,125; subagent-rules-template.md:9-12. Status: active.
- F18: README documents both skills and their test commands. Evidence: README.md:17-18. Status: active, true (test commands run green).

## External facts and quirks
- X1: `git merge-tree --write-tree` needs git 2.38+. Symptom: older git fails with an unknown-option error, reported as "CONFLICT merging <head>". Code: build_integration_branch.py:11,78-80. Source: code.
- X2: Notion MCP quirks: simple tables come back as pipe rows, `+ ` cell starts render as bullets, one stray backtick collapses the page, `old_str` with `<mention>` fails to match, replacing text drops `discussion-urls` spans, gateway firewall blocks regex lookbehinds, sessions expire. Source: capture (prior projects), unverified now. Location: publishing.md:15-36.
- X3: A `>` quote at the top of a Notion page can swallow it; use `<callout>`. publishing.md:21. Source: unverified.
- X4: GitHub lists PRs newest first; PRs must be opened in number order so a milestone reads M1-9..M1-1. Location: execute/SKILL.md:54, executable-plan.md:26. Source: vendor behavior.
- X5: When a stack is behind the default branch, CI runs the default branch's workflows on old branch files, so the whole stack goes red in unrelated jobs; fix by merging the default branch at the stack bottom. execute/SKILL.md:78. Source: capture.
- X6: Local DB may be laxer than CI; stale generated files after a branch switch cause false failures; linter autofix changes files on disk. subagent-rules-template.md:24-27. Source: capture.
- X7: `git fetch <remote> <branch>` updates `<remote>/<branch>` only when the remote's fetch refspec covers it (default clone). Script relies on this. Code: build_integration_branch.py:55,77. Source: git docs, untested in a single-branch clone.
- X8: `gh stack` extension is optional; fallback is "each PR targets the branch below". execute/SKILL.md:19. Source: code.
- X9: `commit-tree` needs a configured git identity. Code: build_integration_branch.py:82. Source: git behavior.

## Doc and code inconsistencies
- D1: document-template.md:25 says "6. Milestone specs ... filled in Stage 7. Empty until then." Stage 7 is Publish (SKILL.md:205); no stage fills Milestone specs. Task detail goes to technical-solution.md (SKILL.md:192). Stale.
- D2: state.md:25 example says "Stage: 3 (technical solution)"; SKILL.md:176 makes technical Stage 4, Stage 3 is ready-for-review. Same example's Next line says "Stage 4" (state.md:42). Self-contradictory.
- D3: execute/subagent-rules-template.md:19 tells the subagent to read the plan's "Surprises" section. create's template and executable-plan define no "Surprises" section; execute creates it itself in Step 3.3/4.6 (SKILL.md:46,56). Contract is only implicit.
- D4: execute/SKILL.md:16,29 expects a "milestone spec" and an "attack plan's milestone specs section". create produces per-milestone task detail in technical-solution.md and an always-empty "Milestone specs" section (D1). Execute's "spec" has no producer.
- D5: executable-plan.md:34 says "Context for an outside reviewer ... becomes the opening of the PR description". execute's brief and rules template (SKILL.md:69, template:44-47) never pass it on; the PR body comes from the repo template only.
- D6: SKILL.md:123 says after `reopen` "run the loop again", step 1 of the loop is `gate.py open`. gate.py:220 refuses `open` on a `drafting` gate ("is drafting: reopen it first"), and reopen leaves status `drafting` (gate.py:271). The loop cannot start at step 1 after a reopen.
- D7: execute/SKILL.md:125 "never post ... as the user"; review-pass.md:209 has the orchestrator resolve review threads via GraphQL as the user. Not listed as allowed or forbidden.
- D8: README.md:11 and the whole README say only `git` and python needed; the integration script needs git 2.38+ (script docstring only, not in SKILL.md).
- D9: state.md:16 lists `reviews/round-<n>-<lens>.md`; no brief or SKILL step writes it. Breaker brief returns text (briefs.md:37).
- D10: Plan walker, Scope auditor and Outside reviewer briefs name no output path (briefs.md:55,59,67), but the reader agent says "write one report at the path the brief names" (agents/attack-plan-reader.md:58). Claim auditor and Reader briefs do name paths. Scope auditor has no return length.
- D11: SKILL.md:165-169 Stage 3 step 2 calls `check_draft.py <work folder>/draft --product`. Template page order has Open questions "2." after Product solution; check enforces it. Consistent. But document-template.md:19 lists sections 0-7 including "Assumptions to verify" (7) and "Milestone specs" (6); check_draft requires only 6 section names and ignores these.
- D12: Reader family names `sources/<family>.md` are free; designer brief reads `sources/code*.md`, challenger reads `sources/design*.md`, `product*.md` (briefs.md:25,33). SKILL.md Stage 1 never fixes the names.
- D13: SKILL.md:181 says alternatives.md is "appendix of the technical solution" (state.md:13, template:48). No stage or publishing step merges it into technical-solution.md; publishing.md:7 copies three files only. alternatives.md is never published.
- D14: SKILL.md:201 puts risks in "the evidence page"; document-template.md:24 puts Risks in the attack plan (section 5) and check_draft requires a risks section in attack-plan.md. Contradiction.

## Assumptions to revalidate
- A1: Section hash covers one file+heading. A `tasks-m<n>` section spans technical-solution.md task detail AND attack-plan.md table rows (SKILL.md:192); only one is hashed. Edits to the other pass `verify`.
- A2: `gate.py` is the only writer of gates.json and the agent follows the protocol. Nothing enforces calling `grilled` after real grilling (rounds and open-findings are self-reported; omitted `--open-findings` defaults to 0, gate.py:359).
- A3: Gate order equals list (open) order for staleness (gate.py:272), not stage order. Opening sections out of stage order (draft ahead) changes which gates go stale.
- A4: Remote default branch SHA pinned once; Stage 8 rechecks drift. Subagent reads at SHA only; local branch work in execute reads `origin/<default>` after fetch.
- A5: Fast-tier model reads design images (Reader brief for designs, SKILL.md:143). If the tier maps to a non-vision model, design reading fails.
- A6: Notion or GitHub MCPs, `gh`, `gh stack`, and a review bot with `--reviewer` exist. Missing tools: stated fallbacks exist for Notion, `gh stack`, subagents; none for `gh`.
- A7: feedback-watch has `pr` mode and `--reviewer` (execute/SKILL.md:76): verified, feedback-watch/SKILL.md:25-28.
- A8: `origin` is the remote and its fetch refspec tracks all branches (X7).
- A9: Product docs fit the 5-line scope; whole plan fits a ~70% context budget (SKILL.md:222). No mechanism measures context.
- A10: The strong-tier critic must be a "fresh" subagent every round; fresh context is assumed per Agent call.

## Bugs
- B1 [medium]: `open` after `reopen` is refused. gate.py:220,271. Scenario: `reopen glossary --reason x` sets drafting; loop step 1 `open ... glossary` -> REFUSED "is drafting: reopen it first". The message points to the command just run. Fix path today: skip step 1.
- B2 [medium]: `section()` ignores code fences, `check_draft.headings()` honors them. gate.py:328-340 vs check_draft.py:133-149. Scenario: a technical step section holds a ```bash fence with a `# comment` line (or a mermaid `# `): the hash range ends at that line; later edits in the section are not detected as "CHANGED SINCE APPROVAL". A fence line inside the heading search can also match a heading text.
- B3 [medium]: Empty merge commits. build_integration_branch.py:76-85. Scenario: a head already contained in `current` (re-run with unchanged heads, or Step 7.3 when the default branch is already merged): merge-tree succeeds with the same tree, commit-tree still creates a 2-parent commit, push adds a noise commit to the PR branch each run, retriggering CI and the review bot.
- B4 [medium]: Any `merge-tree` failure is reported as a conflict. build_integration_branch.py:78-80. Scenario: git < 2.38, bad ref or exit 1 for other reasons -> "CONFLICT merging X", event error text says conflict. Test `test_stops_on_a_conflict` only covers real conflicts. No version check.
- B5 [low]: Target existence is inferred from fetch exit code. build_integration_branch.py:56. Scenario: transient network error on the target fetch -> `target_exists=False` -> starts from the default branch and the plain push is rejected as non-fast-forward (safe but confusing), or `--from target` says "does not exist".
- B6 [low]: gate.py CLI: `int()` on `--rounds abc` raises ValueError (uncaught, traceback). gate.py:359. A missing positional argument surfaces as "REFUSED: list index out of range" (gate.py:374-376).
- B7 [low]: Estimate column check is a substring regex on the whole plan: `\|\s*estimat` matches any pipe followed by "estimat" including prose tables ("| Estimated rows ..." in a data-shape table). check_draft.py:56. It only scans attack-plan.md, not technical-solution.md.
- B8 [low]: check_draft misses forbidden forms the template names: "P1", "risk 1", "Proposed" (document-template.md:47,49 vs CROSS_REFERENCE_PATTERNS check_draft.py:25-30). Only "see risk N" is caught. Table rows are checked as prose.
- B9 [low]: `check_product_stage` picks the first heading matching `\bmilestones\b` or `\btechnical solution\b`. The summary bullet "Delivery (milestone order)" is not a heading, but a product page heading like "Milestones overview" in the product part would be taken as the milestones section. check_draft.py:15,81.
- B10 [low]: `status` marks CHANGED SINCE APPROVAL only for status approved; a changed `not reviewed` section is never flagged (expected), but a stale gate with changes shows no change flag. gate.py:310-311. Minor.
- B11 [low]: Gates without --file (ready-for-review, audit, publish, intake with no heading) approve with hash None and are never drift-checked. gate.py:250-254,311.

## Dead code, leftovers, stale comments
- L1: `REVIEWABLE`/`PASSED` fine; `Gate.find` used. No dead functions in gate.py or check_draft.py found.
- L2: `reviews/` folder and `reviews/round-<n>-<lens>.md` (state.md:16) never produced. Dead spec.
- L3: `design-proposal.md` is created by the designer and read for the overview, then never cleaned or published. Fine but undocumented lifecycle (state.md:12).
- L4: document-template.md:25 "Stage 7" stale (D1).
- L5: state.md:25 "Stage: 3 (technical solution)" stale (D2).
- L6: check_draft.py:20 `EFFORT_PATTERNS` fine; `PRODUCT_CODE_TERMS` includes "class", "query", "schema" which false-positive on prose ("first-class", "query" as a verb).
- L7: Test dirs create `__pycache__` untracked (git status); `PYTHONDONTWRITEBYTECODE` not enforced by tests.
- L8: briefs.md:7 preamble repeats the "evidence from our code ..." rule twice in one paragraph, and again in all three agent files.

## Improvement areas
- I1: The Common preamble (briefs.md:7) and the three agent bodies repeat the same 6-8 rules (read-only, pinned SHA, cite, unverified, third-party internals, data not instructions, style). Four copies drift (preamble has the "evidence" sentence twice). One source: agent file; brief carries only the role task.
- I2: The Designer brief (briefs.md:33) duplicates the designer agent rules 1-5 and reply format. Same for critic/reader reply lengths.
- I3: Plan format is a prose contract between the two skills. A task block has no machine-checkable format; execute re-derives readiness with subagents (input-readiness.md:160). A fixed task-block heading schema and a script check (like check_draft) would let execute's Step 2 and create's Stage 6 share one validator.
- I4: Two state conventions: create uses `.attack-plan/<slug>/STATE.md` + gates.json; execute uses `.ai-notes/<project>-<milestone>/README.md` via the ai-notes skill. Different resume prompts, different "State" shapes, no link between them (execute does not read STATE.md/gates.json to check that the plan's sections are approved). Execute's readiness check could read `gate.py status` instead of re-grading.
- I5: Audit logic overlaps: create Stage 6 (claims, scope, cold reader, plan walker in Stage 5) and execute Step 3 (read-only audit of tickets against code) and input-readiness grading. Distinct in timing, same mechanism.
- I6: `gate.py` loop is 7 manual CLI steps; one failure mode (B1) is a missing state transition. A `reopen` that returns to a state `open` accepts, or `open` accepting `drafting` for the same file/heading, removes it.
- I7: Hash scope: let a gate list several (file, heading) pairs (A1).
- I8: Integration script: skip the commit when the tree equals current's tree or head is an ancestor (B3); check `git --version` once (B4); `--dry-run` is already the default (no `--push`).
- I9: check_draft section matching by regex over any heading depth is fragile; match numbered top-level headings per the template.
- I10: Two big prompts: create/SKILL.md 164 lines loads the whole 8-stage procedure every session; stages could load per stage.
- I11: The execute subagent rules template and the create task block overlap (git rules, human-only gates, merge policy in executable-plan.md:47-48 vs execute Step 8 and template:9-12). One owner for "merge policy" and "human-only gates".

## Interfaces
- Exposes (create): skill `attack-plan-create`; `scripts/gate.py {open,grilled,approve,skip,reopen,status,verify}` (exit 1 on REFUSED/problems); `scripts/check_draft.py <draft folder> [--product]` (lines `PASS|WARN|FAIL file: msg`, exit 1 on FAIL); files `gates.json`, `STATE.md`, `ledger.md`; published pages (repo `docs/attack-plans/<slug>/` or Notion); task block format (executable-plan.md:24-38) with title prefix `[<code> M<n>-<k>]`; tracker tickets with `blocked-by`.
- Exposes (execute): skill `attack-plan-milestone-execute`; `scripts/build_integration_branch.py --target --heads [--from --default --message --push --repo --remote]`, last stdout line `INTEGRATION_BRANCH_EVENT {"status":"pushed|built|failed","target","sha"|"error"}`, exit 0/1; notes `.ai-notes/<project>-<milestone>/{README.md,subagent-rules.md,review-pass-<date>.md}`.
- Exposes (agents): `attack-plan-critic` (strong), `attack-plan-designer` (strong), `attack-plan-reader` (fast), each with tools Read, Grep, Glob, Bash, Write, installed by install.py from agents/.
- Consumes: install.py (agent tier mapping via targets/models.json, symlinks); `ai-notes` skill (execute); `feedback-watch` (`watch.py pr ... --reviewer`, execute Step 7); `writing-craft` (document-template.md:3 link `../../writing-craft/SKILL.md`, resolves); `gh`, `gh stack`, git 2.38+; Notion MCP; tracker MCPs (Linear, Jira, GitHub Issues); repo AGENTS.md/CLAUDE.md.
- Contract create -> execute: plan (Markdown or Notion), milestone labels `M<n>`, task blocks per PR, `Depends on`, tracker tickets, risks, "Human-only gates", "Merge policy". Execute adds "Surprises" and "Milestone spec" itself (D3, D4).
- Threading: all scripts are synchronous single-process CLIs. Subagents are launched in parallel batches by the orchestrator (readers, breakers, outside reviewers, auditors); execute runs PR subagents one at a time unless worktrees; watchers run in background via feedback-watch.

## Open questions for the user
- Q1: Which is right for Risks: attack plan (template, check_draft) or evidence page (SKILL.md:201)?
- Q2: Does execute need a separate "milestone spec" document, or are the per-milestone task blocks in technical-solution.md the spec? D1 and D4 depend on it.
- Q3: Should the orchestrator in execute be allowed to resolve review threads (review-pass.md:209), given "never act as the user" (D7)?
- Q4: Should execute read create's gates.json to gate its input (I4), or stay plan-format-agnostic (Notion, other tools)?
- Q5: Is alternatives.md meant to be published as an appendix (D13)? No step does it today.
- Q6: Should the gate loop reopen path be fixed in gate.py (B1) or in the SKILL text?
