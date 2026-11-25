# Audit: feedback-watch

## Coverage
| File | Lines | Read fully |
|---|---|---|
| README.md | 34 | yes (feedback-watch row at :19) |
| instructions/global.md | 20 | yes (rule at :12) |
| skills/feedback-watch/SKILL.md | 98 | yes |
| skills/feedback-watch/scripts/watch.py | 317 | yes |
| skills/feedback-watch/tests/test_watch.py | 390 | yes |

Tests run: 48 OK (0.14 s).

## Functional behavior
- F1: `watch.py pr N... [--repo]` polls each PR every `--interval` s (default 120) and prints one line per PR when its state tuple (sha7, pending, failing, missing, unresolved) changes. First round prints every PR. Evidence: watch.py:84-99,125-127,161-182. Status: active.
- F2: Head commit, check rollup via `gh pr view --json headRefOid,statusCheckRollup`; reviews via REST `pulls/N/reviews?per_page=100`; threads via GraphQL `reviewThreads(first:100)`. Evidence: watch.py:149-158. Status: active.
- F3: Check logic: newest run per (workflowName, name); CANCELLED runs dropped; non-COMPLETED = pending; FAILURE/TIMED_OUT/STARTUP_FAILURE = failing; commit-status contexts PENDING/EXPECTED = pending, FAILURE/ERROR = failing. Evidence: watch.py:21-23,42-76. Status: active.
- F4: Empty rollup counts as pending unless `--allow-no-checks`. Evidence: watch.py:88. Status: active.
- F5: `--reviewer` (repeatable): a review whose `commit_id` equals head counts. Login compare is case-insensitive and ignores `[bot]`. Evidence: watch.py:79-97. Status: active.
- F6: Stop rules: all PRs fetched this round and done -> `ALL DONE`/`CI DONE`, exit 0; `--once` not done -> `NOT DONE`, exit 1; `--timeout` minutes -> `TIMEOUT`, exit 3. Evidence: watch.py:173-181. Status: active.
- F7: A failed gh call or parse error skips that PR for the round, message to stderr, loop goes on. Evidence: watch.py:166-169. Status: active.
- F8: `watch.py local --cmd ... [--path] [--interval 2] [--debounce 1] [--once]`: runs commands, prints `PASS`/`FAIL (exit N)` plus last 15 ANSI-stripped lines only when a command's pass/fail state flips (first run prints too). Evidence: watch.py:185-215,255-273. Status: active.
- F9: File change detection by polling `(mtime_ns, size)` snapshot, skipping 19 dirs names, debounce via `Trigger`. Evidence: watch.py:16-20,218-252. Status: active.
- F10: `local --once` prints `ALL PASS` (exit 0) or `FAILED: <labels>` (exit 1). Evidence: watch.py:256-263. Status: active.
- F11: Read-only: script never writes to GitHub or repo. Evidence: only `gh pr view`, `gh api` GET, `gh api graphql` query, `gh repo view` (watch.py:146-156). Status: active.
- F12: Global rule: arm the watcher after push, PR open, or long local loop; one watcher per PR set; re-arm on expiry. Evidence: instructions/global.md:12. Status: active.

## External facts and quirks
- X1: Checks appear a few seconds after a push; an empty rollup right after push must not read as done. Workaround: empty rollup = pending (watch.py:88, test_watch.py:109-111). Source: code, test.
- X2: Re-run workflows leave old runs in the rollup; the newest run per (workflow, name) wins by `startedAt`/`createdAt`. Workaround watch.py:50-60; tests :63-71. Source: code, test.
- X3: Cancelled runs are superseded duplicates (concurrency cancel). Dropped at watch.py:54. Source: code, test :60. Unverified for the case where the only run is cancelled (see B2).
- X4: `statusCheckRollup` mixes CheckRun (`status`/`conclusion`, `name`) and StatusContext (`state`, `context`). Handled at watch.py:42-47,67-75. Source: code, test :77-83.
- X5: Review commit coverage is read from REST `commit_id`, not from `gh pr view`. Reason: `gh pr view` reviews carry no per-review commit in the used fields. Source: code (unverified reason).
- X6: Bot logins differ between REST (`claude[bot]`) and GraphQL (`claude`); normalization strips `[bot]`. watch.py:79-81. Source: code, tests :91-97.
- X7: Finished job logs are available mid-run through `gh api .../actions/jobs/<id>/logs`; `gh run view --log` waits for the whole run. SKILL.md:79. Source: SKILL text, unverified.
- X8: "runner lost communication" annotation = infra failure, job with no failed step. SKILL.md:78. Source: SKILL text, unverified.
- X9: CI runs the workflows of the default branch; stacked PRs behind it go red together. SKILL.md:80. Source: SKILL text, unverified. (Statement is imprecise: `pull_request` workflows run from the merge ref, `pull_request_target` from the base.)
- X10: Claude Code Monitor tool turns stdout lines into notifications, max `timeout_ms` 1800000. SKILL.md:55-59. Source: unverified (tool not in repo).
- X11: opencode has no Monitor tool. SKILL.md:61. Source: unverified.
- X12: `startedAt` of a queued check run may be a zero date in gh output. Not handled; unverified (see B4).

## Doc and code inconsistencies
- D1: SKILL.md:14 says run with `/usr/bin/python3 -I -u`. Script shebang is `/usr/bin/python3` without `-u` (watch.py:1), but `emit` flushes (watch.py:299), so `-u` is redundant for stdout. Stderr is unbuffered anyway. Minor.
- D2: SKILL.md:44 says "A line prints only when a command changes between pass and fail". Code also prints on the first run of every command (watch.py:209) and a FAIL to FAIL change with different output prints nothing (see B5). Doc hides this.
- D3: SKILL.md:25 `--timeout MINUTES` and "exit with TIMEOUT" are pr-only; local has no timeout or stop (watch.py:268, loops forever). SKILL.md:92-96 stop section lists local only for `--once`; correct but never says local runs until killed.
- D4: SKILL.md:63 says "the watcher's first round prints the current state of every pull request again, so nothing is lost when you re-arm". True (previous = {}). Verified.
- D5: SKILL.md:37 "Only the head SHA, CI running or done, failing names, missing reviews, unresolved count are compared." True; the dict also holds same keys. Verified.
- D6: SKILL.md:93 "ALL DONE: ... no pending or failing check". True only for FAILURE/TIMED_OUT/STARTUP_FAILURE; ACTION_REQUIRED, STALE, NEUTRAL, SKIPPED, CANCELLED count as fine (watch.py:21). Doc overstates.
- D7: README.md:19 and SKILL description match code. Verified.

## Assumptions to revalidate
- A1: At most 100 review threads per PR (watch.py:26). Over that, unresolved count is undercounted; ALL DONE can fire early.
- A2: At most 100 reviews per PR (watch.py:152, no pagination). Over that, the head-commit review may be on page 2; watcher waits forever.
- A3: `gh` is on PATH, authenticated, and the current folder is a repo when `--repo` is omitted (watch.py:146). Failure at start exits with message; failure later is silent on stdout (B3).
- A4: `/usr/bin/python3` exists (shebang, SKILL.md:14). Not true on some Linux/opencode hosts; README says macOS Command Line Tools.
- A5: Any review on the head commit counts, whatever its state (watch.py:89-92).
- A6: `gh pr view --json statusCheckRollup` returns all contexts (no truncation). Unverified.
- A7: Shell commands in local mode never read stdin and finish (watch.py:186).
- A8: mtime+size polling catches every edit; same-size edit within the same mtime granularity is missed only on coarse filesystems.

## Bugs
- B1 [medium]: Closed or merged PR is never recognized. A merged PR with finished CI is "done" only if reviews and threads are clean; a closed PR with failing checks or open threads yields endless polling (no `state` field fetched). watch.py:151. Scenario: PR merged by user while threads unresolved -> watcher runs until timeout (default 0 = never).
- B2 [medium]: A PR whose only check run is CANCELLED reads as green. `latest_checks` drops it, `rollup` is non-empty so the empty-rollup guard does not apply: pending False, failing []. watch.py:54,88; test_watch.py:60-61 asserts `(False, [])`. Scenario: manual cancel of the sole workflow -> `CI done | failing: none` -> `ALL DONE`.
- B3 [medium]: Persistent gh failure (auth expiry, network, deleted PR) only writes to stderr and loops silently forever when `--timeout` is 0 (default). Monitor reads stdout. watch.py:169,179. Scenario: `gh auth` expires -> no line, no exit, session waits indefinitely.
- B4 [low]: Rerun choice by string compare of `startedAt`. A queued rerun with a zero/empty start stamp sorts below the old failure; old failure wins, `pending` stays False, `ALL DONE` is blocked only by the failing list. Depends on X12 (unverified). watch.py:57-58.
- B5 [medium]: Local mode: FAIL to FAIL with changed output prints nothing. The session fixes error 1, error 2 appears, the watcher stays quiet. watch.py:209.
- B6 [medium]: Early ALL DONE when only some checks are registered. First poll after push may return a rollup holding just the first-registered check, already COMPLETED (or leftover runs of the previous head are replaced by few new ones); pending False. watch.py:88. Scenario: workflow A done in 5 s, workflow B not yet created -> `ALL DONE`. The empty-rollup guard covers only zero checks.
- B7 [low]: Review pagination absent (A2) and thread pagination absent (A1); see Assumptions.
- B8 [low]: Review state ignored. A `DISMISSED` review or `CHANGES_REQUESTED` review counts as "reviewed". watch.py:89-92.
- B9 [low]: `run_shell` has no timeout; a hanging command stalls the loop, inherits stdin. watch.py:186-189.
- B10 [low]: `local` without `--path` default is cwd; a command that writes into cwd (e.g. `.coverage`, logs, `*.pyc` beyond skip list) reruns forever; SKILL warns (SKILL.md:50) but code has no guard (e.g. ignoring files modified during the run). watch.py:255-273.
- B11 [low]: `walk_files` follows `os.walk` default (no symlink follow); symlinked source dirs unwatched. watch.py:222.
- B12 [low]: `TIMEOUT` is checked after the done check but before sleep, and a round takes 3 gh calls per PR; with many PRs the timeout overshoot is bounded by one round. Minor.

## Dead code, leftovers, stale comments
- L1: `PENDING_STATES` includes "EXPECTED" only for contexts; fine, no dead code found.
- L2: `__pycache__/` dirs untracked in the skill tree (git status) from test runs without `PYTHONDONTWRITEBYTECODE`. Not in `.gitignore` check pending.
- L3: Tests do not cover `main`, `parser`, `run_gh`, `run_shell`, `resolve_repo`, `emit`; CLI smoke covers only local `--once`. test_watch.py:371-386.
- L4: `-u` in SKILL.md:14 redundant (D1).

## Improvement areas
- I1: Three gh calls per PR per round (view, REST reviews, GraphQL). One GraphQL query could return head, rollup, reviews (with `commit.oid`, `state`) and threads, with pagination cursors. Cuts API calls 3x and removes the REST/GraphQL login mismatch (X6).
- I2: Add PR `state`/`mergedAt` to stop on MERGED/CLOSED (B1).
- I3: Emit gh-failure lines on stdout after N consecutive failures, and exit non-zero (B3).
- I4: Track expected check count or require stability for 2 polls before ALL DONE (B6).
- I5: Treat sole CANCELLED as failing/unknown (B2).
- I6: Local mode: print on FAIL output change; add `--timeout`; add command timeout.
- I7: Local watcher polling stat of whole tree each 2 s costs CPU on big trees; skip dirs list hard-coded (watch.py:16-20); no `.gitignore` use.
- I8: One shared script for polling skeleton: `run_pr` and `run_local` are separate; fine, but SKILL.md (98 lines) holds failure-reading advice (:74-81) that belongs to another skill or to qa notes.
- I9: Polling floor: `--interval` accepts 0 or negative; no validation (watch.py:284).

## Interfaces
- Exposes: skill `feedback-watch` (folder symlinked by install.py to both tools); CLI `skills/feedback-watch/scripts/watch.py` with modes `pr`, `local`; stdout line protocol (`#N sha | CI ... | failing: ... | waiting for review: ... | unresolved threads: N`, `PASS|FAIL`, `ALL DONE`, `CI DONE`, `NOT DONE`, `TIMEOUT`, `ALL PASS`, `FAILED:`); exit codes 0, 1, 3; test command in README.md:19.
- Consumes: `gh` CLI (pr view, api, api graphql, repo view), `/usr/bin/python3`, host Monitor tool (Claude Code) or background shell (opencode); global rule at instructions/global.md:12 triggers it; attack-plan-milestone-execute is expected to rely on it for "follows CI and reviews" (README.md:18; not verified in that skill).
- Threading: single-threaded, blocking loop; `gh` and shell commands run as synchronous subprocesses; sleeps via `time.sleep`; clock `time.monotonic`.

## Open questions for the user
- Q1: Should a merged or closed PR stop the watcher (B1)?
- Q2: Is a sole cancelled check "done" or "unknown"?
- Q3: Should a dismissed or changes-requested review count as reviewed (B8)?
- Q4: Should local mode print when the FAIL output changes (B5)?
- Q5: Is the Monitor tool limit of 1800000 ms current? Is the opencode background-job path tested?
- Q6: Does attack-plan-milestone-execute call watch.py directly or only instruct arming? (seams)
