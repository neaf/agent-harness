# Working on agent-harness

This repo is the single source of the skills, subagents and global instructions for Claude Code and opencode. It runs on macOS only, with the standard library of `/usr/bin/python3` (3.9+) and nothing else.

## Layout

| Path | Holds |
|---|---|
| `skills/<name>/` | One skill: `SKILL.md`, then `references/`, `scripts/` and `tests/` as needed. Installed as a symlink. |
| `skills/harness-common/` | The shared library: adapters (`scripts/`), conventions (`references/`) and one topic doc per external system (`topics/`). Never invoked on its own. |
| `agents/*.md` | Neutral subagent sources: `name`, `description`, `tier`, `tools`, then the body. `install.py` renders them for each tool. |
| `instructions/global.md` | The user's global rules, copied to `~/.claude/CLAUDE.md` and `~/.config/opencode/AGENTS.md`. |
| `install.py` | Installs into both tools. `--check` lists drift and writes nothing. |
| `tests/` | Repo-wide tests: install, and repo rules such as no model names and Spawns tables. |
| `docs/` | `requirements.md` (one ID per requirement) and `architecture.md` (modules, interfaces, traceability). |

## Checks

Run from the repo root. Each suite prints one line.

```sh
for s in tests skills/*/tests; do printf '%s: ' "$s"; PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s "$s" 2>&1 | tail -1; done
/usr/bin/python3 -I install.py --check
```

- Parse checks use `compile()`, never `py_compile`, which writes `__pycache__`.
- Test installs go into a throwaway `HOME`, never the real `~/.claude` or `~/.config`.

## Rules

- No model name or id anywhere in the repo. Agents declare a tier (`fast`, `default`, `strong`), and the orchestrator resolves tiers to models when a run starts. `tests/test_repo_rules.py` enforces this.
- A skill that spawns subagents has a Spawns table (spawn, tier, use) and follows `skills/harness-common/references/subagents.md`. There are two layers at most: subagents never spawn subagents.
- Facts about external systems live in `skills/harness-common/topics/`, with evidence or marked `unverified`.
- A behavior change updates `docs/requirements.md` and `docs/architecture.md` in the same commit.
- After editing `agents/` or `instructions/`, run `install.py`. Skill edits apply at once through the symlinks.
