# Baseline

Base: `d4b56d4` on `main`, tag `rearch-base`. Run 2026-11-25.

All commands run from the repo root. `PYTHONDONTWRITEBYTECODE=1` keeps `__pycache__/` out of the tree, which `.gitignore` does not cover.

## Build

No build step. Scripts are standard-library Python 3.9+, run with `/usr/bin/python3`.

| Check | Command | Result |
|---|---|---|
| Parse all scripts | `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m py_compile install.py skills/*/scripts/*.py` | ok |
| Install drift | `/usr/bin/python3 -I install.py --check` | `0 change(s) needed`, exit 0 |
| Install drift after storyboard | same | `2 change(s) needed`, exit 1: the two storyboard skill links are not installed yet. Expected until `install.py` runs. |

## Tests

| Suite | Command | Result |
|---|---|---|
| attack-plan-create | `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s skills/attack-plan-create/tests` | 33 OK |
| attack-plan-milestone-execute | `... -s skills/attack-plan-milestone-execute/tests` | 6 OK |
| feedback-watch | `... -s skills/feedback-watch/tests` | 48 OK |
| qa-session | `... -s skills/qa-session/tests` | 9 OK |
| storyboard | `... -s skills/storyboard/tests` | 6 OK (added 2026-11-25 with commit 96ecd40) |

Total 102 tests, all pass (96 at rearch-base, plus 6 storyboard). Lint: none configured.

One-shot run, prints one line per suite:

```sh
for s in skills/*/tests; do printf '%s: ' "$s"; PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s "$s" 2>&1 | tail -1; done
```

## Manual checklist

Not run in this run: the user chose zero manual checks (2026-11-25). Kept as a reference for what automated checks cannot cover. Phases verify automatically (phases.md, "Verification").

- M1: Claude Code install. After `install.py`, every skill, every agent with the model of its tier, and `~/.claude/CLAUDE.md` load in Claude Code.
- M2: opencode install. Same as M1 for opencode: skills, agents with the DeepSeek tiers, `~/.config/opencode/AGENTS.md`.
- M3: Fresh-Mac install. Clone plus `install.py` on a machine with only the Command Line Tools works, including the `y` prompt, `--yes`, and the stop without a terminal.
- M4: feedback-watch live. Watches a real PR through `gh`: CI status, failing checks, head-commit review, unresolved threads. Local mode reruns checks on file change.
- M5: attack-plan-create live. A section runs end to end with critic, designer and reader subagents and publishes to its real destination.
- M6: attack-plan-milestone-execute live. Opens stacked draft PRs for one milestone, builds the integration branch, follows CI and review.
- M7: qa-session live. Builds a QA page that passes `check_page.py` and publishes to its real destination.
- M8: rearchitect live. Stage 0 to a phase runs with the rearch-auditor, rearch-architect and rearch-phase subagents and resumes from `STATE.md`.
- M9: ai-notes live. Notes land in `.ai-notes/<area>/`, and a new session resumes from them.
- M10: writing-craft. The skill triggers before drafting a page, plan, PR description or long reply, and the output follows its rules.
- M11: Global instructions. A session follows `instructions/global.md`: skill-first, delegation with `For review: `, linked PR numbers, minimal test output, feedback-watch after push.

## Models for this run

Confirmed by the user on 2026-11-25 in Claude Code (FR-AGT-07). Every spawn passes the model for its tier.

| Tier | Agents | Model |
|---|---|---|
| fast | rearch-auditor | Sonnet 5.5 (`model: sonnet`) |
| default | rearch-phase | Opus 5.5 (`model: opus`) |
| strong | rearch-architect | Opus 5.5 (`model: opus`) |

Stage 2 audits ran on the installed `fast` agent (Sonnet) and Stage 3 requirements on `strong` (Opus), before this gate existed.
