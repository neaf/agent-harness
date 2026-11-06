# agent-skills

Skills and subagents for Claude Code and opencode.

| Skill | What it does |
|---|---|
| [rearchitect](rearchitect/SKILL.md) | Refactors a working but patched-together project in committed phases. Parallel audits, consolidated requirements, a new architecture, then one fresh subagent per phase. |

## Install

```sh
git clone https://github.com/neaf/agent-skills ~/dev/agent-skills
~/dev/agent-skills/rearchitect/install.sh
```

`install.sh` detects Claude Code (`claude` command or `~/.claude`) and opencode (`opencode` command or `~/.config/opencode`) and sets up each one it finds. It symlinks the skill folder, so keep the clone in place and `git pull` to update. Rerun `install.sh` after a pull that changes `agents/`.

Force or skip a tool with `WITH_CLAUDE=1|0` and `WITH_OPENCODE=1|0`. Change subagent models with `AUDIT_MODEL_CC`, `ARCH_MODEL_CC`, `PHASE_MODEL_CC`, `AUDIT_MODEL_OC`, `ARCH_MODEL_OC`, `PHASE_MODEL_OC`.
