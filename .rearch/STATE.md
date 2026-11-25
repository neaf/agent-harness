# Rearchitect state

Project: agent-harness, one source of skills, subagents and global instructions for Claude Code and opencode, installed by install.py.
Branch: rearch/2026-11-25
Base tag: rearch-base (d4b56d4)
Stage: 4 (architecture), not started

## Done
- Stage 0 setup, ac7502c
- Stage 1 inventory, 5e1bf65, 6 aspects confirmed by user
- Stage 2 audits, d88a3bf, 6 aspect reports plus seams.md, coverage complete
- Stage 3 requirements, all questions answered

## Decisions
- 2026-11-25: target is agent-harness itself, user call.
- 2026-11-25: Q3, no model names or ids anywhere in the repo, no defaults. Delete targets/models.json; install writes no model lines. When a run starts, the orchestrator lists the current tool's models, proposes a model per tier, and the user confirms or overrides at a gate (one model for every tier is allowed). FR-AGT-02, -07, -08; mechanism per tool is Q37, user call.
- 2026-11-25: Q7 macOS only, user call.
- 2026-11-25: Q17 attack-plan-milestone-execute may resolve FIX review threads started by a bot; threads started by a human stay for the user, user call.
- 2026-11-25: Q30f moot. Two layers at most, subagents never spawn subagents (NFR-13), user call.
- 2026-11-25: Q30 user knows none of the external facts; all stay unverified, checked in M2, M4, M5, M7.
- 2026-11-25: Q33/Q34 qa-session simplified for now. Page = collapsed setup for the lead dev, simple numbered scenarios with all needed context, empty Findings section with no table. Known limits, Product questions, After the session dropped. The skill needs more work later, user call.
- 2026-11-25: all other Open questions settled by accepting the orchestrator's recommendations; listed at the end of requirements.md. Experimental FR-AGT-05, FR-QA-13, FR-FW-13 kept; FR-APC-18/19 dropped, user call.
- 2026-11-25: manual checklist covers both installs, fresh-Mac install, and a live run of every skill plus the global instructions (M1..M11), user call.

## Next prompt
    Use the rearchitect skill. Continue from .rearch/STATE.md.
    Next: Stage 4 (architecture).
