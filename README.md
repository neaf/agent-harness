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
| [ai-notes](skills/ai-notes/SKILL.md) | Keeps markdown notes per area in `.ai-notes/`, committed by default (`.git/info/exclude` to keep them private in a repo), so one orchestrator session can hand work to fresh subagents and later sessions. |
| [rearchitect](skills/rearchitect/SKILL.md) | Refactors a working but patched-together project in committed phases. Parallel audits, consolidated requirements, a new architecture, then one fresh subagent per phase. |
| [attack-plan-create](skills/attack-plan-create/SKILL.md) | Writes an attack plan (tech exploration) one section at a time: product solution first, then technical solution, milestones and tasks an agent can turn into pull requests. Fresh subagents attack each section, the author answers one question at a time and reviews each section. Tests: `/usr/bin/python3 -I -m unittest discover -s skills/attack-plan-create/tests`. |
| [attack-plan-milestone-execute](skills/attack-plan-milestone-execute/SKILL.md) | Builds one milestone of an attack plan as stacked draft PRs, one fresh subagent per PR: checks the input, audits the tickets against the code, follows CI and reviews until green, keeps the stacks in sync. Tests: `/usr/bin/python3 -I -m unittest discover -s skills/attack-plan-milestone-execute/tests`. |
| [feedback-watch](skills/feedback-watch/SKILL.md) | Watches a session's work in the background: CI, review and unresolved threads on GitHub pull requests, or local checks rerun on file changes, one line per real change. Tests: `/usr/bin/python3 -I -m unittest discover -s skills/feedback-watch/tests`. |
| [writing-craft](skills/writing-craft/SKILL.md) | Craft rules for text a human reads and acts on: the form that mirrors the reader's task, the exact word, layout, and revision from the reader's failure point. |

## Install

```sh
git clone https://github.com/neaf/agent-harness ~/dev/agent-harness
~/dev/agent-harness/install.py
```

Needs only `git` and `/usr/bin/python3` (Python 3.9+, standard library only). On a new Mac both come with the Command Line Tools (`xcode-select --install`, or the prompt shown by the first `git` call). The script uses `/usr/bin/python3` directly, so asdf, pyenv or Homebrew Python don't change anything. Install Claude Code or opencode first: tools with no config folder and no binary on the `PATH` are skipped.

The script lists every file and link it will create or replace. Replacing anything that already exists (a `CLAUDE.md` you edited, a skill folder copied by hand) needs a `y` at the prompt, or `--yes`. Without a terminal and without `--yes` it stops and changes nothing. `--check` lists the changes and writes nothing.

Skills are symlinks, so `git pull` updates them. Rerun `install.py` after a pull that changes `agents/`, `instructions/` or `targets/`. Force or skip a tool with `--claude 0|1` and `--opencode 0|1`. Change models in `targets/models.json`.
