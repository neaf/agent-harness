# Final audit: milestone-execute

Result: 20 requirements, 19 mapped, 1 missing (FR-APE-15, expected), 0 partial. 27 execute tests and 19 test_git tests pass. No model name or id in the group (FR-AGT-08 clean, grep found 0).

## 1. Traceability

| ID | Where | Status |
|---|---|---|
| FR-APE-01 | SKILL.md:51-57 (ticket wins :55, notes asked once :54) | mapped |
| FR-APE-02 | input-readiness.md:7-15, :39-42; SKILL.md:63 | mapped |
| FR-APE-03 | SKILL.md:65-72 (surprise into owning document :81) | mapped |
| FR-APE-04 | SKILL.md:76-79, :93-94 | mapped |
| FR-APE-05 | SKILL.md:89; subagent-rules-template.md:1-144 | mapped |
| FR-APE-06 | SKILL.md:101 (instructs, no watch.py call) | mapped |
| FR-APE-07 | SKILL.md:105, :111 | mapped |
| FR-APE-08 | build_integration_branch.py:242-318, :335-351; git.py:70-134 | mapped |
| FR-APE-09 | review-pass.md:49-98 | mapped |
| FR-APE-10 | SKILL.md:153; subagent-rules-template.md:115 | mapped |
| FR-APE-11 | SKILL.md:56, :86-90, :133; review-pass.md:65 | mapped |
| FR-APE-12 | SKILL.md:126 (runs qa-session, per Q18) | mapped, requirement text stale |
| FR-APE-13 | SKILL.md:94, :96; subagent-rules-template.md:134 | mapped, requirement text stale (Q19) |
| FR-APE-14 | SKILL.md:21, :94 | mapped |
| FR-APE-15 | none. SKILL.md:153-154 and review-pass.md:94-96 forbid posting a reply | missing |
| CON-GIT-01 | git.py:70-74; build_integration_branch.py:220, :244 | mapped |
| CON-GIT-02 | git.py:76-80; build_integration_branch.py:299-301 | mapped |
| CON-GIT-03 | git.md:184-189 (doc only, no code in group) | mapped |
| CON-GIT-04 | git.py:93-97; git.md:168-182; test_git.py:127-138 | mapped |
| CON-GIT-05 | git.md:191-198 | mapped |

## 2. Leftovers

Counted per file.

- build_integration_branch.py: 1. Line 297 sets `conflict.head` on a `Conflict` that declares no `head` (git.py:16-21). Works, but the attribute is undeclared. Code change, optional.
- git.py: 1. `tree_of` (:103) has no production caller, only test_git.py:146. Architecture lists it. No change.
- test_build_integration_branch.py: 1. Comment ":121 FR-APE-08 fixes (Phase 9)" names a phase of the deleted `.rearch/`. Text change.
- test_review_threads.py: 2. Docstring ":395 Phase 9 exit" names a deleted phase (text change). Line 414 has one blank line before `if __name__`, the other files have two (style, optional).
- git.md: 1. Line 139 "(seen once, Phase 9)" names a deleted phase. Text change.
- SKILL.md, input-readiness.md, review-pass.md, subagent-rules-template.md: 0. No deleted file, old name or old behavior. The grep for `detect_default`, `git_or_fail`, `models.json`, `milestone spec`, `resolveReviewThread` outside tests and github.py finds nothing.
- test_git.py: 0.

## 3. Doc/code mismatches

- requirements.md:265 (FR-APE-12) says "by hand, without qa-session". SKILL.md:126 runs qa-session (Q18). Requirement needs rewording. No code change.
- requirements.md:268 (FR-APE-13) says "Execute's briefs never pass it". SKILL.md:94 passes it (Q19). Reword. No code change.
- requirements.md:508 (NFR-12) says only the integration script writes to a remote. `review_threads.py resolve` also writes (deviation 9.7). Reword.
- requirements.md:526-527 (CON-GIT-01, -02) cite `build_integration_branch.py:11` and `:82`. Now git.py:70-74 and :76-80.
- requirements.md:529 (CON-GIT-04) says untested in a single-branch clone. Checked (deviation Phase 1.6, test_git.py:127). Reword.
- requirements.md:546 describes the old no-op merge and conflict defects, fixed in Phase 9.
- architecture.md:122 lists `git.Git(runner, cwd)` and `.fetch(remote, branch)`. Actual: `Git(cwd=".", runner=run)` (git.py:49), `fetch(remote, *branches)` (:93). Missing from the list: `default_branch`, `require_identity`, `rev`, `push`, `call`, `out`, module `run` and `cause`.
- architecture.md:137 (review_threads CLI) says `resolve --thread ID [--repo]`, one thread, exit 0 or 1, `RESOLVED id` or `REFUSED: human thread`. Actual: no `--repo` on `resolve`, several ids, list ends with a count line, longer REFUSED text (deviation 9.5). Update.
- architecture.md:136 build_integration_branch row is right.
- README.md:17 and :31: match code. No change.
- git.md: all code and test names it cites exist (checked). `--name-only` on git 2.38 stays `unverified` (:151), correct.
- FR-APE-15 versus current text: SKILL.md:10, :145, :153-154 and review-pass.md:70, :94, :96-97 all say the user posts replies, a bot REPLY thread waits for the user, and the run is done with such a line left. These contradict FR-APE-15 and need the code change below.

## 4. Models (FR-AGT-08)

0 findings. No model name, alias or id in any file of the group.

## Needs a code change

1. FR-APE-15 (missing): SKILL.md:10, :145, :153-154; review-pass.md:70, :94, :96-97. Let the orchestrator post the reply for a bot REPLY thread, then resolve it. Never touch a human thread. FR-APE-10 needs the matching exception. No script posts a reply yet: `github.py` has no reply call and `review_threads.py` has no `reply` command, so add both, with tests.
2. build_integration_branch.py:297: declare `head` on `Conflict` or pass it in the constructor (optional).
3. Text only: test_build_integration_branch.py:121, test_review_threads.py:395, git.md:139 drop the "Phase 9" wording.

Result: 19 of 20 mapped, FR-APE-15 missing, 3 code or text changes, 6 stale doc lines.
