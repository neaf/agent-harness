# Final audit: feedback-watch (FW, CON-GH)

Tests: feedback-watch 74 OK, test_github 21 OK. Model-name grep over the group: 0 hits (FR-AGT-08 mapped).

## 1. Traceability

| ID | file:line | Status |
|---|---|---|
| FR-FW-01 | watch.py:148-187 (loop), :95-112, :143-145 (change print), :335 (interval > 0) | mapped |
| FR-FW-02 | github.py:123-155 (all pages), :12-26 | mapped |
| FR-FW-03 | watch.py:54-86 (newest, cancelled superseded, sole cancelled failing, Q24) | mapped |
| FR-FW-04 | watch.py:99, :177 (two identical rounds, Q25), :149 | mapped |
| FR-FW-05 | watch.py:89-92, :100-103 (Q26: dismissed excluded) | mapped |
| FR-FW-06 | watch.py:176-186 | mapped |
| FR-FW-07 | watch.py:156-160, :171-174, :363 | mapped |
| FR-FW-08 | watch.py:162-165 (requirement text is a stub, see 3.1) | mapped |
| FR-FW-09 | watch.py:229-241, :286-309, :346-347 (Q27) | mapped |
| FR-FW-10 | watch.py:22-26, :244-263 | mapped |
| FR-FW-11 | watch.py:287-294 | mapped |
| FR-FW-12 | watch.py (no write); github.py:179 resolve_thread is a write, not called by watch.py; test_watch.py:331 | mapped |
| FR-FW-13 | SKILL.md:98-112 | mapped (opencode experimental) |
| FR-FW-14 | SKILL.md:130-137 | mapped |
| FR-FW-15 | SKILL.md:44-46, :77, :93, :64-66 | mapped |
| CON-GH-01 | github.py:12-18, :74-80; GitHub.md:27-38 | mapped |
| CON-GH-02 | watch.py:48-65; GitHub.md:40-59 | mapped |
| CON-GH-03 | watch.py:99; GitHub.md:61-66 | mapped |
| CON-GH-04 | watch.py:89-92; GitHub.md:82-87 | mapped |
| CON-GH-05 | GitHub.md:96-103 | mapped |
| CON-GH-06 | GitHub.md:113-118 (mechanism marked unverified) | mapped |
| FR-APE-15 | SKILL.md:121, :139 | partial (see 3.2) |
| FR-AGT-08 | none in group | mapped |

Counts: 21 mapped, 0 missing, 1 partial (FR-APE-15 touches this group only through SKILL.md wording).

## 2. Leftovers

- No references to run_gh, fetch_pr, resolve_repo, THREADS_QUERY, REST reviews anywhere in skills, README.md, install.py.
- No dead code found in watch.py, github.py, test_github.py. All imports used.
- skills/feedback-watch/scripts/__pycache__ exists on disk; gitignored (.gitignore:3). No change.
- test_watch.py:27 `thread()` helper omits `body` that github.py:92 returns. Harmless. No change.

## 3. Doc and code mismatches

1. requirements.md:301-303: FR-FW-08 text is only "A merged or closed PR." Behavior built: prints `#N merged|closed, stopped watching`, drops the PR, `ALL DONE` when none open (watch.py:162-165, :177). Doc fix in requirements.md, no code change.
2. SKILL.md:121 and :139: "replying to or resolving a thread needs the user's OK" and "never post a comment or review without the user's OK". FR-APE-15 (new, not built) has the orchestrator reply to bot threads with decision REPLY and resolve them without the user. The text is true for this skill's own watcher but contradicts FR-APE-15 when execute follows it. Needs a wording change (scope it to this skill, or point to execute's rule). Edit when FR-APE-15 is built.
3. GitHub.md:3: "No live `gh` call was made for this doc." Stale. deviations.md Phase 6 (line 116) records a live run of `watch.py pr 15111 15157 --repo cli/cli --once` that validated the query. Doc fix.
4. GitHub.md:12 (GraphQL error exit code) and :57 (queued startedAt) stay `unverified`; consistent with deviations.md:17. No change.
5. architecture.md:131: watch.py pr output column omits `BOTS DONE` and the `skipped` stderr line. Exit column lacks 2 for bad args. Doc fix.
6. architecture.md:132: watch.py local output column omits `FAIL (timed out)`, `ALL PASS`, `FAILED: <cmds>`, `TIMEOUT`. Doc fix.
7. README.md:18: row does not mention `--cmd-timeout`. Test command lacks `PYTHONDONTWRITEBYTECODE=1`. Optional.
8. GitHub.md:80 names `review_threads.py` without path; it is skills/attack-plan-milestone-execute/scripts/review_threads.py. Optional doc fix.

## 4. Model names (FR-AGT-08)

Zero hits for sonnet, opus, haiku, claude-, gpt, gemini, deepseek, flash, anthropic in the group's files. Reviewer example `claude[bot]` (SKILL.md:25, GitHub.md:84-85, tests) is a GitHub bot login, not a model name. Test must exempt it or use another example.

## Needs code change

None in code. SKILL.md:121,139 need a wording change when FR-APE-15 lands. The rest is doc fixes (3.1, 3.3, 3.5, 3.6).
