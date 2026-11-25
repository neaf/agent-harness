# Deviations

## Phase 1 (2026-11-25)

1. CON-CC-03 is wrong for Claude Code. The docs say a subagent can spawn its own subagents, up to three layers by default (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). Only agents without `Agent` in `tools` cannot. The harness agents list `tools` without `Agent`, so they hold NFR-13; a `general-purpose` spawn does not. Change: `topics/Claude Code.md` "Nested spawns" records it. Phase 4 Work now says `subagents.md` and the brief carry "never spawn" for `general-purpose` spawns too. Stage 6 rewrites CON-CC-03 when requirements.md moves.
2. Q37 settled from the docs: `override files`. opencode's `subagent` tool takes agent id, description, prompt and `sessionID`, no model. Project agents in `.opencode/agents/` load; merge order puts them after global ones; config reloads automatically and through `opencode reload`. Merge order for Markdown agent files and reload of agent files stay `unverified`. Phase 4 Work now names the mechanism: full-copy overrides plus `general.md`, `.git/info/exclude`, `opencode reload`, `clear-tiers`.
3. opencode docs describe OpenCode 2 frontmatter. A file with `permissions` is read as V2 and its V1 keys (`tools`, `permission`) are dropped. Phase 3 Work now renders a V2 `permissions` list with the spawn action `subagent` denied, and never writes `tools`. The deny-all-then-allow shape in that line is a proposal; Phase 3 may pick another shape that matches Claude's `tools` restriction.
4. opencode background shell jobs notify the session only when the process exits; there is no per-line event. `watch.py` local mode without `--once` never exits. Phase 6 Work now says how the skill runs on opencode.
5. Screenshot limit (CON-CHROME-04): none found up to 200000 px on the headless shell 156 with `--disable-gpu`, pixels painted to the bottom. Phase 8 Work now caps at 200000.
6. CON-GIT-04 checked: in a `--single-branch` clone, `git fetch origin <b>` does not create `origin/<b>`. `build_integration_branch.py` relies on it (`:55-56`, `:77`). Phase 9 Work now fetches with an explicit refspec.
7. `python3 -m py_compile` writes `__pycache__/` next to the sources even with `-I` and `PYTHONDONTWRITEBYTECODE=1`. The first line of V did this, which is where the untracked `__pycache__/` folders in the tree come from. V now parses with `compile()` and writes nothing. `.rearch/baseline.md` still shows the old command; Stage 6 or the next baseline run updates it. The existing untracked `__pycache__/` folders predate this phase and are left in place.
8. `skills/attack-plan-create/references/publishing.md` keeps its procedure and links the topic doc for every quirk. The procedure moves to the shared reference in Phase 4, as planned.

## Not verified in Phase 1

- opencode: every fact is from its docs. opencode is not installed here, so `opencode --help`, `opencode models` and `opencode agent --help` did not run. Not checked live: model override by a project agent file, agent reload without restart, `opencode models` output format.
- GitHub: no live `gh` call. Not checked: queued `startedAt` as printed by `gh`, job logs mid-run, `gh run view --log` waiting, "runner lost communication", the stacked-CI mechanism, `sort:created-asc`.
- Notion MCP: every quirk stays `unverified`.
- Claude Code: why an agent with an unquoted `: ` in its description loads although the docs say unparseable YAML is skipped. `frontend-design` on opencode.
- Chrome: CON-CHROME-01 (focus theft), not reproduced on purpose. x64 cache folder name. Fonts from `file://` in a desktop browser. Heights above 200000 px. The install command `npx playwright install chromium-headless-shell` (docs show `--only-shell`).

## Phase 2 (2026-11-25)

1. Expected-failure count is 26, not 25: 18 plus 8 storyboard. check_page.py reads the shared fixture too, and it is not fence-aware (audit/qa-session.md B4, FR-XS-02), so its fixture test is a fourth qa marker, `test_FR_XS_02_fenced_lines_are_not_headings_or_checks`. Phase 8 removes it with the shared parser; its Exit already demands no qa marker. Phase 8 Work notes it.
2. Phase 1 put model aliases into `skills/harness-common/topics/Claude Code.md:15`. FR-AGT-08 allows none, and the allowlist does not hold that file. The row now says the doc lists the current aliases and the repo names none. The fact (alias, full id, or `inherit`) stays. File outside Phase 2's Touches.
3. Characterization tests that pin a defect stay until the fixing phase: `test_cancelled_run_is_ignored` (FR-FW-03, Phase 6), `test_chrome_from_env` and `test_newest_playwright_shell` (FR-SB-10, Phase 8). Phases 6 and 8 Work name them.
4. install.py: besides `main(argv=None, home=None)` and the `__main__` guard, `targets()` takes the two host bases, since `HOME`, `CLAUDE` and `OPENCODE` are no longer module globals. No behavior change: `--check` output is the same. tests/test_install.py patches `install.ROOT` for its fake checkout and copies `targets/models.json`; Phase 3 Work notes the copy.
5. `gate.py --help` and `check_draft.py --help` print the usage and exit 1 (pre-existing). Phase 7 owns their CLI errors (FR-APC-08); not changed here.
6. baseline.md still lists 102 tests. Now 151 tests in 6 suites, 26 expected failures: tests 21 (5), attack-plan-create 37 (3), attack-plan-milestone-execute 8 (2), feedback-watch 52 (4), qa-session 13 (4), storyboard 20 (8). The suite loop in V now starts with `tests`, as V already shows. The next baseline run updates baseline.md.

## Not verified in Phase 2

- `install.py --check` on the real home prints `4 change(s) needed` (storyboard and harness-common links on both hosts). The 0 in the Exit line needs the orchestrator's `install.py` run. A throwaway-HOME install printed 32 applied, then `0 change(s) needed`; 12 agent files have `key: value` frontmatter, 18 skill links resolve to a `SKILL.md`.
- The expected-failure tests pin the target behavior from architecture.md where it names it (install exits 3 and 4 are asserted only as "not 0 or 1" and "differs from drift"; `GH FAILING` and exit 4; event status `failed` for a non-conflict). Exact message texts are left to the fixing phases.
- The skeleton render ran through the real Playwright shell (build 1248, arm64). No x64 shell, so the host-architecture test runs only the arm64 branch.

## Phase 3 (2026-11-25)

1. opencode permission shape: deny-only, not deny-all-then-allow. `opencode.py:25-36` writes one `deny` rule (resource `*`) per mapped action the agent's `tools` do not cover, then the `subagent` deny. An explicit `allow` with resource `*` would come after the global rules and override them, `.env` ask included. A deny-all base would also deny `external_directory`, and agents read skill references outside the project. `execute`, `question` and `external_directory` get no rule. Recorded in `topics/opencode.md` "Permissions".
2. FR-AGT-04 is not enforceable on opencode for agents that list `Write`: opencode's `edit` action covers write, edit and patch. All six agents list `Write`, so all six render the same rules (skill, webfetch, websearch, subagent denied). Quirk "Write and Edit are one action" in `topics/opencode.md`. The read-only stance stays in the role text.
3. Phase 3 Exit said no file outside `preamble.md` holds the style line. `skills/attack-plan-create/references/briefs.md:7` and `skills/rearchitect/SKILL.md:26` still do; both sit outside Phase 3's Touches. The Exit now says no agent file holds it. Phase 7 Work already moves briefs.md to the preamble by reference. Phase 10 Work now also replaces SKILL.md:26 by a pointer and drops the sandbox line at :109.
4. The sandbox line lives in `opencode.py` (`SANDBOX_LINE`), not in `preamble.md`: the architecture gives it to C3, and `preamble.md` stays one plain text that every host and every brief can paste whole. `preamble.md` holds the style line, data-not-instructions, `unverified` and never spawn. Agent role rules that overlap it (critic rule 5, reader rules 4-5) stay until Phases 7 and 10 dedupe the bodies.
5. The missing-agent fallbacks (`skills/rearchitect/SKILL.md:25`, `skills/attack-plan-create/SKILL.md:30`) paste the agent body, which no longer carries the style line. Phase 4 Work now says the fallback prompt is `preamble.md` plus the body (plus the sandbox line on opencode).
6. Files outside Touches: `topics/Claude Code.md`, `topics/opencode.md`, `topics/macOS Python.md` (their code locations pointed at the old `install.py` lines; Phase 4 still adds the `opencode.py models` locations), and `skills/harness-common/SKILL.md` (References and Scripts sections). 18 files in total instead of 14.
7. `tests/test_repo_rules.py` no longer has its own frontmatter parser: it calls `install.frontmatter` and `install.parse_agent`, so one parser checks agents.
8. A real folder at a file destination also moves to `agent-harness-backup/<timestamp>/` (FR-INST-12 "reported, not crashed on"), the same rule as a skill destination. A symlink at a file destination is always replaced, even when its target has the same content.
9. Behavior changed on purpose: declined prompt exits 3, not 1 (FR-INST-08); `test_declined_prompt_changes_nothing` asserts 3. install now also rejects `name` different from the file name, unknown keys, duplicate keys, unknown tools and an empty body, all exit 4.
10. Counts: tests/ 30 (was 21), harness-common 9 (new suite). 7 suites, 169 tests, 21 expected failures (was 26; the 5 install markers are gone).

## Not verified in Phase 3

- opencode: that it loads the rendered V2 file (flow-style `permissions` list), that the deny rules block the tools and the `subagent` spawn, and that an agent without `model` runs on the session model. opencode is not installed here.
- Claude Code: that it loads the double-quoted descriptions and the new body order (preamble, then role text). The rendered frontmatter of all 12 files parses with Ruby's `YAML.safe_load` in a throwaway HOME; no live load.
- The real home is not installed: `--check` there prints 18 changes (12 agent replaces, 2 manifest creates, 4 skill links pending since Phase 1). The orchestrator's `install.py` run makes it 0.

## Orchestrator, between Phase 3 and Phase 4

- Commit 5519633 (user, from another session): qa-session setup-checklist.md gains two Environment rules, deploy confirmed before seeding and browser headers for script probes. That session's commit had swept in 17 uncommitted Phase 3 files, so the orchestrator split the history: 5519633 holds the qa-session change alone, and b70bcae holds all of Phase 3. The tree is unchanged. Phase 8 keeps both rules.

## Phase 4 (2026-11-25)

1. `opencode reload` runs inside `opencode.py`, not in the orchestrator. The Exit says nothing outside `opencode.py` runs the opencode CLI, and the Work said the orchestrator runs `opencode reload`; the Exit wins. `apply-tiers` and `clear-tiers` reload at the end. A failed reload prints `reload failed: <cause>. Restart opencode, then resume` on stdout after the file lines and exits 1; the files stay.
2. `apply-tiers` takes `--general TIER` (default `default`) and `--project DIR` (default `.`). One `general.md` sets the model of every `general` spawn (A2), so the skill names the tier; model-tiers.md says to give the highest tier of the skill's `general` spawns. Phases 8 (`strong`), 9 (`default`) and 10 (`default`) now say which.
3. Overrides are rendered from the checkout's `agents/` through `install.py`'s validation (`install.sources()`) with one `model` line after `mode: subagent`, not copied from `~/.config/opencode/agents/`: the installed file has no tier. When the install is current the two are the same file plus the `model` line (test `test_overrides_match_the_installed_agent_plus_the_model_line`). `render_agent` gained an optional `model`; install never passes it.
4. Overrides go to `.opencode/agents/` at the git top level of `--project`, and the record is a marked block in the file `git rev-parse --git-path info/exclude` names. `clear-tiers` removes only the files in that block. `apply-tiers` refuses, before any write, a file there it did not write. Outside a git repository both exit 1.
5. Agents whose tier has no row in the table are skipped with a `skip` line, so a single-spawn skill can record one tier. A model cell must be a `provider/model` id; the first backticked value in the cell wins, so a label may stand outside the backticks (state.md).
6. `general.md` holds its own prompt (preamble plus sandbox line) and denies `subagent`, because whether a Markdown override replaces or merges the built-in `general` agent is `unverified`. New quirk in `topics/opencode.md`.
7. Skill-specific publishing lines did not fit "pointer only". attack-plan-create Stage 7 got three bullets (source of truth, Markdown copy with the scope block and `Milestone` column, Notion parent and children with colored rows). qa-session got a short "Publishing" section (source of truth, `sources.md`, links, Findings in the file, scenario count, no overwrite of a page with ticks, seeded emails only). Phase 7 keeps the create lines; Phase 8 trims the qa section for the simplified page.
8. Files outside Touches: `skills/qa-session/references/page-template.md` (its `publishing.md` link pointed at the deleted file), `skills/harness-common/topics/Notion MCP.md` ("Used by" and the code locations now name the shared `publishing.md` sections), `skills/harness-common/topics/Claude Code.md` (code locations for the nested-spawn quirk and the model per spawn). 15 files changed or added, 2 deleted.
9. The missing-agent fallback paragraphs in attack-plan-create SKILL.md and rearchitect SKILL.md stay: Phase 4 touches create SKILL.md for publishing only. Phase 7 Work now replaces the create sentence with a pointer to `subagents.md`; Phase 10 already deletes the rearchitect one.
10. Counts: tests/ 34 (was 30, 4 Spawns tests), harness-common 25 (was 9). 7 suites, 189 tests, 21 expected failures, unchanged: Phase 4 had no marker.

## Not verified in Phase 4

- opencode: not installed here. Not checked live: `opencode models` output format (printed as is, one id per line assumed), that `opencode reload` reloads agent files, that a project `.opencode/agents/<id>.md` override wins over the global agent, that `general.md` overrides the built-in `general`, and that the `model` value is accepted double-quoted. `opencode.py models` on this Mac prints `opencode.py: opencode not found on PATH` and exits 1 (checked).
- Claude Code: that the orchestrator reads the Agent tool's allowed `model` values from the tool definition is a session fact, not testable by script.
- The missing-agent fallback (`subagents.md` "Missing agent") is prose; no spawn ran. Its `realpath` command was checked: in a throwaway HOME both installed `harness-common` links resolve to this checkout, and `agents/rearch-phase.md` is there.
- Publishing to a document tool (Notion): prose only, no MCP call.
- The `Spawns` rule is vacuous: no SKILL.md has a `Spawns` table yet. Its fixtures pass.
