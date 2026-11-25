# Docs plan

## Location rule

Topic docs live in `skills/harness-common/topics/`, not `docs/`. Running agents need these facts: Notion quirks while publishing, Monitor and opencode facts while arming the watcher, the spawn `model` parameter while resolving tiers. Only skill folders are installed. `docs/` keeps the maintainer docs that Stage 6 moves in: `requirements.md` and `architecture.md`. README links every topic doc. Topic docs follow `skills/rearchitect/references/docs-style.md`: present tense, no history, four-part quirks, every fact sourced, unchecked facts marked `unverified`.

## Fate of every current doc

| Current doc | Fate | Target |
|---|---|---|
| README.md | keep. Each phase updates its own rows; Stage 6 does the final pass | README.md |
| instructions/global.md | rewrite: dedupe, tool-neutral (Phase 5) | same |
| skills/attack-plan-create/references/publishing.md | Notion quirks go to the topic doc (Phase 1). Procedure goes to the shared reference, then the file is deleted (Phase 4) | topics/Notion MCP.md, harness-common/references/publishing.md |
| skills/qa-session/references/publishing.md | fold into the shared reference, delete (Phase 4) | harness-common/references/publishing.md |
| skills/feedback-watch/SKILL.md, Monitor and opencode lines (:55-63) | facts go to topic docs (Phase 1). SKILL keeps the steps and links (Phase 6) | topics/Claude Code.md, topics/opencode.md |
| skills/feedback-watch/SKILL.md, CI failure advice (:74-81) | keep there (Q28). GitHub facts in it get sources in the topic doc | topics/GitHub.md |
| skills/attack-plan-milestone-execute/SKILL.md :54, :78 (PR order, stacked CI) | facts go to the topic doc, SKILL links (Phase 1 doc, Phase 9 link) | topics/GitHub.md |
| skills/attack-plan-milestone-execute/resources/review-pass.md GraphQL | replaced by `review_threads.py` (Phase 9) | same file, shorter |
| skills/attack-plan-milestone-execute/resources/subagent-rules-template.md | keep. Drop "Surprises" (Q16), add outside-reviewer context and writing-craft (Phase 9) | same |
| skills/attack-plan-create/references/state.md | keep, fix the example, conform to the minimum (Phase 7) | same |
| skills/attack-plan-create/references/document-template.md | keep, drop section 6 and the "appendix" wording (Phase 7) | same |
| skills/attack-plan-create/references/executable-plan.md | keep, task-block schema becomes fixed headings (Phase 7) | same |
| skills/attack-plan-create/references/briefs.md | keep, role tasks only, output paths named, preamble by reference (Phase 7) | same |
| skills/attack-plan-create/references/questions.md | keep unchanged | same |
| skills/qa-session/references/page-template.md | rewrite to three parts (Phase 8) | same |
| skills/qa-session/references/briefs.md | keep, absolute paths, injection rule, preamble by reference (Phase 8) | same |
| skills/qa-session/references/setup-checklist.md | keep, collapsed setup, exact-label rule (Phase 8) | same |
| skills/rearchitect/SKILL.md "Model routing" | moved to the shared tier reference plus a `Spawns` table (Phase 10) | harness-common/references/model-tiers.md |
| skills/rearchitect/references/state.md | keep. Add refuted section, Progress block, models table, one Next-prompt format (Phase 10) | same |
| skills/rearchitect/references/docs-style.md | keep. Neutral examples, topic location rule (Phase 10) | same |
| skills/writing-craft/SKILL.md | keep. Scope line, neutral examples, section 7 folded (Phase 5) | same |
| skills/ai-notes/SKILL.md | keep. Trigger fix, "State (start here)" defined, cites the state minimum (Phase 5) | same |
| agents/*.md preamble lines (:8-12) | moved to the shared preamble, which install prepends (Phase 3) | harness-common/references/preamble.md |
| targets/models.json | delete (Phase 3) | |
| .rearch/requirements.md | Stage 6 moves it | docs/requirements.md |
| .rearch/architecture.md | Stage 6 moves it | docs/architecture.md |
| .rearch/STATE.md, baseline.md, inventory.md, audit/*, docs-plan.md, phases.md, deviations.md | Stage 6 deletes them after the final baseline and checklist (Q36) | |

## Target docs

| Doc | Scope |
|---|---|
| README.md | What the harness ships, install and `--check`, agent source format, test commands, links to topic docs. |
| AGENTS.md (repo root) | Under 60 lines for agents working on this repo: baseline commands, layout, pointers. A one-line `CLAUDE.md` imports it with `@AGENTS.md` (Claude Code import syntax, unverified). Stage 6 writes both. |
| docs/requirements.md | Functional requirements with IDs (Stage 6 move). |
| docs/architecture.md | Modules, data flow, interfaces (Stage 6 move). |
| skills/harness-common/topics/Claude Code.md | Agent file format and `tools`, Agent tool `model` parameter and how to read its values, Monitor tool and `timeout_ms`, no nested spawns, skill and CLAUDE.md paths, YAML strictness of frontmatter. |
| skills/harness-common/topics/opencode.md | Agent folder and frontmatter, `mode`, `model` as `provider/model`, `tools`/`permission` keys, task tool parameters, `opencode models`, agent reload behavior, project-local agent precedence, no-model inheritance, no Monitor (background job), `execute` sandbox, skills folder, AGENTS.md. Mostly `unverified`. |
| skills/harness-common/topics/GitHub.md | `statusCheckRollup` shapes, reruns and cancelled runs, empty and partial rollups, bot logins in REST and GraphQL, thread author `__typename`, `resolveReviewThread`, pagination limits, PR list order, stacked-branch CI, job logs mid-run, "runner lost communication". |
| skills/harness-common/topics/git.md | `merge-tree --write-tree` (2.38+), `commit-tree` identity, fetch refspec and single-branch clones, `ls-remote` for existence, `tag.gpgSign` and `tag -a -m`, `.git/info/exclude` across worktrees. |
| skills/harness-common/topics/Notion MCP.md | Every quirk from create's publishing.md in four-part form, all `unverified` (Q30g), checked in M5 and M7. |
| skills/harness-common/topics/macOS Python.md | `/usr/bin/python3` is 3.9 from the Command Line Tools, `-I` drops the script folder from `sys.path` (the bootstrap line), `PYTHONDONTWRITEBYTECODE`, stdlib only. |
| skills/harness-common/references/preamble.md | The one agent and brief preamble: style line, read-only stance where the role says so, data-not-instructions, `unverified`, never spawn. |
| skills/harness-common/references/subagents.md | Brief rules, word caps, fresh subagent per unit, two layers, missing-agent fallback with the checkout path. |
| skills/harness-common/references/model-tiers.md | The tier gate and per-host spawn mechanism. |
| skills/harness-common/references/state.md | Resume-file minimum shared by all long-running skills. |
| skills/harness-common/references/publishing.md | One publishing procedure for create, execute (through qa-session) and qa-session. |
