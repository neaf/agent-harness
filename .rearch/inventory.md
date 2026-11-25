# Inventory

43 tracked files, 3,770 lines, at `rearch-base`. No untracked files apart from `__pycache__/` caches.

The prompt files (`SKILL.md`, `references/`, `resources/`, `agents/`, `instructions/`) are the product, so they count as source. Kind `source (prompt)` marks them, and `source (py)` marks scripts.

| File | Kind | Lines | Aspects |
|---|---|---|---|
| .gitignore | config | 2 | install-and-config |
| README.md | doc | 35 | install-and-config, storyboard, attack-plan, feedback-watch, qa-session, rearchitect, notes-and-writing |
| install.py | source (py) | 109 | install-and-config |
| targets/models.json | config | 4 | install-and-config |
| instructions/global.md | source (prompt) | 20 | install-and-config, notes-and-writing, feedback-watch |
| agents/attack-plan-critic.md | source (prompt) | 25 | attack-plan |
| agents/attack-plan-designer.md | source (prompt) | 25 | attack-plan |
| agents/attack-plan-reader.md | source (prompt) | 25 | attack-plan |
| skills/attack-plan-create/SKILL.md | source (prompt) | 164 | attack-plan |
| skills/attack-plan-create/references/briefs.md | source (prompt) | 71 | attack-plan |
| skills/attack-plan-create/references/document-template.md | source (prompt) | 53 | attack-plan |
| skills/attack-plan-create/references/executable-plan.md | source (prompt) | 48 | attack-plan |
| skills/attack-plan-create/references/publishing.md | source (prompt) | 40 | attack-plan |
| skills/attack-plan-create/references/questions.md | source (prompt) | 58 | attack-plan |
| skills/attack-plan-create/references/state.md | source (prompt) | 60 | attack-plan |
| skills/attack-plan-create/scripts/check_draft.py | source (py) | 178 | attack-plan |
| skills/attack-plan-create/scripts/gate.py | source (py) | 203 | attack-plan |
| skills/attack-plan-create/tests/test_check_draft.py | test | 122 | attack-plan |
| skills/attack-plan-create/tests/test_gate.py | test | 123 | attack-plan |
| skills/attack-plan-milestone-execute/SKILL.md | source (prompt) | 128 | attack-plan |
| skills/attack-plan-milestone-execute/resources/input-readiness.md | source (prompt) | 38 | attack-plan |
| skills/attack-plan-milestone-execute/resources/review-pass.md | source (prompt) | 45 | attack-plan |
| skills/attack-plan-milestone-execute/resources/subagent-rules-template.md | source (prompt) | 46 | attack-plan |
| skills/attack-plan-milestone-execute/scripts/build_integration_branch.py | source (py) | 145 | attack-plan |
| skills/attack-plan-milestone-execute/tests/test_build_integration_branch.py | test | 105 | attack-plan |
| skills/feedback-watch/SKILL.md | source (prompt) | 98 | feedback-watch |
| skills/feedback-watch/scripts/watch.py | source (py) | 317 | feedback-watch |
| skills/feedback-watch/tests/test_watch.py | test | 390 | feedback-watch |
| skills/qa-session/SKILL.md | source (prompt) | 111 | qa-session |
| skills/qa-session/references/briefs.md | source (prompt) | 71 | qa-session |
| skills/qa-session/references/page-template.md | source (prompt) | 85 | qa-session |
| skills/qa-session/references/publishing.md | source (prompt) | 29 | qa-session |
| skills/qa-session/references/setup-checklist.md | source (prompt) | 45 | qa-session |
| skills/qa-session/scripts/check_page.py | source (py) | 114 | qa-session |
| skills/qa-session/tests/test_check_page.py | test | 100 | qa-session |
| agents/rearch-architect.md | source (prompt) | 41 | rearchitect |
| agents/rearch-auditor.md | source (prompt) | 68 | rearchitect |
| agents/rearch-phase.md | source (prompt) | 39 | rearchitect |
| skills/rearchitect/SKILL.md | source (prompt) | 115 | rearchitect |
| skills/rearchitect/references/docs-style.md | source (prompt) | 23 | rearchitect |
| skills/rearchitect/references/state.md | source (prompt) | 98 | rearchitect |
| skills/ai-notes/SKILL.md | source (prompt) | 68 | notes-and-writing |
| skills/writing-craft/SKILL.md | source (prompt) | 87 | notes-and-writing |
| skills/storyboard/SKILL.md | source (prompt) | 81 | storyboard |
| skills/storyboard/references/brief.md | source (prompt) | 43 | storyboard |
| skills/storyboard/references/page.md | source (prompt) | 56 | storyboard |
| skills/storyboard/references/skeleton.html | source (asset) | 286 | storyboard |
| skills/storyboard/scripts/shoot.py | source (py) | 81 | storyboard |
| skills/storyboard/tests/test_shoot.py | test | 46 | storyboard |

## Totals per aspect

Shared files (README, global.md) are counted in every aspect they join.

| Aspect | Files | Lines | Scope |
|---|---|---|---|
| install-and-config | 5 | 169 | install.py, model tiers, global instructions, README, ignore rules |
| attack-plan | 21 | 1,736 | both attack-plan skills, their 3 agents, scripts and tests |
| feedback-watch | 5 | 859 | skill, watcher script, tests |
| qa-session | 8 | 589 | skill, references, page checker, tests |
| rearchitect | 7 | 418 | skill, references, 3 rearch agents |
| notes-and-writing | 4 | 209 | ai-notes, writing-craft, the global rules that point at them |
| storyboard | 7 | 628 | storyboard skill, added from branch skill/storyboard (commit 96ecd40); README line joins |

All aspects are under the 8,000-line budget. A `seams` audit follows in Stage 2: agent file format versus install.py, tier mapping, the conventions shared across skills (briefs, state files, publishing, subagent rules), and duplicated logic between the scripts.
