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
