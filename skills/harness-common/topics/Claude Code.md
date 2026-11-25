# Claude Code

Facts about Claude Code that the installer and the skills depend on. Vendor docs were read on 2026-11-25: [Subagents](https://code.claude.com/docs/en/sub-agents), [Tools reference](https://code.claude.com/docs/en/tools-reference), [Skills](https://code.claude.com/docs/en/skills), [Memory](https://code.claude.com/docs/en/memory).

Adapter: `skills/harness-common/scripts/claude_code.py`, called by `install.py`.

## Agent files

| Fact | Source |
|---|---|
| User agents live in `~/.claude/agents/`, project agents in `.claude/agents/`. Both are scanned recursively. Identity comes from `name`, not the file name. | Subagents doc, "Choose the subagent scope" |
| Several project `.claude/agents/` folders between the working directory and the repo root: the definition closest to the working directory wins for one `name`. | Subagents doc |
| Required keys: `name` and `description`. `name` cannot contain `:` or start with `-`. | Subagents doc, "Frontmatter reference" |
| `tools` is a comma-separated string or a YAML list. It restricts the agent to those tools. Without `tools` the agent inherits every tool available to subagents. `disallowedTools` removes tools. | Subagents doc |
| `model` takes a family alias, a full model id, or `inherit`. The doc lists the current aliases; the repo names none (FR-AGT-08). | Subagents doc, "Choose a model" |
| Claude Code watches `~/.claude/agents/` and `.claude/agents/`. A changed file is used by the next spawn, with no restart. | Subagents doc |
| The body after the closing `---` is the agent's system prompt. | Subagents doc |

Code: `claude_code.py:19-26` writes `name`, `description` and `tools`, then the preamble and the body. It writes no `model` line (FR-AGT-02). `install.py:48-70` rejects an agent source whose `tools` lists `Agent` or `Task`.

### Quirk: unquoted `: ` in a description

- Symptom: a description such as `Audits one aspect of a project for the rearchitect skill: reads every assigned file` is not valid YAML as a plain scalar. The docs say a file whose YAML does not parse is skipped, with the error in the `--debug` log. Yet the installed `rearch-auditor` agent, which has this description, loaded and ran the Stage 2 audits of this run (`.rearch/STATE.md`).
- Cause: unknown. The loader may be more lenient than strict YAML. `unverified`.
- Workaround: write every description as a double-quoted YAML string (FR-INST-11).
- Code: `claude_code.py:24` (`json.dumps`, a JSON string is a valid double-quoted YAML scalar).

## Model per spawn

| Fact | Source |
|---|---|
| The model of a spawn is the first of: the Agent tool's per-call `model` parameter, the agent file's `model`, `CLAUDE_CODE_SUBAGENT_MODEL`, the parent conversation's model. | Subagents doc, "Choose a model" |
| The Agent tool's `model` parameter takes an alias only, not a full model id and not `inherit`. | Subagents doc |
| The allowed values of `model` are listed in the Agent tool's definition in the session. The orchestrator reads them there. | This run: `.rearch/baseline.md` "Models for this run", every spawn passed `model` |
| A resumed subagent keeps the alias it started with. | Subagents doc |

## Nested spawns

| Fact | Source |
|---|---|
| By default a subagent can spawn its own subagents, up to three layers below the main conversation. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes the limit; `1` turns nesting off. | Subagents doc, "Let subagents spawn their own subagents" |
| An agent without `Agent` in `tools`, or with `Agent` in `disallowedTools`, cannot spawn. | Subagents doc |
| At most 20 subagents run at once; the next spawn fails with `Concurrent subagent limit reached`. | Subagents doc, "Concurrent subagent limit" |

### Quirk: general-purpose subagents can spawn

- Symptom: a `general-purpose` subagent has the Agent tool and can start a third layer. The harness allows two layers at most (NFR-13).
- Cause: nesting is on by default, up to three layers.
- Workaround: every harness agent lists `tools` without `Agent`, and install rejects an agent that lists `Agent` or `Task`. The preamble says "You never spawn subagents". A brief for a `general-purpose` spawn carries the preamble rule "never spawn a subagent". The harness does not change the user's `settings.json`.
- Code: `agents/*.md` `tools` lines; `claude_code.py:11` (`SPAWN_TOOLS`), checked in `install.py:62-64`; `skills/harness-common/references/preamble.md`.

## Subagent environment

| Fact | Source |
|---|---|
| A subagent starts in the main conversation's working directory. `cd` does not persist between Bash calls. | Subagents doc |
| A background subagent keeps Read, Grep, Glob, Bash, Edit, Write, WebFetch, WebSearch, Skill, Monitor, TaskStop, SendMessage and the MCP tools, and loses most other built-in tools. | Subagents doc, "Available tools" |

## Monitor tool

| Fact | Source |
|---|---|
| Monitor runs a command in the background and turns each stdout line into an event for the session. | Tools reference, "Monitor tool" |
| Every watch has a deadline, `timeout_ms`: 5 minutes by default, 30 minutes (`1800000`) at most, 10 minutes in a `-p` run. At the deadline the watch ends and the session gets one notice. | Tools reference |
| Stopping a subagent stops the monitors it started. | Tools reference |
| Monitor commands follow the Bash permission rules. | Tools reference |

Code: `skills/feedback-watch/SKILL.md:58-61` arms `watch.py` with `timeout_ms` 1800000.

## Skills and global instructions

| Fact | Source |
|---|---|
| Personal skills live in `~/.claude/skills/<name>/SKILL.md`. The folder can be a symlink; Claude Code reads `SKILL.md` from the target. | Skills doc, "Choose where skills load" |
| A personal skill wins over a project skill of the same name. | Skills doc |
| Edits to `SKILL.md` text are picked up live. | Skills doc, "Live change detection" |
| `~/.claude/CLAUDE.md` holds the user's instructions for every project. | Memory doc |
| A `CLAUDE.md` line `@path` imports that file. Relative paths resolve from the importing file. Imports nest four hops deep. An `@path` inside backticks or a code block is not imported. | Memory doc, "Import additional files" |

Code: `install.py:98-106` copies `instructions/global.md` to `~/.claude/CLAUDE.md` and links every skill folder into `~/.claude/skills/`; paths in `claude_code.py:14-16`.

## Plugin skills

| Fact | Source |
|---|---|
| `frontend-design` is a Claude Code plugin skill under `~/.claude/plugins/cache/claude-plugins-official/frontend-design`. | Directory listing, 2026-11-25 |
| This repo neither ships nor installs it. Skills name it "when available" and work without it. | `skills/storyboard/SKILL.md:10`, CON-CC-04 |
| Whether opencode can load it: `unverified`. | none |
