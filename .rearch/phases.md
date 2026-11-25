# Phases

10 phases. Phase 1 writes the topic docs and Phase 2 adds the test harness. Phases 3-10 build the modules in dependency order: installer, shared conventions, global prompts, then the skills (feedback-watch before execute, create before execute, qa-session before execute, rearchitect last). The storyboard skill (added 2026-11-25) folds into Phase 1 (its topic doc), Phase 2 (its tests) and Phase 8 (with qa-session: both build a human-read page through one strong Builder), so the count stays 10. Final cleanup and the traceability audit belong to Stage 6 (Q35), so this plan ends with the last code phase.

## Rules for every phase

- The baseline stays green when the phase ends: every unittest suite passes, and `install.py --check` behaves as the phase states. Every kept requirement still works.
- A phase that changes `agents/`, `instructions/` or the set of skill folders changes installed outputs. Its `--check` must list exactly the expected items. The orchestrator then runs `install.py` with the user's OK, and after that `--check` prints `0 change(s) needed`. The phase agent never writes into `~/.claude` or `~/.config/opencode`.
- Known defects get tests in Phase 2, marked `@unittest.expectedFailure` with the FR ID in the test name. The phase that fixes a defect removes its marker. Python 3.9 counts an unexpected success as a failure, so a forgotten marker turns the suite red.
- Old code goes in the phase that replaces it. No two implementations of one behavior remain when a phase ends.
- Characterization tests change only where the phase changes behavior on purpose, and the commit names the FR.

Standard verification (V), from the repo root:

```sh
/usr/bin/python3 -I -c 'import sys; [compile(open(f).read(), f, "exec") for f in sys.argv[1:]]' install.py skills/*/scripts/*.py   # py_compile writes __pycache__ even with PYTHONDONTWRITEBYTECODE (topics/macOS Python.md)
for s in tests skills/*/tests; do [ -d "$s" ] || continue; printf '%s: ' "$s"; PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s "$s" 2>&1 | tail -1; done
/usr/bin/python3 -I install.py --check | tail -1
git status --porcelain --untracked-files=all | grep -c pycache   # 0 from Phase 2 on (NFR-05)
```


## Verification (applies to every phase)

The user chose zero manual checks for this run (2026-11-25). M1..M11 in baseline.md are not run. A phase verifies with automated means only:
- the baseline: the unittest suites and `install.py --check`;
- an install into a throwaway `HOME` (a `mktemp -d` folder) for both tools, then parse every rendered agent file's frontmatter and check every skill link resolves;
- scripts run against fixtures, and `--help` for each script;
- the grep tests the phase adds (model names, Spawns tables).
What can't be checked this way (live `gh`, live opencode, Notion) gets listed in the phase's done reply as "not verified" and in deviations.md. It is not a blocker.

## Phase 1: Topic docs

Goal: every external fact from the audits lives in one topic doc with a source or the word `unverified`. Q37's opencode branch is settled as far as docs allow.
Covers: CON-CC-01..04, CON-OC-01..02, CON-GH-01..06, CON-GIT-01..05, CON-NOTION-01, CON-CHROME-01..05, NFR-01, NFR-02, Q37 (check), FR-RA-11
Touches: skills/harness-common/SKILL.md (new, description: shared harness conventions, load when another harness skill points here), skills/harness-common/topics/Claude Code.md, topics/opencode.md, topics/GitHub.md, topics/git.md, topics/Notion MCP.md, topics/macOS Python.md, topics/Chrome headless shell.md (all new), skills/attack-plan-create/references/publishing.md (Notion quirk list replaced by a link), README.md (harness-common row, topic links). 10 files.
Deletes: none
Work:
- Sources are the audits' External facts sections (X items) and requirements.md CON-* lines. Each quirk gets symptom, cause, workaround and code location (docs-style.md).
- Q37 check, one scripted pass: if `opencode` is on PATH, run `opencode --help`, `opencode models` and `opencode agent --help`. In every case read the vendor docs pages for agents, CLI, permissions and the task tool. Record each answer with its link: does the task tool take a per-call model; which agent folder name (`agent/` or `agents/`) and frontmatter keys apply; are project-local agents loaded, and do they override global ones of the same name; are agents reloaded without restart; is the spawn tool deniable; does an agent with no `model` inherit the session model. opencode is not installed on the architect's Mac, so live answers wait for M2.
- In `topics/opencode.md`, write a "Model per spawn" section ending in one of: `per-spawn parameter`, `override files`, `unknown`. Phase 4 builds what it says.
- `topics/Chrome headless shell.md` from audit/storyboard.md X1-X6, X8 and CON-CHROME-*. One scripted batch with the Playwright shell, output in `mktemp -d`, never a browser app: (a) shoot a generated page with `data-h` 20000 and 40000 and record the PNG heights, which settles the screenshot limit (CON-CHROME-04); (b) a page in a temp folder loading a font file copied from `/System/Library/Fonts/Supplemental` by a relative `url()`, checked with `document.fonts.check` in `--dump-dom`, which settles CON-CHROME-05. `PLAYWRIGHT_BROWSERS_PATH` comes from the Playwright docs with its link. CON-CHROME-01 stays `unverified`: reproducing it would steal the user's focus. Without a shell, every item stays `unverified`.
- `topics/Claude Code.md` gets a plugin-skills section: `frontend-design` lives under `~/.claude/plugins/cache/`, is not shipped here, and is named "when available" (CON-CC-04).
Verify: V. `--check` shows 2 new skill links (harness-common, both hosts) until install, plus the 2 storyboard links if install.py has not run since commit 96ecd40 (baseline.md).
Manual: none. Verify automatically (see "Verification" at the top).
Exit: each CON-* fact sits in exactly one topic doc. The Notion quirks exist only in `topics/Notion MCP.md`. Every fact has a source or `unverified`.

## Phase 2: Test harness

Goal: characterization tests for current behavior, defect tests marked expected-failure, install.py tests, and repo-wide rule tests including the FR-AGT-08 model-name grep.
Covers: NFR-04, NFR-05, FR-AGT-08 (test), FR-XS-02 (shared fixture)
Touches: .gitignore (`__pycache__/`, `*.pyc`), install.py (only `if __name__ == "__main__"` and `main(argv=None, home=None)` so tests use a temp home; no behavior change), tests/test_install.py (new), tests/test_repo_rules.py (new), tests/fixtures/markdown/fenced-headings.md (new), tests/fixtures/agents/bad-fence.md and bad-tier.md (new), skills/attack-plan-create/tests/test_gate.py, skills/attack-plan-create/tests/test_check_draft.py, skills/qa-session/tests/test_check_page.py, skills/feedback-watch/tests/test_watch.py, skills/attack-plan-milestone-execute/tests/test_build_integration_branch.py, skills/storyboard/tests/test_shoot.py, README.md (test commands include `tests/`). 15 files.
Deletes: none
Work:
- `tests/test_install.py`: empty temp home plan, second run is a no-op, `--check` exits 0 or 1, declined prompt, no-TTY exit 2, `--claude 0`, link replacement. Expected-failure tests: description with `: ` is quoted (FR-INST-11), prune of a removed agent (FR-INST-09), symlinked destination not written through (FR-INST-12), named error for a bad agent file (FR-INST-10), declined exit differs from drift (FR-INST-08).
- `tests/test_repo_rules.py`:
  - Model-name grep over `git ls-files`. It scans every tracked file under `skills/storyboard/` too, `skeleton.html` included; the test asserts each `skills/*/` folder contributed at least one scanned file, so a new skill cannot fall outside it. Run-state folders `.rearch/`, `.attack-plan/` and `.ai-notes/` are excluded, because FR-AGT-07 records the confirmed mapping there. Patterns are stored ROT13-encoded, so the test file holds no model name. The allowlist `{targets/models.json, skills/rearchitect/SKILL.md}` is checked both ways: no hit outside it, and every listed file still hits.
  - `__pycache__` is ignored. Every `skills/*/` has a SKILL.md whose `name` equals the folder name. Every `agents/*.md` parses.
- Shared fixture `fenced-headings.md`: a section with a fenced `# comment` and `- [ ]`. gate, check_draft and check_page tests all read it.
- `skills/storyboard/tests/test_shoot.py`: characterization of `main` with `subprocess.run` replaced by a fake (one `path  WxH` line per theme, height from `data-h`), and a skeleton render through the real shell, skipped when `find_chrome()` finds none (SB-Q11). Expected-failure tests: Chrome timeout gives one FAIL line (FR-SB-11), non-executable `$CHROME` gives a FAIL line (FR-SB-10), failed dump is reported (FR-SB-11), FAIL reason is plain text (FR-SB-11), `PLAYWRIGHT_BROWSERS_PATH` honoured and host-architecture shell preferred (FR-SB-10), skeleton OS reduced-motion rule covers every element (FR-SB-08), skeleton heading reads "Keyboard path" (FR-SB-05). 8 markers.
- Expected-failure tests for the known defects: gate reopen-then-open, gate fenced hash, gate `--rounds abc`, integration no-op merge, non-conflict git failure reported as conflict, watch sole cancelled check, watch merged PR, watch gh failure on stdout, watch FAIL-to-FAIL output change, check_page `Q4 Budget` in backticks, check_page `[Next fact.]`, check_page `### 1 Title`.
Verify: V. 6 suites green (tests/ plus 5 skill suites, storyboard included). Report the expected-failure count, 25 (17 plus 8 storyboard).
Manual: none. Verify automatically (see "Verification" at the top).
Exit: every item in requirements.md "Known defects" except the prompt-only ones (rearchitect SKILL.md, storyboard brief.md:3 and SKILL.md:81) has an expected-failure test. The model-name grep scans `skills/storyboard/`. `--check` prints 0 after Phase 1's install.

## Phase 3: Installer and agent sources

Goal: install.py rebuilt on the two host adapters. No model lines, validated sources, prune with a manifest, backups, one preamble.
Covers: FR-INST-01..14, FR-AGT-01..04, FR-AGT-06, FR-XS-01 (preamble), NFR-06..08, NFR-13 (install side)
Touches: install.py, skills/harness-common/scripts/claude_code.py (new), skills/harness-common/scripts/opencode.py (new, paths and render only), skills/harness-common/references/preamble.md (new), agents/attack-plan-critic.md, agents/attack-plan-designer.md, agents/attack-plan-reader.md, agents/rearch-architect.md, agents/rearch-auditor.md, agents/rearch-phase.md, tests/test_install.py, skills/harness-common/tests/test_adapters.py (new), tests/test_repo_rules.py (allowlist loses models.json), README.md (install section, exit codes, agent format, rerun after new skill folders). 14 files.
Deletes: targets/models.json, targets/
Work:
- install.py imports the adapters through the bootstrap line. `parse_agent` names the file and key on every error. The tier must be `fast`, `default` or `strong`. `tools` must not list Agent or Task.
- Render: descriptions are double-quoted YAML. Claude keeps `tools`. opencode maps `tools` to a V2 `permissions` list (`topics/opencode.md` "Permissions": deny-all base, one allow per mapped action) plus `{action: subagent, resource: "*", effect: deny}`, and never writes a `tools` or `permission` key (a file with `permissions` is read as V2 and V1 keys are dropped). The sandbox line goes to opencode only. Neither host gets a `model` line.
- Manifest `<host>/agent-harness-manifest.json`. Prune manifest entries that are no longer planned, and links into this checkout whose target is gone. Never touch other links.
- A real folder at a skill destination moves to `<host>/agent-harness-backup/<timestamp>/`. Exit codes 0/1/2/3/4 as in architecture.md.
- Agent bodies lose the style and sandbox lines. Their role text stays.
- tests/test_install.py: `fake_root` copies `targets/models.json`; drop that copy with the file. `targets()` takes the two host bases since Phase 2 (deviations.md, Phase 2).
Verify: V. `--check` lists 12 agent rewrites plus the manifests, then 0 after install.
Manual: none. Verify automatically (see "Verification" at the top).
Exit: no expected-failure marker left in tests/test_install.py. The grep allowlist holds only skills/rearchitect/SKILL.md. No agent file holds the style line or the sandbox line (deviations.md, Phase 3: briefs.md loses its copy in Phase 7, rearchitect SKILL.md its copies in Phase 10).

## Phase 4: Shared conventions and model tiers

Goal: the runtime references every skill cites, and the tier mechanism from Q37.
Covers: FR-AGT-05, FR-AGT-07 (mechanism), FR-XS-01, FR-XS-03, FR-XS-04, FR-APC-14, FR-QA-10, NFR-09, NFR-10, NFR-13
Touches: skills/harness-common/SKILL.md, skills/harness-common/references/subagents.md (new), references/model-tiers.md (new), references/state.md (new), references/publishing.md (new), skills/harness-common/scripts/opencode.py (`models`, plus `apply-tiers`/`clear-tiers` only if Phase 1 wrote `override files`), skills/harness-common/tests/test_adapters.py, tests/test_repo_rules.py (`Spawns` table rule: each named agent exists, tier matches), skills/attack-plan-create/SKILL.md (publishing pointer only), skills/qa-session/SKILL.md (publishing pointer only), skills/harness-common/topics/opencode.md (code locations), README.md. 12 files.
Deletes: skills/attack-plan-create/references/publishing.md, skills/qa-session/references/publishing.md
Work:
- `model-tiers.md`: list, propose, confirm gate (one model for all tiers allowed), record the table, pass per spawn. Claude Code: Agent tool `model` (an alias only). opencode: `override files` (Phase 1, `topics/opencode.md` "Model per spawn"): `opencode.py apply-tiers` writes full copies of the installed agents with a `model` line, plus `general.md`, into the project's `.opencode/agents/`, excludes them in `.git/info/exclude`, then the orchestrator runs `opencode reload`; `clear-tiers` removes them. The `subagents.md` two-layer rule covers Claude Code `general-purpose` spawns too: Claude Code allows three layers by default (`topics/Claude Code.md` "Nested spawns"), so the brief carries "never spawn".
- `subagents.md`: brief minimum, fresh subagent per unit, word caps, two layers, missing-agent fallback that finds the checkout with `realpath` of the installed harness-common link and reads `agents/<name>.md` there. The fallback prompt is `preamble.md`, then the agent body: agent sources hold no preamble since Phase 3. On opencode it adds the sandbox line from `opencode.py` (`SANDBOX_LINE`).
- `state.md`: `Next` line, `Models for this run` table, exclude rule. Single-spawn skills (storyboard) keep no resume file: the table and Next line go in the work's ai-notes "State (start here)" when one exists, else the gate runs in the session and the hand-over ends with a fenced resume prompt (SB-Q1).
- `publishing.md`: the merged procedure. Each calling skill states its source of truth.
Verify: V. `opencode.py models` prints a clear "opencode not found" line and exits 1 on this Mac.
Manual: none. Verify automatically (see "Verification" at the top).
Exit: no skill holds its own publishing procedure. Nothing outside `opencode.py` runs the opencode CLI. The `Spawns` test runs (vacuous until the skill phases add tables).

## Phase 5: Global instructions, notes and writing

Goal: global.md deduplicated and tool-neutral. ai-notes and writing-craft scoped.
Covers: FR-GLB-01..11, FR-NOTES-01..07, FR-WRIT-01..07, NFR-09
Touches: instructions/global.md, skills/ai-notes/SKILL.md, skills/writing-craft/SKILL.md, README.md. 4 files.
Deletes: none
Work:
- global.md: one delegation rule (lines 8, 13, 17 merged), one test-output rule (9, 16), no "Claude" for the model, `frontend-design` and REA "when available" (Q8, Q9).
- ai-notes: the body trigger wins in the description (Q10). It defines the "State (start here)" section and cites `harness-common/references/state.md`.
- writing-craft: covers human-read text, names agent-to-agent briefs and audits as exempt, neutral examples, section 7 folded in (Q12).
Verify: V. `--check` lists 2 global-file rewrites, then 0 after install.
Manual: none. Verify automatically (see "Verification" at the top).
Exit: each global rule appears once. writing-craft has no section 7 and no QA-only example.

## Phase 6: GitHub adapter and feedback-watch

Goal: watch.py on `github.py` with every audited defect fixed.
Covers: FR-FW-01..15, NFR-03, NFR-11, NFR-12, FR-XS-05
Touches: skills/harness-common/scripts/github.py (new), skills/harness-common/tests/test_github.py (new), skills/feedback-watch/scripts/watch.py, skills/feedback-watch/tests/test_watch.py, skills/feedback-watch/SKILL.md, skills/harness-common/topics/GitHub.md (code locations), README.md. 7 files.
Deletes: watch.py's `run_gh`, `gh`, `resolve_repo` and the REST reviews call (moved into github.py)
Work:
- One paginated GraphQL snapshot per PR: state, head, rollup, reviews with commit and state, threads with author kind.
- Merged or closed PR: one line, then stop watching it (Q23). A sole cancelled run counts as failing with the label "cancelled" (Q24). ALL DONE needs 2 identical polls (Q25). Changes-requested counts as reviewed, dismissed does not (Q26). An empty `startedAt` sorts as newest. `--interval` must be > 0. 3 failing rounds print `GH FAILING` and exit 4.
- `--until bots`: done when CI is green, the reviewers are done and no bot-started thread is unresolved. The line shows the human count (Q17 exit goal).
- Local mode: print on changed FAIL output, `--cmd-timeout`, `--timeout`, stdin closed, snapshot after the run, skip `.attack-plan` and `.rearch` (Q27).
- test_watch.py: `test_cancelled_run_is_ignored` pins the FR-FW-03 defect; delete it when `test_FR_FW_03_a_sole_cancelled_run_is_failing` loses its marker. The FR-FW-08 test asserts one line holding `merged` and that the watcher stops; set its exit code there (deviations.md, Phase 2).
- SKILL.md states the exact print, stop and "fine conclusion" rules (FR-FW-15) and links the topic docs for Monitor and the background job. opencode background shell jobs notify only when the process exits (`topics/opencode.md` "No Monitor tool"): on opencode the skill runs PR mode with `--timeout` and reads the log tail at exit or idle; local mode there needs `--once` or the user's prompt.
Verify: V
Manual: none. Verify automatically (see "Verification" at the top).
Exit: watch.py runs no subprocess for gh. No watch expected-failure marker remains.

## Phase 7: Markdown seam and attack-plan-create

Goal: one fence-aware parser under gate.py and check_draft.py. Create fixes and the task-block schema.
Covers: FR-APC-01..17, FR-APC-20, FR-XS-02 (create side), FR-WRIT-06 (create cites writing-craft), FR-AGT-07 (`Spawns` table), FR-XS-01, FR-XS-03; removes dropped FR-APC-18, -19
Touches: skills/harness-common/scripts/markdown.py (new), skills/harness-common/tests/test_markdown.py (new), skills/attack-plan-create/scripts/gate.py, scripts/check_draft.py, tests/test_gate.py, tests/test_check_draft.py, SKILL.md, references/briefs.md, references/document-template.md, references/executable-plan.md, references/state.md, agents/attack-plan-critic.md, agents/attack-plan-designer.md, agents/attack-plan-reader.md. 14 files.
Deletes: heading and section code in gate.py and check_draft.py
Work:
- gate.py: hash through `markdown.digest`, several (file, heading) pairs per gate (Q22). `open` accepts a reopened gate. CLI errors are named. Document staleness by list order.
- check_draft.py: B7 (estimates only in table headers), B8 (P1, risk 1, Proposed), B9 (milestones by numbered heading), L6 (code-term list). Add `--tasks <file>` for the fixed task-block headings (Q20).
- Template: drop section 6, risks only in section 5 (Q14), alternatives internal (Q15). Fix the state.md example stage. `reviews/` gone.
- Briefs: role tasks only, every brief names its output path and return cap, preamble by reference. Agent bodies drop duplicated rules (attack-plan I1, I2). `Spawns` table plus the tier gate from model-tiers.md.
- SKILL.md "Subagents": the missing-agent fallback sentence becomes a pointer to `harness-common/references/subagents.md` "Missing agent". Keep the Stage 7 publishing lines Phase 4 added (source of truth, Markdown copy, Notion parent and children) (deviations.md, Phase 4).
Verify: V. `check_draft.py --tasks` passes on the example in executable-plan.md.
Manual: none. Verify automatically (see "Verification" at the top).
Exit: neither script holds a heading regex. No create expected-failure marker remains. "Milestone specs" and "appendix" appear nowhere in the skill.

## Phase 8: qa-session and storyboard

Goal: the simplified QA page and check_page.py on the shared parser. Storyboard on the shared tier gate, brief minimum and state rule, with shoot.py failing cleanly.
Covers: FR-QA-01..15, FR-SB-01..16, NFR-14, NFR-15, FR-XS-02 (qa side), FR-AGT-07 (`Spawns`: qa Builder and Verifier, storyboard Builder, all general, strong), FR-XS-01, FR-XS-03 (storyboard)
Touches: skills/qa-session/scripts/check_page.py, skills/qa-session/tests/test_check_page.py, skills/qa-session/SKILL.md, references/page-template.md, references/briefs.md, references/setup-checklist.md, skills/storyboard/SKILL.md, skills/storyboard/references/brief.md, skills/storyboard/references/skeleton.html, skills/storyboard/scripts/shoot.py, skills/storyboard/tests/test_shoot.py, skills/harness-common/topics/Chrome headless shell.md (code locations), README.md (both rows). 13 files.
Deletes: Known limits, Product questions and After the session from the template and checker. In storyboard: "Commit the storyboard with the decisions", "strongest model tier available", the brief's copies of SKILL.md rules, the docstring's external facts (now in the topic doc).
Work:
- Keep the two Environment rules from commit 5519633 (user, outside the plan) in the collapsed setup: confirm the deploy finished on the pushed commit before seeding, and send browser headers (for example `Accept: text/html`) when probing the environment from a script.
- Page: collapsed setup for the lead developer (`<details>` in Markdown, a toggle in a document tool), numbered scenarios with persona, start point, steps and expected results, then an empty Findings section with no table (Q33, Q34).
- check_page: fence-aware through `markdown.py`. `[...]` placeholders are caught. `### 1 Title` is flagged. Backticked labels are exempt from the id and word checks (Q31). "now" is added. The persona line follows the template's format. The Findings heading matches exactly and must be empty with no table at Create.
- qa SKILL.md "Publishing" (added in Phase 4): drop the Findings-table and scenario-count wording that the simplified page no longer has; keep the pointer to `harness-common/references/publishing.md`. On opencode both skills pass `apply-tiers --general strong` (deviations.md, Phase 4).
- Briefs: absolute paths, the injection rule, US English prose with UI-language labels (Q32). `previous.md` moves to `.ai-notes/.qa-previous/<slug>.md`, outside the area folder, and is deleted after Rework (S13).
- Storyboard SKILL.md: `Spawns` table (Builder, `general`, `strong`) and the tier gate from model-tiers.md; run state per state.md's single-spawn rule (SB-Q1); `frontend-design` when available with the fallback (SB-Q2); commit only when the user asks (SB-Q3); a default for every input (SB-Q6); "Every frame works in both themes"; decisions through publishing.md when the requirements doc is in a document tool (SB-Q9); links the global delegation rule (SB-Q10).
- brief.md: preamble by reference, absolute paths for `<skill>`, the page and every source, data-not-instructions, `unverified`, never spawn, 150-word report. Rules by reference to SKILL.md.
- skeleton.html: "Keyboard path" in heading and contents; `@media (prefers-reduced-motion: reduce)` stops every animation, as the toggle does.
- shoot.py: one `FAIL <reason>` line and exit 1 for timeout, non-executable `$CHROME`, failed dump and failed screenshot, reason as plain text; `PLAYWRIGHT_BROWSERS_PATH` and host architecture in the lookup; `(no data-h, used --height)` and `(clipped from H)` suffixes with the limit Phase 1 measured: no limit up to 200000 px, so the cap is 200000 (SB-Q7, SB-Q8). Docstring keeps usage and links the topic doc.
- test_shoot.py: `test_chrome_from_env` (a missing `/opt/chrome`) and `test_newest_playwright_shell` (non-executable files) pin today's unchecked lookup; change them with the executable check. test_check_page.py has a fourth marker, `test_FR_XS_02_fenced_lines_are_not_headings_or_checks`, fixed by the shared parser (deviations.md, Phase 2).
Verify: V. Then, from the repo root:
- `/usr/bin/python3 -I skills/storyboard/scripts/shoot.py --help` exits 0.
- `CHROME=/nonexistent /usr/bin/python3 -I skills/storyboard/scripts/shoot.py skills/storyboard/references/skeleton.html --out "$(mktemp -d)"` prints exactly one line starting `FAIL` and exits 1.
- With a shell present, the same command without `CHROME` prints 2 `path  WxH` lines. Without one, report it as not verified.
- `grep -rn 'strongest' skills/qa-session skills/storyboard` prints nothing.
Manual: none. Verify automatically (see "Verification" at the top).
Exit: the template has exactly three parts. No qa or storyboard expected-failure marker remains. Storyboard SKILL.md has a `Spawns` table, and the repo rule test passes for it. No storyboard file says to commit.

## Phase 9: git adapter and attack-plan-milestone-execute

Goal: integration script on `git.py`, review threads by script, and the execute exit goal.
Covers: FR-APE-01..14, NFR-02, NFR-12, FR-WRIT-06 (execute cites writing-craft), FR-AGT-07 (`Spawns`: PR and fix subagents default, ticket auditors fast), FR-XS-05
Touches: skills/harness-common/scripts/git.py (new), skills/harness-common/tests/test_git.py (new), skills/attack-plan-milestone-execute/scripts/build_integration_branch.py, tests/test_build_integration_branch.py, scripts/review_threads.py (new), tests/test_review_threads.py (new), SKILL.md, resources/input-readiness.md, resources/review-pass.md, resources/subagent-rules-template.md, skills/harness-common/topics/git.md (code locations), README.md (row, git 2.38+). 12 files.
Deletes: `git()` in build_integration_branch.py, the GraphQL commands in review-pass.md
Work:
- Integration: skip a head already contained in the target (event status `unchanged`). `Conflict` is distinct from `GitError`. The git version is checked up front. Target existence comes from `ls-remote`. Fetch each branch with an explicit refspec `+refs/heads/<b>:refs/remotes/<remote>/<b>`: a single-branch clone does not update `<remote>/<b>` otherwise (`topics/git.md`).
- `review_threads.py`: list with bot or human per thread; resolve refuses human threads (Q17). Use `github.Gh.pr_snapshot` (threads carry `is_bot`, every page read) and `Gh.resolve_thread`, both in place since Phase 6.
- SKILL.md:
  - Exit goal: every PR in every stack has green CI, and every bot review thread is addressed and resolved. Human threads are listed for the user.
  - Arm feedback-watch with `--until bots`. Its stop line is `BOTS DONE`; open human threads show as `(human M)` on the PR line (deviations.md, Phase 6).
  - Gate input on `gate.py status` when gates.json exists (Q21), and run `check_draft.py --tasks <technical-solution.md> --milestone <n>` on the milestone's task blocks (Q13, Q20). The task headings are fixed in create's `executable-plan.md` "Task block schema"; input-readiness.md points there instead of restating the fields (deviations.md, Phase 7).
  - Pass "Context for an outside reviewer" to PR subagents (Q19). Step 9 runs the qa-session skill in this session (Q18). Its own page description ("personas, happy path scenarios ..., and a findings table", SKILL.md:99) goes: the qa-session page has no findings table since Phase 8.
  - The notes "State (start here)" section follows ai-notes.
  - On opencode, PR, fix and ticket-auditor spawns are all `general`, so `apply-tiers --general default` puts them on one model (A2; deviations.md, Phase 4).
- Rules template: no "Surprises" (Q16), writing-craft for PR text, never spawn.
Verify: V
Manual: none. Verify automatically (see "Verification" at the top).
Exit: no "milestone spec", "Surprises" or raw `resolveReviewThread` text remains in the skill. No execute expected-failure marker remains.

## Phase 10: rearchitect

Goal: rearchitect fixed, domain-neutral, and on the shared tier gate. This is the last model-name holder.
Covers: FR-RA-01..14, FR-GLB-12, FR-AGT-07 (rearchitect gate, models table in baseline.md), FR-AGT-08 (complete), NFR-10
Touches: skills/rearchitect/SKILL.md, references/state.md, references/docs-style.md, agents/rearch-architect.md, agents/rearch-auditor.md, agents/rearch-phase.md, tests/test_repo_rules.py (allowlist removed; every skill that names an agent or a general spawn, storyboard and qa-session included, has a `Spawns` table), README.md. 8 files.
Deletes: "Model routing" names and the fallback paragraph in SKILL.md, the allowlist in test_repo_rules.py
Work:
- Stage 0:
  - Exact commands: `git switch -c rearch/<date>` and `git tag -a rearch-base -m "rearchitect base"`.
  - An existing branch or tag is handled.
  - `PYTHONDONTWRITEBYTECODE=1`, or ignored caches, in the clean-tree check.
- FR-GLB-12 (added after Phase 8): one new rule in instructions/global.md: shell commands suggested for the user to run use the `!` prefix, for example `! open <file>`. Commands the agent runs itself are unaffected. Mark opencode support unverified. Also use the prefix in every user-facing command line in rearchitect SKILL.md (Stage 0 clean-tree and stop/resume text).
- Model gate: the tier gate at Stage 0 and on resume. The `Models for this run` table in baseline.md follows `harness-common/references/state.md`: the backticked cell is the exact value the tool takes (an alias, or a `provider/model` id), so `opencode.py apply-tiers --state .rearch/baseline.md --general default` can read it. Stage 6 runs `opencode.py clear-tiers` on opencode (deviations.md, Phase 4).
- SKILL.md:26 style line becomes a pointer to `harness-common/references/preamble.md`; the `execute` sandbox line at :109 goes (it lives in `opencode.py` since Phase 3).
- Manual-check gate (FR-RA-14): Stage 0 asks how many manual checks the user wants, default zero. With zero, Stage 5 and Stage 6 verify automatically only and report what is not verified. Every gate shows a recommended default for each decision.
- STATE: a Progress block (aspects audited, phase in flight with its base commit). On a dirty tree after a dead phase agent, show `git diff --stat` and ask: keep and continue, or `git restore` and rerun. STATE is committed with its stage.
- Stage 6: read baseline first, audit, run the baseline and checklist, then delete `.rearch/` last. An extra phase gets appended to phases.md. Stage 6 owns cleanup (Q35, Q36).
- The architect agent gets no final-cleanup phase. Real-time rules apply only when the project has real-time paths. The auditor gets a Stage 6 per-module mode.
Risk: the running orchestrator re-reads SKILL.md on resume, so Stage 6 of this run follows the new text. That is intended.
Verify: V. The grep test runs with no allowlist.
Manual: none. Verify automatically (see "Verification" at the top).
Exit: no model name in the tracked tree outside run state. Every skill that spawns has a `Spawns` table that matches the agent tiers.
