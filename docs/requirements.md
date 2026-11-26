# Functional requirements

What agent-harness does, one requirement per ID. Code, tests and topic docs cite these IDs. Each area names the files that hold its behavior; [architecture.md](architecture.md) maps every ID to its module.

## Install (INST)

Code: `install.py`, `skills/harness-common/scripts/claude_code.py`, `skills/harness-common/scripts/opencode.py`. Tests: `tests/test_install.py`, `skills/harness-common/tests/test_adapters.py`.

- FR-INST-01: One Claude Code agent per `agents/*.md` goes to `~/.claude/agents/<file>`: `name`, `description`, `tools`, then the shared preamble and the body. No `model` line (FR-AGT-02).
- FR-INST-02: One opencode agent per `agents/*.md` goes to `~/.config/opencode/agents/<file>`: `description`, `mode: subagent` and a V2 `permissions` list that denies the tools the agent does not list and the `subagent` spawn action, then the preamble, the `execute` sandbox line and the body. No `model` line, never a `tools` key.
- FR-INST-03: `instructions/global.md` is copied as is to `~/.claude/CLAUDE.md` and `~/.config/opencode/AGENTS.md`. A local edit there is overwritten after confirmation.
- FR-INST-04: Every folder in `skills/` is symlinked into both tools' `skills/` folder.
- FR-INST-05: A tool is installed when its config folder exists or its binary is on `PATH`. `--claude 0|1` and `--opencode 0|1` override the detection.
- FR-INST-06: Install plans first. It writes only when the content differs and links only when the link target differs, so a second run changes nothing.
- FR-INST-07: `--check` prints the plan and `<n> change(s) needed`, writes nothing, and exits 1 on drift, 0 when clean.
- FR-INST-08: Changing anything that exists needs `y` at the prompt or `--yes`. Without a terminal and without `--yes` it changes nothing and exits 2. A declined prompt exits 3.
- FR-INST-09: `agent-harness-manifest.json` in each config folder lists what install wrote. A later run removes listed agents and skill links whose source is gone, and any skill link into this checkout whose target is gone. Links to other folders are never touched. `--check` reports the removals.
- FR-INST-10: A malformed agent file stops install before any write, exit 4, with the file and the bad key named: a missing fence, a line that is not `key: value`, a missing, unknown or duplicate key, `name` different from the file name, an unknown tier or tool, an empty body.
- FR-INST-11: Rendered frontmatter is valid YAML whatever the description holds: the description is written as a double-quoted string.
- FR-INST-12: A symlink where a file goes is replaced by the file, never written through. A real folder where a file goes moves to the backup folder (FR-INST-13).
- FR-INST-13: A real folder where a skill link goes moves to `agent-harness-backup/<timestamp>/` in the tool's config folder. It is never deleted.
- FR-INST-14: A missing `agents/` or `skills/` folder, or a missing source file, exits 4 with the path named, not a traceback.

## Plugin (PLG)

Code: `.claude-plugin/plugin.json`, `install.py` (`--plugin`), `skills/harness-common/SKILL.md`. Tests: `tests/test_repo_rules.py`, `tests/test_install.py`. Facts: [Claude Code](<../skills/harness-common/topics/Claude Code.md>) "Plugins".

- FR-PLG-01: The checkout root is one Claude Code plugin named `agent-harness`: `.claude-plugin/plugin.json`, every skill from the default `skills/` scan, the agents from `build/agents/`. Its skills run as `/agent-harness:<skill>`, its agents spawn as `agent-harness:<agent>`. `instructions/global.md` is not part of the plugin; a host that loads the plugin passes it itself.
- FR-PLG-02: `harness-common` is not user-invocable (`user-invocable: false`): it is in no Claude Code `/` menu, as a plugin or installed. Claude can still load it. That opencode ignores the key is `unverified`.
- FR-PLG-03: `install.py --plugin` renders one Claude Code agent per `agents/*.md` into `build/agents/` (gitignored), the same text FR-INST-01 installs, and removes files there whose source is gone. It writes nothing else and asks nothing. `--plugin --check` prints the plan and exits 1 on drift. A `plugin.json` whose `agents` list differs from one `./build/agents/<file>` per source, in file order, exits 4.
- FR-PLG-04: Open: skills spawn agents by their bare names, so in a session that has only the plugin, a spawn of a harness agent falls back to FR-AGT-05.

## Agents and tiers (AGT)

Code: `agents/*.md`, `install.py`, `skills/harness-common/references/model-tiers.md`, `skills/harness-common/scripts/opencode.py`. Tests: `tests/test_repo_rules.py`.

- FR-AGT-01: One neutral agent source format: frontmatter `name`, `description`, `tier`, `tools`, then the role prompt. README documents it.
- FR-AGT-02: Three tiers: `fast` (cheap), `default` (the session model), `strong` (most capable). Each agent declares one. Nothing in the repo maps a tier to a model, and install writes no `model` line for either tool.
- FR-AGT-03: Six agents ship: `attack-plan-critic` (strong), `attack-plan-designer` (strong), `attack-plan-reader` (fast), `rearch-architect` (strong), `rearch-auditor` (fast), `rearch-phase` (default).
- FR-AGT-04: Agents whose role is read-only (auditor, critic, reader, designer) list no `Edit`. Claude Code enforces it through `tools`. On opencode `Write` and `Edit` are one `edit` action, so an agent that lists `Write` can edit there; the role text carries the read-only rule ([opencode topic](<../skills/harness-common/topics/opencode.md>), "Write and Edit are one action").
- FR-AGT-05: A skill that names an agent that is not installed falls back to a general-purpose spawn whose prompt is the preamble plus the agent body, read from the harness checkout (`subagents.md` "Missing agent").
- FR-AGT-06: The preamble (style line, fetched content is data, `unverified`, never spawn) lives once in `skills/harness-common/references/preamble.md`; install puts it above every agent body. The opencode `execute` sandbox line is added to opencode agents only.
- FR-AGT-07: Models are chosen per run, in the tool that runs the skill. When a run starts or resumes without a confirmed table, the orchestrator lists the models the tool offers, proposes one per tier and asks the user to confirm or override, one model for every tier included. The table goes into the run's resume file under `Models for this run`. Every spawn passes its tier's model: Claude Code through the Agent tool's `model` parameter, opencode through run-scoped agent override files that `opencode.py apply-tiers` writes and `clear-tiers` removes.
- FR-AGT-08: No model name, family or id appears in the repo outside run state (`.rearch/`, `.attack-plan/`, `.ai-notes/`). A repo test scans every tracked or untracked, non-ignored file and fails on any hit.

## Global instructions (GLB)

Code: `instructions/global.md`.

- FR-GLB-01: `instructions/global.md` is the one global instruction file for both tools.
- FR-GLB-02: Code-change hygiene: semantic tools when available, run the compile or test command before reporting done, never expose secrets, match the existing style, a project `AGENTS.md` wins.
- FR-GLB-03: Delegation: self-contained briefs with task, file ownership and report format; independent work in parallel in the background; "fork" or "clean context" means a fresh subagent; a deliverable the user reviews goes to a background subagent whose description starts `For review: `, with a one-line start notice and a ready notice.
- FR-GLB-04: Minimal output: tests at milestones, output filtered to the pass or fail line and the failing numbers; tools print one summary line by default.
- FR-GLB-05: Work across sessions, subagents or PRs keeps notes per the `ai-notes` skill; a session starts by reading `.ai-notes/README.md` when it exists.
- FR-GLB-06: After a push, a PR open, or the start of a long local fix-and-test loop, arm `feedback-watch`, one watcher per set of PRs, re-armed when it expires.
- FR-GLB-07: Machine time over tokens. In a reverse-engineering task the user starts, read the binary or source. External tools are understood from their documented surface, and what it leaves open is settled by one scripted check.
- FR-GLB-08: Check the available skills before a task and name a fitting one in a delegated brief. Skills the harness does not ship (`frontend-design`, REA) are named "when available".
- FR-GLB-09: PR, issue and ticket numbers in replies are Markdown links.
- FR-GLB-10: Follow `writing-craft` before writing text a human reads and acts on.
- FR-GLB-11: Every rule reads right in both tools: the file names no tool where the rule is general.
- FR-GLB-12: A shell command suggested for the user to run is written with the `!` prefix, for example `! open prototype/storyboard.html`, so it runs in the session and its output joins the conversation. Commands the agent runs itself are unaffected. opencode support for the prefix is `unverified`.

## Notes (NOTES, skill ai-notes)

Code: `skills/ai-notes/SKILL.md`, `skills/harness-common/references/state.md`.

- FR-NOTES-01: A new session reads `.ai-notes/README.md`, then the area README, and resumes from its "State (start here)" section.
- FR-NOTES-02: Notes are kept when work spans more than one session, subagent or PR. The description and the body say the same.
- FR-NOTES-03: Notes live at `<repo root>/.ai-notes/<area-slug>/`, committed by default; kept private through `.git/info/exclude`, never `.gitignore` (`state.md` "Private state").
- FR-NOTES-04: An area README holds a dated "State (start here)" section (where the work stands, the `Next:` line, a `Models for this run` table when the work spawns), then goal, links, files, workstreams, to do, open questions and lessons. Beside it: `findings.md`, `<topic>.md` and dated deliverables.
- FR-NOTES-05: Writing rules for notes: summary first, reproducible evidence, absolute dates, verified apart from inferred, retracted theories kept as such, user decisions dated with their reason, one fact in one place, superseded text marked instead of deleted.
- FR-NOTES-06: Lifecycle: update as the work moves, one ticket per workstream, the stop point recorded when a session stops, rows ticked after a merge.
- FR-NOTES-07: One orchestrator owns the notes. Subagents get self-contained prompts that point at the notes. A subagent in a worktree returns text and the orchestrator writes it. Reports are claims to check.
- FR-NOTES-08: Handoff to a new session: on request (`/handoff`, "hand this off", "continue in a new session"), write `.ai-notes/<area>/handoff-<slug>.md` as a prompt the new session follows alone (where to read, verified facts, the task and its stop point, the user's rules, the user's notes word for word, no own conclusions), link it from "State (start here)", and start the session through the host's session tool when one is available, else print the prompt.
- FR-NOTES-09: `/handoff [notes]` is the skill `skills/handoff/`, the one source of that command (no `~/.claude/commands/handoff.md`). Its body points at the ai-notes handoff steps without repeating them, and passes the user's notes word for word: `$ARGUMENTS` in Claude Code; where a host leaves the placeholder unreplaced (opencode, `unverified`), the notes are the user's words in the request.

## Writing (WRIT, skill writing-craft)

Code: `skills/writing-craft/SKILL.md`.

- FR-WRIT-01: Before writing: the reader, their moment, the one job of the text, their vocabulary.
- FR-WRIT-02: The form follows the reader's task (sequence, decision, reference, explanation). A precondition, a warning and the expected result sit beside the action they belong to.
- FR-WRIT-03: Word rules: the exact word, the reader's vocabulary, one term per concept, no spec ids, no placeholders in live steps.
- FR-WRIT-04: Facts are checked before they are written; the rest is labelled as an assumption with the check that settles it.
- FR-WRIT-05: Revision starts from the point where the reader would fail, then cuts.
- FR-WRIT-06: The rules cover text a human reads and acts on. Agent-to-agent text (briefs, subagent reports, audit reports, run state) is exempt by name. attack-plan-create, execute, qa-session and storyboard cite the skill for their human-read output.
- FR-WRIT-07: Each rule is stated once, and the examples are domain-neutral.

## Attack plan create (APC)

Code: `skills/attack-plan-create/`, `agents/attack-plan-*.md`, `skills/harness-common/scripts/markdown.py`. Tests: `skills/attack-plan-create/tests/`.

- FR-APC-01: Work folder `.attack-plan/<slug>/` with `STATE.md`, `gates.json`, `ledger.md`, `sources/`, `draft/` and `audit/` (`references/state.md`); committed by default, `.git/info/exclude` to keep it private.
- FR-APC-02: Eight stages: intake, sources, product, product-review, technical, milestones, audit, publish. `gate.py open` refuses a section while a gate of the same or an earlier stage is neither `approved` nor `not reviewed`.
- FR-APC-03: A seven-step loop per section: open, draft, challenge (a fresh critic each round), grill one question at a time, record the grilling, review in full, approve or skip. Three rounds with blocking findings go to the author.
- FR-APC-04: The author can speed up, skip reviews or draft ahead. A skipped section is `not reviewed`, and each stage end lists such sections.
- FR-APC-05: Approval stores a SHA-256 over one or more (file, heading) pairs. `status` and `verify` flag a later edit. Sections are sliced by `markdown.py`, which ignores headings inside code fences. A `gates.json` in the older one-pair format loads and is migrated on the next write, approvals kept. A gate opened with no file has no hash and no drift check.
- FR-APC-06: `reopen` with a reason returns a gate to `drafting` and marks every later approved gate `stale`, by list order; `open` accepts a `drafting`, `stale` or `not reviewed` gate.
- FR-APC-07: `verify` flags technical drafts written before the technical stage opened.
- FR-APC-08: `gate.py` rejects a bad command line with a named message and exit 2 (a non-numeric `--rounds`, a missing positional), and refuses a state change with `REFUSED: <reason>` on stderr and exit 1.
- FR-APC-09: Three agents with role briefs (`references/briefs.md`): reader (fast), critic (strong), designer (strong). Every brief names its output path, or says it writes no file, and its word cap.
- FR-APC-10: Stage 1 records the SHA of `origin/<default branch>`. Every code read uses that commit, never the working tree. The audit stage checks the commits since then in the touched paths.
- FR-APC-11: `check_draft.py <draft folder> [--product]`: required sections in order, questions as Q<n> with Context, Question and Recommendation, no estimates in table headers, no Option A-D, no decision log, no `P1`, `risk 1` or `proposed` labels, balanced backticks, the milestones section by its numbered heading, code-term warnings in the product part (controller, endpoint, serializer, migration, ORM, SQL), and `--product` rejects early technical content. Output `PASS|WARN|FAIL file: message`, exit 1 on a FAIL or a bad command line.
- FR-APC-12: Questions to the author follow `references/questions.md`: one at a time, each with a recommendation and a safe default.
- FR-APC-13: One task block per PR with fixed headings (`references/executable-plan.md`): title `[<code> M<n>-<k>] <title>`, base, files, rule everywhere, invariants and tests, edge cases, ordering, reviewers, context for an outside reviewer, rationale, QA, depends on, ticket. `check_draft.py --tasks <file> [--milestone N]` checks the schema, one project code, and the task order per milestone.
- FR-APC-14: Publishing follows `skills/harness-common/references/publishing.md`: repo Markdown (default) or a document tool, read back after each write, reviewer edits kept, commit only when the author asks. The drafts stay the source of truth.
- FR-APC-15: The publish stage re-reads the published pages, reopens each changed section and offers every later stale section for review.
- FR-APC-16: Risks live in section 5 of the attack plan; `check_draft.py` requires it.
- FR-APC-17: `draft/alternatives.md` holds the ruled-out designs. It is internal and never published.
- FR-APC-20: The `references/state.md` example matches the stage numbers (technical solution is Stage 4).

FR-APC-18 and FR-APC-19 are retired IDs.

## Attack plan milestone execute (APE)

Code: `skills/attack-plan-milestone-execute/`, `skills/harness-common/scripts/git.py`, `skills/harness-common/scripts/github.py`. Tests: `skills/attack-plan-milestone-execute/tests/`, `skills/harness-common/tests/test_git.py`.

- FR-APE-01: Inputs: the attack plan, the milestone, optional additional notes asked once. Tracker tickets are found from the plan; a ticket wins over its task block when they disagree.
- FR-APE-02: Input readiness is graded before any code (`resources/input-readiness.md`): `gate.py status` when the plan has a `gates.json` (gates of stages intake to milestones plus this milestone's `tasks-m<n>` approved, `not reviewed` an accepted gap), then `check_draft.py --tasks <file> --milestone <n>`. A blocking gap stops the run unless the user accepts it.
- FR-APE-03: Two or three parallel read-only subagents audit the tickets against `origin/<default branch>`. Each surprise goes into the document that owns it before the first PR opens.
- FR-APE-04: One fresh subagent per PR. Stacked draft PRs are opened in number order, titled `[<code> M<n>-<k>] <title>`, one project label each.
- FR-APE-05: A per-milestone `subagent-rules.md`, built from `resources/subagent-rules-template.md`: git rules, human-only gates, local environment notes, a growing "Learned" section.
- FR-APE-06: After each push the orchestrator arms `feedback-watch` in `pr` mode on the stack with `--until bots`, and `--reviewer` for a review bot that reviews every push. Execute does not call `watch.py` itself.
- FR-APE-07: A stack behind the default branch goes red in unrelated jobs. The fix merges the default branch into the bottom of each stack and merges up, through `build_integration_branch.py --from target --push` when there is no checkout.
- FR-APE-08: `build_integration_branch.py --target B --heads A,B [--from target|<branch>] [--default B] [--message T] [--push] [--repo P] [--remote R]` merges heads with `git merge-tree --write-tree` and `commit-tree`, no checkout. It fetches with explicit refspecs, skips a head already in the branch, checks git 2.38 or later and the commit identity before the first commit, reads the target's existence with `ls-remote` and never from a failed fetch, and pushes a plain fast-forward only with `--push`. The last line is `INTEGRATION_BRANCH_EVENT {json}` with `status` `pushed`, `built`, `unchanged`, `conflict` (with `head` and `files`) or `failed` (with `error`).
- FR-APE-09: A review pass (`resources/review-pass.md`) lists the unresolved threads of every PR with `review_threads.py list`, decides FIX or REPLY per thread with evidence, sends FIX rows to one fresh subagent per PR from the bottom of each stack, merges up, then resolves the threads a bot started.
- FR-APE-10: Never post as the user, except the reply in a thread a bot started (FR-APE-15). Never mark a PR ready, never merge, never rebase or force-push. PR subagents never post or resolve anything.
- FR-APE-11: Notes in `.ai-notes/<project>-<milestone>/`: a README whose "State (start here)" holds the PR table, pending items by owner, the `Models for this run` table and the `Next:` line; `subagent-rules.md`; `review-pass-<date>.md`. A later session resumes from "State (start here)".
- FR-APE-12: QA before merge: an integration branch of every stack top and unstacked PR, a draft QA PR, seed data in its own PR, and the `qa-session` skill run in the orchestrator to build the QA page.
- FR-APE-13: The task block's "Context for an outside reviewer" goes into each PR subagent's brief as the opening of the PR description, and the orchestrator checks the PR body opens with it.
- FR-APE-14: `gh stack` is used when installed; otherwise each PR targets the branch below it and its body names that PR.
- FR-APE-15: A thread a bot started and decided REPLY (no code change, for example "no change needed, because ...") gets its reply posted by the orchestrator under the user's account with `review_threads.py reply`, which then resolves it. The run's exit goal is green CI on every PR and no unresolved bot thread, reached without the user. Threads a person started are never replied to or resolved: their fix commits and reply texts go to the user.

## Feedback watch (FW)

Code: `skills/feedback-watch/`, `skills/harness-common/scripts/github.py`. Tests: `skills/feedback-watch/tests/`, `skills/harness-common/tests/test_github.py`.

- FR-FW-01: `watch.py pr N... [--repo OWNER/NAME]` polls every `--interval` seconds (default 120, must be above 0) and prints one line per PR when its head SHA, CI running or done, failing names, missing reviewers, unresolved count or human count changes. The first round prints every PR, so a re-armed watcher loses nothing.
- FR-FW-02: Each round reads per PR its state, head, check rollup, reviews with their commit and threads with their first comment's author kind, every page of each, in one GraphQL call plus one per further page of 100.
- FR-FW-03: Checks: the newest run per workflow and name wins, by `startedAt` (a queued run without one counts as newest); a cancelled run loses to any other run of the check; a check whose only run is cancelled is failing, shown as `<name> (cancelled)`. `FAILURE`, `TIMED_OUT` and `STARTUP_FAILURE` fail; status contexts `PENDING` and `EXPECTED` are pending, `FAILURE` and `ERROR` fail.
- FR-FW-04: An empty rollup counts as running unless `--allow-no-checks`. Done needs two rounds in a row with the same state, except with `--once`.
- FR-FW-05: `--reviewer LOGIN` (repeatable): a review counts when it is on the head commit and approved, commented or changes-requested; a dismissed review does not. Logins compare case-insensitively with a trailing `[bot]` stripped.
- FR-FW-06: Stop rules: `ALL DONE` (`--until all`), `CI DONE` (`--until ci`) or `BOTS DONE` (`--until bots`, human threads may stay open), exit 0; `--once` not done prints `NOT DONE`, exit 1; `--timeout` minutes prints `TIMEOUT`, exit 3; bad arguments exit 2.
- FR-FW-07: A failed `gh` call skips that PR for the round, with a `skipped` line on stderr. Three failing rounds in a row for one PR, or no repository at start, print `GH FAILING: <cause>` on stdout and exit 4, since Monitor reads stdout only.
- FR-FW-08: A merged or closed PR prints `#N merged, stopped watching` or `#N closed, stopped watching` once and is no longer polled. When none is left open, the watcher prints `ALL DONE`.
- FR-FW-09: `watch.py local --cmd C... [--path P...] [--interval 2] [--debounce 1] [--cmd-timeout 600] [--timeout MIN] [--once]` runs the commands with stdin closed and prints `PASS <command>`, or `FAIL <command> (exit N)` or `(timed out)` with the last 15 ANSI-stripped lines, on the first run, on a flip, and when a failure's exit code or tail changes. A command past `--cmd-timeout` is killed with its children.
- FR-FW-10: Change detection polls modification time and size, and skips `.git`, `.ai-notes`, `.attack-plan`, `.rearch`, dependency folders, caches and build output. The file snapshot is taken after the commands finish, so files they write do not retrigger them.
- FR-FW-11: `local --once` prints `ALL PASS` (exit 0) or `FAILED: <commands>` (exit 1).
- FR-FW-12: `watch.py` only reads: GraphQL queries through `github.py` and the shell commands it is given. It never writes to GitHub or the repository.
- FR-FW-13: Claude Code runs the watcher under the Monitor tool with `timeout_ms` 1800000. opencode runs it as a background shell job with `--timeout` (pr mode) or `--once` (local mode), its output in a log file outside the repository.
- FR-FW-14: `SKILL.md` holds the advice for reading a CI failure: infrastructure failures, job logs of a running workflow, a stack behind the default branch, failures that also happen on the default branch.
- FR-FW-15: `SKILL.md` states what the code does: every line, every stop line and exit, the fine conclusions, the first-round print, local mode running until stopped.

## QA session (QA)

Code: `skills/qa-session/`, `skills/harness-common/references/publishing.md`. Tests: `skills/qa-session/tests/`.

- FR-QA-01: Three modes chosen from the state: Create (no page), Rework (a page and no running session), Live edit (a session is running). A page with ticks or findings is never rebuilt without asking.
- FR-QA-02: Inputs: the spec, the code at a commit, the seed, the environment, and an optional publishing target, asked one question at a time.
- FR-QA-03: Session folder `.ai-notes/qa-<slug>/`: `README.md` (its "State (start here)" holds the models table and the `Next:` line), `sources.md`, `decisions.md`, `rework-log.md`, `derivation.md` (the Builder's source per check, never read by the Verifier). A rework copies the current page to `.ai-notes/.qa-previous/<slug>.md`, outside the session folder, so no subagent reads it, and deletes it after publishing. The page holds no history.
- FR-QA-04: Create: record sources, Builder subagent, `check_page.py`, Verifier subagent, show the shape and counts, publish after the go-ahead.
- FR-QA-05: Rework: a fresh Builder re-derives the page without the previous one; ticks and findings carry over by scenario title and check text; the change report goes to `rework-log.md`.
- FR-QA-06: Live edit: targeted edits, ticks kept, a tick removed when its check changes meaning, `check_page.py --live` after.
- FR-QA-07: The page has three parts: the setup for the lead developer in a collapsed block (seed, environment, users, values to check before the session); numbered scenarios, each with all the context its driver needs (persona, start, steps, expected results); an empty Findings section with no table.
- FR-QA-08: Every on-screen word is the exact label that scenario's persona sees, in their UI language, traced to the code that renders it. The template, the setup checklist and the briefs state it.
- FR-QA-09: `check_page.py <page> [-v] [--live]`: FAIL on emoji, internal ids, angle or bracket placeholders, TODO/TBD/FIXME/XXX, a malformed scenario heading, a scenario whose first line is not the persona line `As <persona> (`<email>`):`, scenario numbers out of order, no collapsed setup, no Findings section, or a non-empty Findings section without `--live`; WARN on bare "today" or "now", "(cont.)" and a scenario without checkboxes. Exact labels in backticks are exempt from the id and word checks. Fence-aware through `markdown.py`. One summary line, findings with line numbers under `-v`, exit 1 on a FAIL.
- FR-QA-10: Publishing follows `skills/harness-common/references/publishing.md`, with the published page as the source of truth; tool notes go to `sources.md`.
- FR-QA-11: Setup checklist: an idempotent seed, one labelled line per check, "found N of N", values printed before the session, no passwords on the page, the deploy confirmed before seeding.
- FR-QA-12: Builder and Verifier are `general` spawns on tier `strong`, listed in a `Spawns` table, with the filled brief as the whole prompt and every path absolute.
- FR-QA-13: Without subagents, the orchestrator runs the briefs itself in separate passes and notes it in the README.
- FR-QA-14: Stopping writes "State (start here)" and prints a resume prompt.
- FR-QA-15: At Create the Findings section is empty and has no table; a non-empty one is a FAIL.

## Rearchitect (RA)

Code: `skills/rearchitect/`, `agents/rearch-*.md`.

- FR-RA-01: A session resumes from `.rearch/STATE.md`; no `.rearch/` means Stage 0. Before each stage or phase the orchestrator states its plan in 3 to 8 lines, and before an action outside it, why.
- FR-RA-02: A `Spawns` table: auditor `fast`, architect `strong`, phase `default`, resolved through the tier gate.
- FR-RA-03: Stage 0: a clean tree (caches the baseline creates ignored), branch `rearch/<date>`, annotated tag `rearch-base`, an existing branch or tag handled at a gate, baseline commands that leave no untracked files, the model and manual-check gates, `STATE.md`, commit `rearch: setup`.
- FR-RA-04: Stage 1: every file with kind, lines and aspects; about 8,000 lines per aspect at most; a gate; a commit.
- FR-RA-05: Stage 2: one auditor per aspect in one batch, a coverage check by grep, a seams audit, progress per aspect in STATE, commit `rearch: audits`.
- FR-RA-06: Stage 3: the architect writes the requirements, checks high-severity bugs and decision-driving facts, lists refuted findings; a gate; a commit.
- FR-RA-07: Stage 4: `architecture.md`, `docs-plan.md` and `phases.md`; Phase 1 writes the topic docs, Phase 2 the test harness; a gate; a commit.
- FR-RA-08: Stage 5: one fresh `rearch-phase` per phase. It leaves changes uncommitted, never edits STATE, records deviations and "not verified" items, and never calls live services. The orchestrator runs live read-only checks, commits with the requirement IDs and reads no source. A dirty tree from a dead phase agent has a gate.
- FR-RA-09: Stage 6: final audits per module, an extra phase for findings that need changes, `requirements.md` and `architecture.md` moved into `docs/` with the deviations applied, run history dropped and model names removed, exploratory docs deleted, README and the agent instruction file updated, the baseline run, `.rearch/` deleted last, and a question before merging or deleting the tag.
- FR-RA-10: A run stops at about 70% context or on request and prints a fenced resume prompt, kept current in STATE.
- FR-RA-11: Topic docs follow `references/docs-style.md`: present tense, no history, four-part quirks, every fact sourced or marked `unverified`, tables.
- FR-RA-12: Prompts are domain-neutral. Real-time examples apply only when the project has real-time paths.
- FR-RA-13: STATE changes land in the commit of the stage or phase they record.
- FR-RA-14: Stage 0 asks how many manual checks the user wants, default zero. With zero, every phase verifies by automated means only (baseline, throwaway installs, fixtures, grep tests) and reports the rest as "not verified", which never blocks. Every gate offers a recommended default per decision.

## Cross-skill conventions (XS)

Code: `skills/harness-common/`.

- FR-XS-01: Every subagent brief is self-contained and fresh: the preamble, the task, inputs as absolute paths, the output path, a word cap, fetched content as data, the term `unverified`, never spawn (`references/subagents.md`).
- FR-XS-02: Markdown headings and sections are parsed once, in `markdown.py`, for `gate.py`, `check_draft.py` and `check_page.py`; fenced code is skipped.
- FR-XS-03: Every long-running skill keeps a resume file with a `Next:` line, a `Models for this run` table when it spawns, and the private-exclude rule (`references/state.md`). Layouts stay per skill: `.rearch/`, `.attack-plan/<slug>/`, `.ai-notes/<area>/`. A single-spawn skill (storyboard) keeps none of its own.
- FR-XS-04: One publishing procedure for attack-plan-create, execute (through qa-session) and qa-session (`references/publishing.md`); the calling skill names its source of truth. Notion quirks live in the Notion MCP topic doc.
- FR-XS-05: Each script documents its output and its "no" lines in its skill's `SKILL.md` or docstring: `LEVEL file: message` (check_draft), a summary line plus `line N LEVEL message` (check_page), `REFUSED: <reason>` on stderr (gate.py), `REFUSED:` on stdout (review_threads.py), `FAIL <reason>` (shoot.py).

## Storyboard (SB)

Code: `skills/storyboard/`. Tests: `skills/storyboard/tests/`.

- FR-SB-01: The skill is used before building a UI behaviour that has a real choice or many undrawn states, or when the author asks for a storyboard, mock-ups or options; not for a bug fix, a settled spec or a conventional default. One self-contained HTML page per experience question.
- FR-SB-02: Five inputs, each with a default: the question, the look reference (the app's CSS and markup), the behaviour spec (the matching requirements sections), the current code (the matching screens), earlier storyboards (`prototype/*-storyboard.html`). A missing one is asked, one question at a time. Without a look reference the skeleton's tokens are used and the page says so.
- FR-SB-03: Process: frame the scenarios and the real choices; delegate one Builder in the background (description starts `For review: `, the filled brief is its whole prompt, no conversation, no preferred option); check with `shoot.py` in both themes and a cold read, fix in place; hand over (what, where, how to open, what to look at first) and stop.
- FR-SB-04: On the author's answers, the requirements doc gets each dated decision, each requirement change under its id, a design note per question naming the losing options and why, and one line that the storyboard is design history. The storyboard gets one "Decided on <date>" line and is not reworked. A change of mind is a new dated decision; a new question gets a new storyboard. A requirements doc in a document tool is written through `publishing.md`.
- FR-SB-05: Page order: title and one line, summary (recommended, requirement changes with ids, open questions), the design in one picture, one section per scenario, "Keyboard path", edge cases, rejected options, footer.
- FR-SB-06: Page rules: one file, inline CSS and JS, no network request, opens by double-click; bundled fonts by a relative path, else system fonts; invented data only, stated on the page; the look reference's tokens and parts at real sizes; options side by side only where the choice is real, exactly one "Recommended" with a one-line why, each loser with a one-line reason; the project's own design rules win.
- FR-SB-07: The page follows the system appearance, has one theme toggle, and `?theme=light|dark` wins over both. Every frame works in both themes.
- FR-SB-08: A greyscale row when marks or icons are part of the choice, and a "Preview reduced motion" toggle when anything moves. The OS reduced-motion setting stops every animation, as the toggle does.
- FR-SB-09: `shoot.py <page.html> [--out DIR] [--width 1440] [--height 6000] [--theme light|dark|both]`: per theme one `--dump-dom` pass at `<width>x900` reads `data-h` from `<html>`, then one screenshot at that height. Screenshots go to `<tmp>/storyboard-shots/` by default, never into the project. One `path  WxH` line per screenshot.
- FR-SB-10: Browser lookup: `$CHROME` when it names an executable file, else `chrome-headless-shell` on `PATH`, else the newest Playwright headless shell for the host architecture under `$PLAYWRIGHT_BROWSERS_PATH` or `~/Library/Caches/ms-playwright`. Never a browser app. Each run uses its own temporary profile.
- FR-SB-11: Every expected failure prints one `FAIL <reason>` line and exits 1, no traceback: no shell (with the install command), page missing, `$CHROME` not executable, a Chrome run past its 120 s timeout, a failed dump, a failed screenshot. The reason is the last stderr line as plain text.
- FR-SB-12: A dump without `data-h` uses `--height`, and the line ends `(no data-h, used --height)`. A page taller than 200000 px is shot at 200000 and the line ends `(clipped from <H>)`.
- FR-SB-13: The storyboard lives at `prototype/<topic>-storyboard.html` next to the look reference, or where the project keeps design files; an asset review is `preview.html` beside the asset. It is committed only when the user asks.
- FR-SB-14: The Builder is one `general` spawn on tier `strong`, in a `Spawns` table, resolved through the tier gate. Its brief meets the brief minimum with every path absolute, points at SKILL.md "Rules" instead of restating them, runs `shoot.py` and a scan for real data before it reports, and reports in under 150 words.
- FR-SB-15: writing-craft applies to the page text and its review. `frontend-design` is loaded when available, only to match the look reference; without it the Builder copies the look reference's tokens and parts.
- FR-SB-16: The skill keeps no resume file. With an ai-notes area, the models table and the `Next:` line go in its "State (start here)"; otherwise the tier gate runs in the session and the hand-over ends with a fenced resume prompt naming the storyboard path.

## Non-functional

- NFR-01: Scripts and `install.py` use only the Python 3.9 standard library and run as `/usr/bin/python3 -I`.
- NFR-02: A fresh Mac needs only the Command Line Tools (git, python3). `build_integration_branch.py` needs git 2.38 or later and names the version it found when it is older. macOS only.
- NFR-03: Default script output is minimal: one line per change or result and a summary; detail behind `-v`.
- NFR-04: Every script, `install.py` included, has a unittest suite run as `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -m unittest discover -s <folder>`; `install.py` imports without running.
- NFR-05: Running the tests leaves no untracked files; `.gitignore` covers `__pycache__/` and `*.pyc`.
- NFR-06: Install is idempotent, and `--check` writes nothing.
- NFR-07: Skill edits take effect at once through the links; changes to `agents/`, `instructions/`, the preamble, or a skill folder added, renamed or removed need an `install.py` run. README says so.
- NFR-08: Everything installed works in Claude Code and opencode.
- NFR-09: One fact in one place across SKILL.md files, references, briefs and agent bodies: prompt size is a cost per session and per subagent.
- NFR-10: Long skills stop near 70% context with a resume prompt; subagent reports are word-capped; orchestrators read summaries, not full reports.
- NFR-11: Watcher load: pr mode every 120 s by default, one GraphQL call per PR per round plus one per further page; local mode a 2 s poll and a 1 s debounce.
- NFR-12: Scripts write to a remote only where a skill rule allows it: `build_integration_branch.py` pushes only with `--push`, a plain push, never forced; `review_threads.py resolve` and `reply` write only to threads a bot started. `watch.py` and every other script only read.
- NFR-13: Two layers at most: the orchestrator session spawns subagents, and subagents never spawn. Installed agents get no spawn tool on either host, and every skill that delegates says so.
- NFR-14: Storyboard checks never open a window or take the author's focus: headless shell only, a temporary profile per run, screenshots in the temp folder.
- NFR-15: One `shoot.py` run is bounded: two Chrome runs per theme, each under a 120 s timeout and a 3000 ms virtual-time budget.

## Constraints from external systems

Each constraint is a fact in a topic doc under `skills/harness-common/topics/`, with its source or marked `unverified`.

- CON-CC-01: Claude Code agent frontmatter holds `name`, `description`, `tools` (a restriction list) and an optional `model` (a family alias, a full id, or `inherit`). [Claude Code](<../skills/harness-common/topics/Claude Code.md>) "Agent files".
- CON-CC-02: The Monitor tool turns each stdout line of a command into a notification; `timeout_ms` is at most 1800000. "Monitor tool".
- CON-CC-03: A Claude Code subagent can spawn subagents unless its `tools` leave out `Agent`. The harness agents leave it out, and briefs for `general-purpose` spawns say never spawn. "Nested spawns".
- CON-CC-04: `frontend-design` is a Claude Code plugin skill under `~/.claude/plugins/cache/`; the harness neither ships nor installs it. "Other plugins".
- CON-CC-05: A plugin's manifest is `.claude-plugin/plugin.json`; its skills and agents are namespaced `<plugin>:<name>`, so a plugin skill never replaces a personal skill of the same name: both load and bare `/<name>` runs the personal one. The `agents` key replaces the `agents/` scan and takes file paths only. "Plugins".
- CON-OC-01: opencode agent files use V2 frontmatter: `description`, `mode`, `permissions`, an optional `model` as `provider/model`; the name comes from the file name. A file with `permissions` drops V1 keys such as `tools`. [opencode](<../skills/harness-common/topics/opencode.md>).
- CON-OC-02: opencode has no Monitor tool; a background shell job notifies the session only when it exits. "No Monitor tool".
- CON-GH-01: A check rollup mixes `CheckRun` (`name`, `status`, `conclusion`) and `StatusContext` (`context`, `state`). [GitHub](../skills/harness-common/topics/GitHub.md) "Check rollup".
- CON-GH-02: Reruns leave the old runs in the rollup; the newest by start time wins, and a queued rerun may have no start time (`unverified`).
- CON-GH-03: Checks register seconds after a push; an empty or partial rollup is not done.
- CON-GH-04: Bot logins differ between REST (`<name>[bot]`) and GraphQL (`<name>`).
- CON-GH-05: GitHub lists PRs newest first; a milestone's PRs are opened in number order.
- CON-GH-06: A stack behind the default branch goes red together in unrelated jobs; the exact mechanism is `unverified`.
- CON-GIT-01: `git merge-tree --write-tree` needs git 2.38 or later. [git](../skills/harness-common/topics/git.md).
- CON-GIT-02: `commit-tree` needs a configured identity.
- CON-GIT-03: With `tag.gpgSign=true`, `git tag <name>` fails without a message; `git tag -a <name> -m <message>` works.
- CON-GIT-04: In a single-branch clone, `git fetch <remote> <branch>` does not create `<remote>/<branch>`; an explicit refspec does.
- CON-GIT-05: `.git/info/exclude` lives in the common git folder and covers every worktree.
- CON-NOTION-01: The Notion MCP write and update quirks, all `unverified`: [Notion MCP](<../skills/harness-common/topics/Notion MCP.md>).
- CON-CHROME-01: A browser app started with `--headless` still registers with macOS and takes focus (`unverified`). [Chrome headless shell](<../skills/harness-common/topics/Chrome headless shell.md>).
- CON-CHROME-02: Playwright puts the shell at `~/Library/Caches/ms-playwright/chromium_headless_shell-<build>/chrome-headless-shell-mac-<arch>/chrome-headless-shell`, not on `PATH`; `PLAYWRIGHT_BROWSERS_PATH` moves the cache.
- CON-CHROME-03: `--dump-dom` with `--virtual-time-budget=3000` returns the DOM after the page's scripts and `document.fonts.ready` ran; `?theme=` and `matchMedia` work headless.
- CON-CHROME-04: Screenshots up to 200000 px tall are painted whole; taller ones are not measured.
- CON-CHROME-05: Fonts by a relative path load from a `file://` page in the headless shell.
