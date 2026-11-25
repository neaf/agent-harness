# GitHub

Facts about GitHub (`gh`, REST, GraphQL, Actions) that the skills depend on. Vendor docs were read on 2026-11-25: [GraphQL schema](https://docs.github.com/public/fpt/schema.docs.graphql), [GraphQL limits](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api), [REST pulls](https://docs.github.com/en/rest/pulls/pulls), [REST workflow jobs](https://docs.github.com/en/rest/actions/workflow-jobs), [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows). No live `gh` call was made for this doc.

Adapter: `skills/feedback-watch/scripts/watch.py` (`run_gh`, `gh`, `fetch_pr`). From Phase 6 on: `skills/harness-common/scripts/github.py`.

## Check rollup

| Fact | Source |
|---|---|
| `statusCheckRollup` items are a union of `CheckRun` and `StatusContext`. | GraphQL schema, `union StatusCheckRollupContext` |
| `CheckRun` has `name`, `status`, `conclusion` and `startedAt`. `startedAt` and `conclusion` can be null. | GraphQL schema, `type CheckRun` |
| `StatusContext` has `context`, `state` and `createdAt`. | GraphQL schema, `type StatusContext` |
| `CheckRun` conclusions: `ACTION_REQUIRED`, `CANCELLED`, `FAILURE`, `NEUTRAL`, `SKIPPED`, `STALE`, `STARTUP_FAILURE`, `SUCCESS`, `TIMED_OUT`. | GraphQL schema, `enum CheckConclusionState` |
| `StatusContext` states: `ERROR`, `EXPECTED`, `FAILURE`, `PENDING`, `SUCCESS`. | GraphQL schema, `enum StatusState` |

Code: `watch.py:20-22` (failing and pending sets), `:42-47` (item kind and name), `:63-75` (classification). Tests: `skills/feedback-watch/tests/test_watch.py:53-83`.

### Quirk: reruns stay in the rollup

- Symptom: a rerun workflow leaves the old failed run next to the new one, so the PR reads as failing after a green rerun.
- Cause: the rollup lists every run, not only the latest.
- Workaround: per check name, keep only the newest item by `startedAt` (`CheckRun`) or `createdAt` (`StatusContext`).
- Code: `watch.py:50-60`. Tests: `test_watch.py:63-72`.

### Quirk: cancelled runs

- Symptom: a run cancelled by a workflow's concurrency group shows as `CANCELLED` beside the run that replaced it.
- Cause: concurrency cancels the older run.
- Workaround: drop `CANCELLED` items. When the only run of a check is cancelled, dropping it hides the check; that case is a known defect (feedback-watch B2).
- Code: `watch.py:54`. Test: `test_watch.py:60`.

### Quirk: a queued run has no start time

- Symptom: a queued rerun may sort as older than the run it replaces.
- Cause: `CheckRun.startedAt` is nullable (schema). Whether `gh` prints null or a zero date for it is `unverified`.
- Workaround: treat a missing or zero `startedAt` as newest. Not handled today (feedback-watch B4).
- Code: `watch.py:57`.

### Quirk: empty rollup right after a push

- Symptom: right after a push the rollup is empty, which reads as "no checks, done".
- Cause: checks appear a few seconds after the push.
- Workaround: an empty rollup counts as pending, unless `--allow-no-checks` is given.
- Code: `watch.py:88`. Test: `test_watch.py:109-111`.

## Reviews and threads

| Fact | Source |
|---|---|
| REST reviews carry `commit_id`, the commit each review covers. | `watch.py:91`, tests |
| Why `gh pr view` reviews are not used for the commit: `unverified`. | feedback-watch audit X5 |
| A review comment's `author` is the `Actor` interface; `__typename` tells `Bot` from `User`. | GraphQL schema, `type PullRequestReviewComment` |
| `PullRequestReviewThread` has `isResolved`, `isOutdated`, `path` and `comments`. | GraphQL schema |
| The mutation `resolveReviewThread` resolves a thread. | GraphQL schema |

Code: `watch.py:23-26` (threads query), `:84-99` (`pr_state`), `:149-158` (`fetch_pr`).

### Quirk: bot logins differ between REST and GraphQL

- Symptom: a reviewer named `claude[bot]` never counts as having reviewed.
- Cause: REST returns `claude[bot]`, GraphQL returns `claude`.
- Workaround: strip a trailing `[bot]` before comparing logins.
- Code: `watch.py:79-81`. Test: `test_watch.py:95`.

### Quirk: lists stop at 100

- Symptom: on a PR with more than 100 threads or reviews, the extra ones are not seen.
- Cause: a GraphQL connection takes `first` or `last` between 1 and 100 (GraphQL limits doc). REST `per_page` is at most 100 (REST pulls doc).
- Workaround: page with `pageInfo.endCursor` and the REST `page` parameter. Not done today.
- Code: `watch.py:26` (`reviewThreads(first: 100)`), `:152` (`per_page=100`).

## Pull request order

| Fact | Source |
|---|---|
| REST lists pull requests by `created`, newest first, unless `sort` and `direction` say otherwise. | REST pulls doc, "List pull requests" |
| The search `is:pr label:<label> sort:created-asc` lists the oldest first. | `skills/attack-plan-milestone-execute/SKILL.md:54`, `unverified` |

Workaround in use: open a milestone's PRs in number order, so newest-first reads as one sequence. Code: `skills/attack-plan-milestone-execute/SKILL.md:54`, `skills/attack-plan-create/references/executable-plan.md:26`.

## Stacked branches and CI

| Fact | Source |
|---|---|
| A `pull_request` workflow runs on the merge ref `refs/pull/<n>/merge`. | Events doc, `pull_request` |
| `pull_request` workflows do not run while the PR has a merge conflict; `pull_request_target` workflows do. | Events doc |
| `gh stack` is an optional `gh` extension. Without it each PR targets the branch below. | `skills/attack-plan-milestone-execute/SKILL.md:19` |

### Quirk: a stack behind the default branch goes red together

- Symptom: every PR of a stack fails at once, in jobs its code does not touch (a change detector firing on files only the default branch changed, a missing task, a tool version mismatch).
- Cause: the branches are behind the default branch. The skill text says CI runs the default branch's workflows against the old branch files. For `pull_request` the docs say the run uses the PR's merge ref; the exact mechanism is `unverified`.
- Workaround: merge the default branch into the bottom of each stack and merge up.
- Code: `skills/attack-plan-milestone-execute/SKILL.md:78`, `skills/feedback-watch/SKILL.md:89`.

## Job logs and failures

| Fact | Source |
|---|---|
| `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs` returns a redirect to the job's plain-text log. The link expires after one minute. | REST workflow jobs doc |
| A finished job's log can be fetched while the rest of the run is still going. | `skills/feedback-watch/SKILL.md:88`, `unverified` |
| `gh run view --log` waits for the whole run. | `skills/feedback-watch/SKILL.md:88`, `unverified` |
| A failed check with no failed step and an annotation such as "runner lost communication" is an infrastructure failure. | `skills/feedback-watch/SKILL.md:87`, `unverified` |
