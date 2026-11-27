# Architecture

How agent-harness is built: modules, data flow, interfaces. Requirement IDs refer to [requirements.md](requirements.md).

## Decisions in one place

- `skills/harness-common/` holds everything two or more skills share: Python adapters and the Markdown parser (`scripts/`), runtime conventions (`references/`) and the facts about external systems (`topics/`). It is installed like every other skill: only skill folders reach a running session, and sibling skill folders stay siblings in the checkout and under both tools' `skills/`, so `../harness-common/...` resolves everywhere.
- Scripts import the shared code with one bootstrap line: `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness-common" / "scripts"))`. `-I` drops the script's folder from `sys.path`, and `resolve()` follows the skill link into the checkout ([macOS Python](<../skills/harness-common/topics/macOS Python.md>)).
- The checkout root is also a Claude Code plugin. Agents need rendering (the preamble, a quoted description, no `tier`), and the manifest's `agents` key replaces the `agents/` scan, so it names generated files in `build/agents/` rather than the sources; the neutral sources stay the one copy (FR-PLG-01, -03). Skills keep bare agent names; the orchestrator resolves each to the listed name, bare or `harness:`-prefixed, at spawn time (FR-PLG-04).
- No model name or id in the repo. Tiers are resolved per run through `harness-common/references/model-tiers.md`, the one place every tiered spawn goes through (FR-AGT-07, -08).
- Two layers. Only the orchestrator session spawns. A skill that uses another skill (execute uses qa-session and feedback-watch) runs it in the orchestrator, never in a subagent. Installed agents get no spawn tool on either host (NFR-13).
- External skills the repo does not ship (`frontend-design`, REA) are named "when available", and each skill that names one says what to do without it.
- One fact in one place. The agent preamble lives in `references/preamble.md` and install puts it above every agent. External facts live in one topic doc each, conventions in one reference each (NFR-09).

## Overview

```
                user
                 |
   +-------------v--------------+        install.py (once per change)
   | orchestrator session       |        |  reads agents/, instructions/,
   | (Claude Code or opencode)  |        |  harness-common/references/preamble.md
   |  loads skills by trigger   |        |  uses claude_code.py, opencode.py
   +--+-----------+---------+---+        v
      |           |         |        ~/.claude/{agents,skills,CLAUDE.md}
      | spawn     | runs    | reads  ~/.config/opencode/{agents,skills,AGENTS.md}
      | (1 layer) | CLI     |
      v           v         v
  subagents   skill scripts ------> harness-common/scripts
  (agents/*.md  gate.py               markdown.py   (pure)
   or general)  check_draft.py        github.py ----> gh CLI -> GitHub API
      |         check_page.py         git.py -------> git
      | no      watch.py              claude_code.py  (render, paths)
      | spawn   build_integration_    opencode.py ---> opencode CLI
      v         branch.py
   files in     review_threads.py
   run state    shoot.py ---------> chrome-headless-shell (no window)
                ledger.py --------> .ai-notes/<area>/open-items.md
   (.rearch/, .attack-plan/<slug>/, .ai-notes/<area>/, prototype/*-storyboard.html)
```

Document tools (Notion and others) are reached through the host's MCP tools by the orchestrator. No script talks to them. Their quirks live in [Notion MCP](<../skills/harness-common/topics/Notion MCP.md>).

## Modules

27 modules, 14 code and 13 prompt, one responsibility each.

### Code

| # | Module | Responsibility |
|---|---|---|
| C1 | `install.py` | Read and validate agent sources, plan writes, links and prunes, confirm, apply with backup, keep a manifest. Planning is pure and separate from the apply step. `--plugin` plans and applies only the plugin's rendered agents in `build/agents/`. |
| C2 | `skills/harness-common/scripts/claude_code.py` | Claude Code adapter: install paths, agent rendering (quoted `description`, `tools` without any spawn tool, no `model` line). |
| C3 | `skills/harness-common/scripts/opencode.py` | opencode adapter: install paths, agent rendering (`mode: subagent`, V2 `permissions` from `tools` with the `subagent` action denied, the `execute` sandbox line), model listing, and the per-run tier overrides (`apply-tiers`, `clear-tiers`). |
| C4 | `skills/harness-common/scripts/github.py` | GitHub adapter over `gh`: one runner, `GhError`, one paginated GraphQL PR snapshot, one thread by id, reply to a thread, resolve a thread. |
| C5 | `skills/harness-common/scripts/git.py` | git adapter: runner, `GitError` and `Conflict`, version gate, identity check, remote branch existence by `ls-remote`, fetch with explicit refspecs, merge-tree, commit-tree, ancestor test, plain push. |
| C6 | `skills/harness-common/scripts/markdown.py` | Pure Markdown structure: fence mask, ATX headings outside fences, section ranges by heading, SHA-256 over one or more (file, heading) pairs. |
| C7 | `skills/feedback-watch/scripts/watch.py` | Pure PR-state and done rules plus the two poll loops (`pr`, `local`). GitHub only through C4. |
| C8 | `skills/attack-plan-create/scripts/gate.py` | Gate state machine over `gates.json`: open, grilled, approve, skip, reopen, status, verify. Hashing through C6. |
| C9 | `skills/attack-plan-create/scripts/check_draft.py` | Plan checks (`<draft folder>`, `--product`) and the task-block schema check (`--tasks`), shared with execute. Headings through C6. |
| C10 | `skills/attack-plan-milestone-execute/scripts/build_integration_branch.py` | Merge heads into a target without a checkout, skip heads already in it, tell conflicts from failures, push a plain fast-forward on request. git through C5. |
| C11 | `skills/attack-plan-milestone-execute/scripts/review_threads.py` | `list` the unresolved threads of a PR set with who started them (bot or human); `resolve` and `reply` only on threads a bot started. GitHub through C4. |
| C12 | `skills/qa-session/scripts/check_page.py` | The mechanical rules of the QA page. Headings and fences through C6. |
| C13 | `skills/storyboard/scripts/shoot.py` | Chrome headless shell adapter and screenshot CLI: find the shell (never a browser app), dump the DOM for `data-h`, shoot each theme. Pure parts (`find_chrome`, `page_url`, `shot_height`) apart from the subprocess calls. It stays in storyboard until a second skill needs a browser. |

| C14 | `skills/open-items/scripts/ledger.py` | The ledger's version 1 grammar: parse and check, the next free id, the reply's block, pruning closed lines, an empty ledger. Pure functions (`parse`, `next_id`, `block`, `prune`) under a thin CLI; reads prose nowhere. |

### Prompt

| # | Module | Responsibility |
|---|---|---|
| P1 | `skills/harness-common/` (SKILL.md, `references/`, `topics/`) | Shared conventions: `preamble.md` (agent and brief preamble), `subagents.md` (brief minimum, two layers, missing-agent fallback), `model-tiers.md` (tier gate and per-host spawn), `state.md` (resume-file minimum), `publishing.md` (one publishing procedure). `topics/`: one doc per external system. |
| P2 | `instructions/global.md` | Global rules for both hosts, deduplicated, tool-neutral. |
| P3 | `agents/*.md` | Six agent role bodies in the neutral format (`name`, `description`, `tier`, `tools`). No preamble copies. |
| P4 | `skills/ai-notes/` | Notes convention on top of `state.md`, handoff to a new session. |
| P5 | `skills/writing-craft/` | Rules for human-read text. Agent-to-agent text is exempt by name. |
| P6 | `skills/feedback-watch/` | How to arm and read C7 on each host, and how to read a CI failure. |
| P7 | `skills/attack-plan-create/` | Plan-writing procedure, briefs, templates, work-folder layout. |
| P8 | `skills/attack-plan-milestone-execute/` | Milestone execution, input readiness, review pass, PR subagent rules. |
| P9 | `skills/qa-session/` | QA page procedure, briefs, page template, setup checklist. |
| P10 | `skills/rearchitect/` | Rearchitect stages, state formats, docs style. |
| P11 | `skills/storyboard/` (SKILL.md, `references/brief.md`, `page.md`, `skeleton.html`) | Storyboard procedure: frame, one Builder spawn (`general`, `strong`), check with C13, hand over, record the decisions in the requirements doc. No resume file of its own. Commits only when the user asks. |
| P12 | `skills/handoff/` | The `/handoff [notes]` entry point: a pointer to the P4 handoff steps plus the user's notes (`$ARGUMENTS`). No steps of its own. |
| P13 | `skills/open-items/` (SKILL.md, `references/format.md`) | The every-turn rules for the ledger, what earns an item (follow-ups only when nothing else brings them back), answering in prose, the block from C14, shown only when the user asks, subagents and review items, new sessions and handoffs, the line between the ledger and the host's task tools. |

## Model tiers

Tiers: `fast`, `default`, `strong`. Agents declare one in `agents/*.md`. Each skill that spawns lists every spawn and its tier in a `Spawns` table (agent or `general`, tier, used for). `tests/test_repo_rules.py` checks that each named agent exists with that tier, and that every skill that names an agent, `general-purpose` or `model-tiers.md` has the table.

The procedure lives only in `harness-common/references/model-tiers.md`:

1. When a run starts or resumes and its resume file has no confirmed `Models for this run` table, the orchestrator lists the models the host offers. Claude Code: the allowed values of the Agent tool's `model` parameter, from the tool definition in the session. opencode: `opencode.py models`, which runs `opencode models`.
2. It proposes one model per tier (fast = cheapest that fits, strong = most capable, default = the session model) and asks the user to confirm. This is a gate. The user may override any tier or put every tier on one model.
3. It writes the table into the run's resume file (`state.md`).
4. Every spawn passes its tier's model. Claude Code: the Agent tool's `model` parameter, for named agents and `general-purpose` alike. opencode: the `subagent` tool takes no model, so `opencode.py apply-tiers --state <resume file> [--general TIER] [--project DIR]` writes one `.opencode/agents/<id>.md` per tiered agent at the project's git top level, a full copy with the tier's `model` line, plus one `general.md` for every `general` spawn. The paths go into a marked block of `.git/info/exclude`, and `opencode reload` runs. `clear-tiers` removes exactly those files and reloads. A failed reload prints `reload failed: <cause>. Restart opencode, then resume`.

## Data flow

- Install: `agents/*.md` and `preamble.md` -> C1 validates -> C2 and C3 render -> plan (write, link, prune, backup) -> `--check` prints the plan, or apply after confirmation -> `<host config>/agent-harness-manifest.json` lists what C1 owns, so a later run can prune it. Links into the checkout are also pruned when their target is gone. Links pointing elsewhere are never touched.
- Plugin: `agents/*.md` and `preamble.md` -> C1 validates and checks the `agents` list of `.claude-plugin/plugin.json` -> C2 renders -> `build/agents/` (gitignored). A host loads the checkout root as a plugin: skills straight from `skills/`, agents from `build/agents/`. One source: the rendered files are generated, and the manifest's list is checked against `agents/` by C1 and by a repo test (FR-PLG-03).
- Plan to code: attack-plan-create writes drafts under `.attack-plan/<slug>/draft/`. Task blocks follow the schema in `references/executable-plan.md`, checked by `check_draft.py --tasks`. Execute gates its input on `gate.py status` when `gates.json` exists, else grades by hand, then runs `check_draft.py --tasks --milestone <n>`. Each block's "Context for an outside reviewer" opens its PR description.
- CI and review: after a push the orchestrator arms feedback-watch (C7) with `--until bots`. C7 polls C4 snapshots and prints change lines. In the review pass, `review_threads.py list` feeds the FIX/REPLY table. A pushed FIX on a bot thread is closed with `review_threads.py resolve`; a bot thread decided REPLY gets its text posted and the thread resolved with `review_threads.py reply`. Human threads go to the user, with the fix commit or the reply text (FR-APE-15).
- QA: execute Step 9 runs the qa-session skill in the orchestrator. qa-session spawns Builder and Verifier (`general`, `strong`), runs C12 and publishes through `publishing.md`.
- Rearchitect: run state in `.rearch/`, one `rearch-phase` per phase, models table in `.rearch/baseline.md`. Stage 6 moves the requirements and the architecture into `docs/` and deletes `.rearch/`.
- Storyboard: the orchestrator frames the question, runs the tier gate (or reads the table from the work's ai-notes area), spawns one background Builder with the filled brief. The Builder writes `<project>/prototype/<topic>-storyboard.html` and runs C13. The orchestrator runs C13 again, reads the page cold, hands over and stops. Decisions go into the project's requirements doc. Screenshots stay in `<tmp>/storyboard-shots/`. Nothing is committed unless the user asks.

- Open items: each turn the orchestrator reads `.ai-notes/<area>/open-items.md`, applies the user's answers and its own work to it, runs `ledger.py check`, then ends the reply with `ledger.py block`. Subagents never write it: briefs carry the owned ids (`subagents.md`), reports carry `Closed:` lines and questions, and the orchestrator records them. ai-notes READMEs and handoffs link the ledger instead of listing pending items; execute and qa-session keep their pending items there. Synopia, when it runs the session, reads and writes the same file between turns.

## Process model

- No real-time paths and no threads. Every script is a synchronous, single-process CLI.
- The orchestrator never blocks on a long job. `watch.py` runs under Claude Code's Monitor tool or as an opencode background shell job. Its stdout is the only channel: every terminal condition prints a line.
- `watch.py local` gives every command a timeout and has an overall `--timeout`. It takes the file snapshot after the commands finish, so files they write do not retrigger them.
- Subagents run in parallel only when the orchestrator launches them in one batch. Claude agents: `tools` never lists `Agent` or `Task`, and install rejects an agent file that does. opencode agents: the `subagent` action is denied in the rendered `permissions`.
- `shoot.py` runs Chrome in sequence: per theme one dump and one screenshot, each under a 120 s timeout and a 3000 ms virtual-time budget. No Chrome run opens a window.
- Load: pr mode every 120 s by default, one GraphQL call per PR per round plus one per further page of 100. Local mode a 2 s poll and a 1 s debounce.

## Interfaces

### Shared Python (harness-common/scripts)

- `markdown`: `split(text)`, `fence_mask(lines) -> [bool]`, `headings(lines) -> [(index, level, title)]` (ATX outside fences), `section(lines, title) -> (start, end) | None` (ends at the next heading of the same or a higher level), `part(path, heading=None)`, `digest(pairs) -> str` over `[(path, heading or None)]`, `legacy_digest(path, heading=None)` for the older gate format. Raises `Missing` naming the file or section.
- `github`: `run(args, timeout=60)`; `Gh(runner=run)` with `.graphql(query, **variables)`, `.repo() -> "OWNER/NAME"`, `.pr_snapshot(repo, number) -> {state, head, rollup, reviews: [{login, is_bot, state, commit}], threads: [{id, url, resolved, path, line, login, is_bot, body}]}` with every page read, `.thread(id)` (one thread plus `pr`), `.reply_to_thread(id, body) -> comment URL`, `.resolve_thread(id) -> bool`. Raises `GhError` with one line.
- `git`: `run(args, cwd=".", timeout=300)`, `cause(text)`; `Git(cwd=".", runner=run)` with `.call`, `.out`, `.version()`, `.require(major, minor)`, `.require_identity()`, `.remote_has(remote, branch) -> bool`, `.default_branch(remote)`, `.fetch(remote, *branches)`, `.rev(ref)`, `.tree_of(rev)`, `.is_ancestor(a, b)`, `.merge_tree(a, b) -> tree`, `.commit_tree(tree, parents, message) -> sha`, `.push(remote, commit, branch)` (never forced). Raises `GitError` with one line, or `Conflict(files, messages, head=None)`; a `Conflict` is not a `GitError`.
- `claude_code`: `paths(home)`, `render_agent(meta, body, preamble) -> str`.
- `opencode`: `paths(home)`, `permissions(tools)`, `render_agent(meta, body, preamble, model=None) -> str`, `render_general(preamble, model)`, `list_models(runner=run)`, `tier_models(text, tiers)` (reads the `Models for this run` table), `apply_tiers(...)`, `clear_tiers(...)`. Raises `Failed` with one line.

### CLIs

Every script runs as `/usr/bin/python3 -I <path>`. The owning `SKILL.md` documents each line in full.

| Script | Signature | Output | Exit |
|---|---|---|---|
| install.py | `[--check] [--claude 0\|1] [--opencode 0\|1] [--yes]`, or `--plugin [--check]` | one line per planned item (`create`, `replace`, `backup`, `remove`), a summary line | 0 done or clean, 1 drift with `--check`, 2 needs `--yes` without a terminal, 3 declined, 4 invalid source (file and key named) |
| watch.py pr | `N... [--repo OWNER/NAME] [--reviewer LOGIN]... [--interval S] [--until all\|ci\|bots] [--timeout MIN] [--allow-no-checks] [--once]` | `#N <sha> \| CI running\|done \| failing: ... \| reviewed\|waiting for review: ... \| unresolved threads: N (human M)`, `#N merged\|closed, stopped watching`; `skipped #N this round: <cause>` on stderr; last line `ALL DONE`, `CI DONE`, `BOTS DONE`, `NOT DONE`, `TIMEOUT` or `GH FAILING: <cause>` | 0, 1 not done, 2 bad arguments, 3 timeout, 4 gh failing |
| watch.py local | `--cmd C... [--path P]... [--interval 2] [--debounce 1] [--cmd-timeout 600] [--timeout MIN] [--once]` | `PASS <cmd>`, `FAIL <cmd> (exit N)` or `(timed out)` with the last 15 lines; with `--once` last line `ALL PASS` or `FAILED: <cmds>`; `TIMEOUT` | 0, 1, 2 bad arguments, 3 timeout |
| gate.py | `open <work> <stage> <section> [--file F [--heading H]]...`, `grilled <work> <section> --rounds N --open-findings N`, `approve <work> <section> --by NAME`, `skip`, `reopen <work> <section> --reason TEXT`, `status <work>`, `verify <work>` | status table on stdout, `REFUSED: <reason>` on stderr | 0, 1 refused or verify problems, 2 bad command line |
| check_draft.py | `<draft folder> [--product]`, `--tasks <file> [--milestone N]` | `PASS\|WARN\|FAIL file: message`; `check_draft.py: <cause>` on stderr for a bad command line | 0, 1 a FAIL or a bad command line |
| check_page.py | `<page.md> [-v] [--live]` | one summary line; `line N LEVEL message` per finding under `-v` | 0, 1 a FAIL |
| build_integration_branch.py | `--target B --heads A,B [--from target\|<branch>] [--default B] [--message T] [--push] [--repo P] [--remote R]` | progress lines, `skipped <head>: already in <sha>`, last line `INTEGRATION_BRANCH_EVENT {json}` with `status` `pushed\|built\|unchanged\|conflict\|failed` | 0 pushed, built or unchanged; 1 conflict or failed |
| review_threads.py | `list --pr N... [--repo OWNER/NAME]`, `resolve --thread ID...`, `reply --thread ID --body-file FILE\|-` | `list`: `#<pr> <id> bot\|human <login> <path>[:<line>] <url> \| <first line>`, then `<n> unresolved: <b> bot, <h> human`. `resolve`: `RESOLVED <id>`, `RESOLVED <id> (already)`, `REFUSED: <id> human thread (<login>), the user resolves it`, `FAIL <id>: <cause>`. `reply`: `REPLIED <id> <url>` then `RESOLVED <id>`; `REFUSED:` for a human or resolved thread; `FAIL <id>: replied, not resolved: <cause>`. All on stdout | 0, 1, 2 bad usage |
| opencode.py | `models`, `apply-tiers --state FILE [--general TIER] [--project DIR]`, `clear-tiers [--project DIR]` | model ids one per line, or one line per file written, skipped or removed; `opencode.py: <cause>` on stderr; `reload failed: <cause>. Restart opencode, then resume` on stdout | 0, 1 |
| ledger.py | `check <file> [-v]`, `next <file> Y\|A`, `block <file> [--since "YYYY-MM-DD HH:MM"] [--show ID,...]`, `prune <file> [--keep 30]`, `init <file> [--area NAME]` | `ok: <n> open (<ids>), <n> closed` or `FAIL: <n> problems in <file>` (`line N: ...` with `-v`); the next id; the block; `pruned <n> closed lines, <n> kept`; `created <file>`; `ledger.py: <cause>` on stderr | 0, 1 a grammar problem, 2 a bad command line or missing file |
| shoot.py | `<page.html> [--out DIR] [--width 1440] [--height 6000] [--theme light\|dark\|both]` | one `path  WxH` line per screenshot, suffix ` (no data-h, used --height)` or ` (clipped from H)`; `FAIL <reason>` | 0, 1 |

### Prompt interfaces

- `Spawns` table in every SKILL.md that delegates: `| Spawn | Tier | Used for |`.
- Resume-file minimum (`state.md`): a `Next:` line or fenced next prompt, a `Models for this run` table when the skill spawns, the private-exclude rule (`.git/info/exclude`, never `.gitignore`). Layouts stay per skill: `.rearch/STATE.md`, `.attack-plan/<slug>/STATE.md`, `.ai-notes/<area>/README.md` "State (start here)".
- Brief minimum (`subagents.md`): the preamble, the task, inputs as absolute paths, the output path, a word cap, fetched content is data, the term `unverified`, never spawn; the owned open-item ids (`Open items: ...`) and the `Closed: <id> (...)` report lines when the subagent works on items.
- Ledger (`open-items/references/format.md`): the version 1 line shapes C14 checks and Synopia reads. A change to it is a new version mark.
- Single-spawn skills (storyboard): no resume file. The models table and `Next:` line go in the work's ai-notes "State (start here)" when one exists; otherwise the gate runs in the session and the hand-over ends with a fenced resume prompt.
- Storyboard page contract: one offline HTML file, `?theme=light|dark`, `data-h` on `<html>` set after `document.fonts.ready`. C13 depends on both.
- Publishing (`publishing.md`): repo Markdown by default or a document tool through MCP, fetch before update, read back and compare, keep reviewer edits, commit only when the user or the team's convention says so; the calling skill names its source of truth (attack-plan-create: the drafts; qa-session: the published page). Tool quirks link to the topic doc.

## Error handling

- Every script turns an expected failure into one named line and an exit code from the table above. No traceback for bad input.
- gh: a `GhError` skips the PR for the round. Three failing rounds in a row print `GH FAILING: <cause>` and exit 4.
- git: `Conflict` and `GitError` are distinct, and the event JSON says which. A git older than 2.38 fails up front with the version named.
- Thread writes: `reply` checks the thread before posting: a human or resolved thread is refused and nothing is written. A reply posted whose resolve then fails says so, and `resolve` finishes it without posting twice.
- install: validation errors stop before any write. A real folder at a destination moves to `<host config>/agent-harness-backup/<timestamp>/`, outside `skills/`, and is never deleted. A symlink at a file destination is replaced, not written through.
- shoot.py: no shell, a missing page, a non-executable `$CHROME`, a timeout, a failed dump or screenshot each print one `FAIL <reason>` line (the last stderr line as text) and exit 1.
- Prompt level: a denied command is reported to the user, never worked around.

## External-system adapters

| System | Code adapter | Topic doc |
|---|---|---|
| Claude Code | `claude_code.py` | [Claude Code](<../skills/harness-common/topics/Claude Code.md>) |
| opencode | `opencode.py` | [opencode](../skills/harness-common/topics/opencode.md) |
| GitHub (gh, REST, GraphQL, Actions) | `github.py` | [GitHub](../skills/harness-common/topics/GitHub.md) |
| git | `git.py` | [git](../skills/harness-common/topics/git.md) |
| Notion MCP | none (prompt only, through `publishing.md`) | [Notion MCP](<../skills/harness-common/topics/Notion MCP.md>) |
| macOS system Python | the bootstrap line in each script | [macOS Python](<../skills/harness-common/topics/macOS Python.md>) |
| Chrome headless shell (Playwright cache) | `skills/storyboard/scripts/shoot.py` | [Chrome headless shell](<../skills/harness-common/topics/Chrome headless shell.md>) |
| `frontend-design` (Claude Code plugin) | none, named "when available" in P2 and P11 | [Claude Code](<../skills/harness-common/topics/Claude Code.md>) "Other plugins" |

## Requirement to module traceability

| Requirement | Module |
|---|---|
| FR-INST-01..14 | C1, C2, C3 |
| FR-PLG-01 | `.claude-plugin/plugin.json`, C1 |
| FR-PLG-02 | P1 `SKILL.md` frontmatter |
| FR-PLG-03 | C1 `plan_plugin`, C2 |
| FR-PLG-04 | P1 `subagents.md` "Agent names" |
| FR-AGT-01, -03 | P3, C1 validation |
| FR-AGT-02 | C1, C2, C3 |
| FR-AGT-04 | C2 `tools`, C3 permission map |
| FR-AGT-05 | P1 `subagents.md` |
| FR-AGT-06 | P1 `preamble.md`, C3 sandbox line |
| FR-AGT-07 | P1 `model-tiers.md`, C3; `Spawns` tables in P7, P8, P9, P10, P11 |
| FR-AGT-08 | `tests/test_repo_rules.py` over every tracked or untracked, non-ignored file |
| FR-GLB-01..14 | P2 (installed by C1) |
| FR-NOTES-01..08 | P4 |
| FR-NOTES-09 | P12 (steps in P4) |
| FR-WRIT-01..07 | P5; citations in P7, P8, P9, P11 |
| FR-APC-01..04, -06..-17, -20 | P7, C8, C9 |
| FR-APC-05 | C8 on C6 |
| FR-APC-14 | P1 `publishing.md`, P7 |
| FR-APE-01..07, -10..-14 | P8 |
| FR-APE-08 | C10 on C5 |
| FR-APE-09, -15 | P8 review pass, C11 on C4 |
| FR-FW-01..13 | C7 on C4 |
| FR-FW-14, -15 | P6 |
| FR-QA-01..08, -10..-15 | P9 |
| FR-QA-09 | C12 on C6 |
| FR-RA-01..14 | P10, P3 rearch agents |
| FR-XS-01 | P1 `preamble.md`, `subagents.md`; every brief |
| FR-XS-02 | C6 in C8, C9 and C12 |
| FR-XS-03 | P1 `state.md`; each skill |
| FR-XS-04 | P1 `publishing.md` |
| FR-XS-05 | each script's SKILL.md and docstring |
| FR-SB-01..08, -13..-16 | P11 (with P1 `model-tiers.md`, `subagents.md`, `state.md`) |
| FR-SB-09..12 | C13 |
| FR-OI-01, -06..-10 | P13, P2 (the global line), P1 `subagents.md`, P4, P8, P9 |
| FR-OI-02..05 | C14 |
| NFR-01, -02 | every script; git 2.38 stated in P8 and README |
| NFR-03 | every script |
| NFR-04 | `tests/`, `skills/*/tests/` |
| NFR-05 | `.gitignore` |
| NFR-06, -07, -08 | C1, README |
| NFR-09 | P1 single sources; every prompt module |
| NFR-10 | P1 `subagents.md` word caps, P10 |
| NFR-11 | C7 |
| NFR-12 | C7 (read-only), C10 (`--push`), C11 (bot threads only) |
| NFR-13 | P1 `subagents.md`, `preamble.md`; C1 rejects spawn tools; C3 denies the `subagent` action |
| NFR-14, -15 | C13 |
| CON-* | topic docs |

## Tests

| Suite | Covers |
|---|---|
| `tests/` | `install.py` against a throwaway home, `--plugin` against a fake checkout; repo rules: the plugin manifest, no model names, ignored caches, one `SKILL.md` per skill folder, well-formed agents, `Spawns` tables |
| `skills/harness-common/tests/` | C2, C3, C4, C5, C6 (fake runners, temp git repositories) |
| `skills/attack-plan-create/tests/` | C8, C9 |
| `skills/attack-plan-milestone-execute/tests/` | C10 on temp repositories, C11 with a fake `gh`, the skill text rules |
| `skills/feedback-watch/tests/` | C7 with fake snapshots and commands |
| `skills/qa-session/tests/` | C12 |
| `skills/open-items/tests/` | C14: the grammar on invented ledgers, the format page's example, ids and pruning, the block, and the block shown in P13 |
| `skills/storyboard/tests/` | C13 with a fake Chrome; the skeleton through the real shell when one is installed |
