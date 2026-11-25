---
name: harness-common
description: Shared library of the agent-harness skills, never invoked on its own. Load a file from it only when another harness skill links to it. It holds the facts about the external systems the skills use (Claude Code, opencode, GitHub, git, Notion MCP, macOS Python, Chrome headless shell).
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

## Scripts

Host adapters used by `install.py`. Each holds the install paths and the agent rendering for one host.

| Script | Host |
|---|---|
| `scripts/claude_code.py` | Claude Code: quoted `description`, `tools` kept, no `model` line |
| `scripts/opencode.py` | opencode: V2 `permissions` from `tools` with the spawn denied, the `execute` sandbox line, no `model` line |

Tests: `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s skills/harness-common/tests`.
