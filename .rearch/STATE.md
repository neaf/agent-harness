# Rearchitect state

Project: agent-harness, one source of skills, subagents and global instructions for Claude Code and opencode, installed by install.py.
Branch: rearch/2026-11-25
Base tag: rearch-base (d4b56d4)
Stage: 5 (phase execution)
Phase: 3 of 10 (Installer and agent sources), not started

## Done
- Stage 0 setup, 7f686cb
- Stage 1 inventory, eb518ca, 6 aspects confirmed by user
- Stage 2 audits, 19cf3c1, 6 aspect reports plus seams.md, coverage complete
- Stage 3 requirements, f349b26, all questions answered
- Stage 4 architecture, 61d78ce, 22 modules, 10 phases
- Storyboard added: commit 96ecd40 (cherry-pick of ec14673 from skill/storyboard), audit/storyboard.md, FR-SB-01..16, folded into phases 1, 2, 4, 8; 24 modules
- Phase 1 Topic docs: 7 topic docs in skills/harness-common/topics/, Q37 = override files (opencode subagent tool has no model input), 7 deviations in deviations.md, 178f980
- Phase 2 Test harness: 151 tests in 6 suites, 26 expected failures; root tests/ with install and repo-rule tests

## Decisions
- 2026-11-25: target is agent-harness itself, user call.
- 2026-11-25: this repo commits with the personal email (local git config user.email); the 4 rearch commits were re-authored, user call.
- 2026-11-25: Q3, no model names or ids anywhere in the repo, no defaults. Delete targets/models.json; install writes no model lines. When a run starts, the orchestrator lists the current tool's models, proposes a model per tier, and the user confirms or overrides at a gate (one model for every tier is allowed). FR-AGT-02, -07, -08; mechanism per tool is Q37, user call.
- 2026-11-25: Q7 macOS only, user call.
- 2026-11-25: Q17 attack-plan-milestone-execute may resolve FIX review threads started by a bot; threads started by a human stay for the user, user call.
- 2026-11-25: Q30f moot. Two layers at most, subagents never spawn subagents (NFR-13), user call.
- 2026-11-25: Q30 user knows none of the external facts; all stay unverified, checked in M2, M4, M5, M7.
- 2026-11-25: Q33/Q34 qa-session simplified for now. Page = collapsed setup for the lead dev, simple numbered scenarios with all needed context, empty Findings section with no table. Known limits, Product questions, After the session dropped. The skill needs more work later, user call.
- 2026-11-25: all other Open questions settled by accepting the orchestrator's recommendations; listed at the end of requirements.md. Experimental FR-AGT-05, FR-QA-13, FR-FW-13 kept; FR-APC-18/19 dropped, user call.
- 2026-11-25: manual checklist M1..M11 recorded, then dropped: zero manual checks for this run; phases verify automatically and report what is not verified. The rearchitect skill gets FR-RA-14 (ask how many manual checks, default zero; defaults at every gate), user call.
- 2026-11-25: Stage 4 architect questions A1-A4 plus A5 settled with the recommended defaults, per the user's preference for defaults (end of requirements.md).
- 2026-11-25: include the storyboard skill from ~/dev/agent-harness-storyboard; its questions SB-Q1..Q11 settled with defaults (end of requirements.md), user call.
- 2026-11-25: models for this run: fast Sonnet 5.5, default Opus 5.5, strong Opus 5.5 (baseline.md), user call.

## Next prompt
    Use the rearchitect skill. Continue from .rearch/STATE.md.
    Next: Phase 3 (Installer and agent sources).
