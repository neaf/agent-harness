# agent-harness

One source for the skills, subagents and global instructions used by Claude Code and opencode.

| Path | Role |
|---|---|
| `skills/` | `SKILL.md` folders, symlinked into both tools |
| `agents/` | Neutral subagent files: `name`, `description`, `tier` (`fast`, `default`, `strong`), `tools`, then the prompt |
| `instructions/global.md` | Copied to `~/.claude/CLAUDE.md` and `~/.config/opencode/AGENTS.md` |
| `targets/models.json` | Maps each tier to a model per tool |
| `install.py` | Writes the global config of each tool found. `--check` lists drift and exits 1 |

| Skill | What it does |
|---|---|
| [rearchitect](skills/rearchitect/SKILL.md) | Refactors a working but patched-together project in committed phases. Parallel audits, consolidated requirements, a new architecture, then one fresh subagent per phase. |

## Install

```sh
git clone git@github.com:neaf/agent-harness ~/dev/agent-harness
~/dev/agent-harness/install.py
```

Skills are symlinks, so `git pull` updates them. Rerun `install.py` after a pull that changes `agents/`, `instructions/` or `targets/`. Force or skip a tool with `--claude 0|1` and `--opencode 0|1`. Change models in `targets/models.json`.
