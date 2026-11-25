---
name: harness-common
description: Shared library of the agent-harness skills, never invoked on its own. Load a file from it only when another harness skill links to it. It holds the shared conventions (subagents, model tiers, run state, publishing) and the facts about the external systems the skills use (Claude Code, opencode, GitHub, git, Notion MCP, macOS Python, Chrome headless shell).
---

# harness-common

Other harness skills link here. Read the one file the link names, not the whole folder.

## Topics

One doc per external system. Each fact has a source: a code location, a test, a scripted check or a vendor doc. A fact without one says `unverified`.

| Topic | Covers |
|---|---|
| [Claude Code](<topics/Claude Code.md>) | Agent files and `tools`, the spawn `model` parameter, nested spawns, Monitor, skills and `CLAUDE.md` paths, plugin skills |
| [opencode](topics/opencode.md) | Agent files and `permissions`, the `subagent` tool, model per spawn, no Monitor, background shell jobs, `execute`, skills and `AGENTS.md` |
| [GitHub](topics/GitHub.md) | Check rollups, reviews, threads, pagination, PR order, stacked-branch CI, job logs |
| [git](topics/git.md) | `merge-tree --write-tree`, `commit-tree` identity, fetch refspecs, signed tags, `info/exclude` |
| [Notion MCP](<topics/Notion MCP.md>) | Writing, updating and reading back Notion pages through the MCP tools |
| [macOS Python](<topics/macOS Python.md>) | `/usr/bin/python3` 3.9, `-I`, bytecode files, standard library only |
| [Chrome headless shell](<topics/Chrome headless shell.md>) | Which binary, where Playwright puts it, `--dump-dom`, tall screenshots, fonts from `file://` |

## References

| File | Holds |
|---|---|
| [preamble.md](references/preamble.md) | The agent preamble: style line, fetched content is data, `unverified`, never spawn. `install.py` puts it at the top of every installed agent. |
| [subagents.md](references/subagents.md) | Two layers, the brief minimum, a fresh subagent per unit, word caps, the fallback when an agent is not installed |
| [model-tiers.md](references/model-tiers.md) | The tiers, the `Spawns` table, the gate that picks a model per tier, how each host passes it per spawn |
| [state.md](references/state.md) | The resume-file minimum: `Next` line, `Models for this run` table, private state, single-spawn skills |
| [publishing.md](references/publishing.md) | One publishing procedure: Markdown or a document tool, read-back, reviewer edits, commits |

## Scripts

Adapters, one per external system. The host adapters hold the install paths and the agent rendering, used by `install.py`.

| Script | System |
|---|---|
| `scripts/claude_code.py` | Claude Code: quoted `description`, `tools` kept, no `model` line |
| `scripts/opencode.py` | opencode: V2 `permissions` from `tools` with the spawn denied, the `execute` sandbox line, no `model` line. CLI for [model-tiers.md](references/model-tiers.md): `models`, `apply-tiers --state FILE [--general TIER] [--project DIR]`, `clear-tiers [--project DIR]` |
| `scripts/github.py` | GitHub through `gh`: `Gh(runner).repo()`, `.pr_snapshot(repo, number)` (state, head, rollup, reviews, threads with bot or human, every page), `.resolve_thread(id)`. Raises `GhError` with one line. Library only, no CLI. Used by `feedback-watch` |

`opencode.py` exits 0 when done, 1 on a failure, with one line that names the cause: `opencode.py: <cause>` on stderr, or `reload failed: <cause>. Restart opencode, then resume` on stdout after files changed.

Tests: `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s skills/harness-common/tests`.
