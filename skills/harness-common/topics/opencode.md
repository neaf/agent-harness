# opencode

Facts about opencode that the installer and the skills depend on. Vendor docs were read on 2026-11-25: [Agents](https://opencode.ai/docs/agents/), [Tools](https://opencode.ai/docs/tools/), [Permissions](https://opencode.ai/docs/permissions/), [CLI commands](https://opencode.ai/docs/cli/commands/), [Config](https://opencode.ai/docs/config/), [Models](https://opencode.ai/docs/models/), [Skills](https://opencode.ai/docs/skills/), [Instructions](https://opencode.ai/docs/instructions/), [Migrate from V1](https://opencode.ai/docs/migrate-v1/). These pages describe OpenCode 2.

opencode is not installed on the maintainer's Mac, so nothing here was checked against a running opencode. Every fact below is from the docs only, and none is checked live. A fact the docs leave open says `unverified`.

Adapter: `skills/harness-common/scripts/opencode.py`, called by `install.py`.

## Agent files

| Fact | Source |
|---|---|
| Global agents live in `~/.config/opencode/agents/<name>.md`, project agents in `.opencode/agents/<name>.md`. The folders `agent/`, `mode/` and `modes/` are still read. | Agents doc, "Locations"; Migrate doc, "Agent files" |
| The agent id comes from the path: `.opencode/agents/team/reviewer.md` is `team/reviewer`. | Agents doc |
| Project `.opencode` folders are found from the working directory up to the project root. | Agents doc |
| Frontmatter keys: `description`, `mode`, `model`, `permissions`, `steps`, `hidden`, `color`, `disabled`, `request`. The body is the system prompt. | Agents doc, "Options" |
| `mode` is `primary`, `subagent` or `all`. A custom agent without `mode` is `primary`. | Agents doc, "Mode" |
| `model` is `provider/model`, optionally `#variant`. | Agents doc, "Model" |
| A subagent with no `model` runs on the parent session's model. | Agents doc, "Model" |
| A built-in agent (`build`, `plan`, `general`, `explore`) is overridden by an agent with the same id. | Agents doc, "Built-ins" |

Code: `opencode.py:39-48` writes `description`, `mode: subagent` and `permissions`, then the preamble, the sandbox line and the body. It writes no `model` line: the agent runs on the session model until a run applies tiers ("Model per spawn").

### Quirk: V1 and V2 frontmatter

- Symptom: keys in an agent file are ignored, with only a warning in the log.
- Cause: a file that uses any of `permissions`, `request`, `system` or `disabled` is read as V2, and its V1 keys (`name`, `tools`, `permission`, `temperature`) are dropped. A file without them is read as V1 and translated.
- Workaround: write only V2 keys. Express tool limits as `permissions` rules, never as `tools`.
- Code: `opencode.py:39-48` writes `permissions` and never `tools`, `permission` or `name`.

## Permissions

| Fact | Source |
|---|---|
| `permissions` is an ordered list of `{action, resource, effect}` rules. `effect` is `allow`, `ask` or `deny`. The last matching rule wins. | Permissions doc |
| Every agent starts from "allow everything", with an `ask` for `.env` reads. | Permissions doc, "Defaults" |
| Agent rules are appended after the global rules. A custom subagent uses its own rules, not a subset of its parent's. | Permissions doc, "Agents" |

Actions the harness maps tools to:

| Claude Code tool | opencode action | Source |
|---|---|---|
| Read | `read` | Tools doc |
| Glob | `glob` | Tools doc |
| Grep | `grep` | Tools doc |
| Edit, Write | `edit` (also covers patch) | Tools doc |
| Bash | `shell` | Tools doc |
| WebFetch | `webfetch` | Tools doc |
| WebSearch | `websearch` | Tools doc |
| Skill | `skill` | Tools doc |
| Agent (spawn) | `subagent` | Tools doc |
| none | `execute`, `question`, `external_directory` | Permissions doc |

V1 names map as `bash` to `shell`, `task` to `subagent`, `write` and `patch` to `edit` (Migrate doc, "Permissions and tools").

How the harness renders `tools` (`opencode.py:25-36`): one `deny` rule with resource `*` for every action in the table above that the agent's `tools` do not cover, then `{action: subagent, resource: "*", effect: deny}`. Allowed actions get no rule, so they keep the defaults and the user's global rules, `.env` ask included. `execute`, `question` and `external_directory` get no rule. An agent's skill references sit outside the project, so a deny on `external_directory` would cut it off from them. Whether these rules take effect in a running opencode is `unverified`.

### Quirk: Write and Edit are one action

- Symptom: an agent whose `tools` list `Write` but not `Edit` (attack-plan-critic, -designer, -reader, rearch-auditor) can still edit files on opencode. On Claude Code it cannot.
- Cause: opencode's `edit` action covers writing, editing and patching. There is no write-only action.
- Workaround: none in the permissions. The read-only stance stays in the agent's role text (FR-AGT-04).
- Code: `opencode.py:10-13` maps both to `edit`.

## The `subagent` tool

| Fact | Source |
|---|---|
| `subagent` starts a child session. Its inputs are the agent id, a short description and the prompt. A returned `sessionID` continues the same child. There is no model input. | Tools doc, "Subagent" |
| Children always run in the background. The parent gets a `<subagent>` message when the child goes idle. | Tools doc; Agents doc, "Modes" |
| Only agents with `mode: subagent` (or `all`) can be spawned. | Tools doc |
| Nesting depth is `experimental.subagent_depth`, default `1`: a subagent cannot start another subagent. | Config doc, "Experimental" |
| The built-in `general` agent denies launching subagents. | Permissions doc, "Defaults" |
| The spawn is deniable: a rule with action `subagent` and resource `*` (or an agent id) and effect `deny`. | Agents doc, "Modes"; Permissions doc |

## Model per spawn

| Question | Answer | Source |
|---|---|---|
| Does the spawn tool take a model per call? | No. The `subagent` tool takes agent id, description, prompt and `sessionID`. | Tools doc, "Subagent" |
| Which agent folder and keys? | `agents/`, V2 keys (above). | Agents doc; Migrate doc |
| Are project-local agents loaded? | Yes, `.opencode/agents/<id>.md` from the working directory up to the project root. | Agents doc, "Locations" |
| Does a project agent override a global one of the same id? | Agent definitions merge in configuration order, project after global. Later scalar values such as `model` replace earlier ones; `permissions` rules append. That this order also applies to Markdown agent files is `unverified`. | Agents doc, "Merging"; Config doc, "Locations" |
| Are agents reloaded without a restart? | Config files "normally reload automatically", and `opencode reload` reloads config without restarting the server; running sessions pick it up at the next step. Whether agent files count as config here is `unverified`. | Models doc, "Caveats"; CLI commands doc, "reload" |
| Can the spawn tool be denied? | Yes, action `subagent`. | Permissions doc |
| Does an agent without `model` inherit? | Yes, the parent session's model. | Agents doc, "Model" |
| How are models listed? | `opencode models` lists every available model. Its output format is not documented: `unverified`. Availability depends on the project's providers. | CLI commands doc, "models"; Models doc |

Answer: override files. At the tier gate, `opencode.py apply-tiers` writes one `.opencode/agents/<id>.md` per tiered agent in the project, each a full copy of the installed agent with the tier's `model` line, so the result does not depend on how files merge. A `general.md` override puts every `general` spawn on one model (A2). The written paths go into `.git/info/exclude`, and `clear-tiers` removes them when the run ends. After writing, the orchestrator runs `opencode reload`. If the next spawn does not use the new model, the gate ends with "restart opencode, then resume".

`override files`

## No Monitor tool

| Fact | Source |
|---|---|
| The tool list has no Monitor tool. | Tools doc |
| A shell call with `background: true` returns at once and notifies the session when the process finishes. It has no timeout unless one is given. Large output is shortened, and the full output is kept in a managed file. | Tools doc, "Shell" |
| A foreground shell call times out after two minutes unless `timeout` is set. | Tools doc, "Shell" |

### Quirk: no event per output line

- Symptom: a background `watch.py` reports nothing to the session until it exits. Claude Code's Monitor delivers each line as it prints.
- Cause: background shell calls notify only on finish.
- Workaround: run `watch.py` as a background shell job with its output in a log file outside the repo. Read the tail of the log when the job finishes, when the session is idle, or when the user asks. Pull-request mode exits on `ALL DONE` and `CI DONE`, and on `TIMEOUT` only when `--timeout` is set (default `0`, no limit). Local mode without `--once` never exits, so it never notifies.
- Code: `skills/feedback-watch/SKILL.md:63`; exits in `skills/feedback-watch/scripts/watch.py:175-181`, `--timeout` default at `:286`.

## `execute` (Code Mode)

| Fact | Source |
|---|---|
| `execute` runs JavaScript that calls other tools. It has no filesystem access, no imports and no timers; it has `fetch`. | Tools doc, "Execute" |
| Denying `execute` with resource `*` removes Code Mode; its tools are then listed directly. | Tools doc; Permissions doc |

Code: `opencode.py:16-17` (`SANDBOX_LINE`), added to opencode agents only (FR-AGT-06).

## Skills and global instructions

| Fact | Source |
|---|---|
| Global skills live in `~/.config/opencode/skills/`. opencode also reads `~/.claude/skills/` and `~/.agents/skills/`. | Skills doc, "Discovery" |
| For one skill id, `~/.config/opencode/skills/` is registered after `~/.claude/skills/` and wins. | Skills doc, "Precedence" |
| A match between `name` and the folder name is not enforced. | Skills doc |
| The global instructions file is `~/.config/opencode/AGENTS.md`. Without it opencode reads `~/.claude/CLAUDE.md`. | Instructions doc, "CLAUDE.md fallback" |
| Edits to a nested `AGENTS.md` that already loaded are not seen until a new session. | Instructions doc, "Discovery" |

### Quirk: every harness skill is found twice

- Symptom: each harness skill exists in `~/.claude/skills/` and in `~/.config/opencode/skills/`.
- Cause: opencode reads both folders, and install links every skill into both.
- Workaround: none needed. Both links point at the same folder in this checkout, and the opencode one wins.
- Code: `install.py:104-105`.
