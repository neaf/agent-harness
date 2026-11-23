# Review pass

One pass handles every open review thread of the project's PRs at once, in stack order. Run it once CI is green: review comments arrive after CI.

## 1. Collect

For each PR with the project label, list its unresolved review threads: `gh api graphql` on `reviewThreads` (with `isResolved`, `path`, `line` and the first comment), or the review UI. Comments on the integration PR count too.

## 2. Check each finding against the code

Read the cited lines on the PR head, not on the default branch. Reviewers, human or review bot, are often right and sometimes not: a component may already hide the button it says is visible, a prop it says is missing may never be read. Decide with evidence, file and line.

## 3. Decide

Write `.ai-notes/<area>/review-pass-<YYYY-MM-DD>.md`:

```markdown
# Review pass, <date>

FIX = change the PR that owns the code. REPLY = no change, the user posts the text.

| # | PR | thread | finding | decision |
|---|---|---|---|---|
| 1 | #123 [XX M1-2] | <thread url> | <one line> | FIX: <what to change> |
| 2 | #124 [XX M1-3] | <thread url> | <one line> | REPLY |

Reply texts:
- 2: "<short answer with the evidence, file:line>"

## Status
- <date>: row 1 fixed in <sha>, merged up to <branches>.
```

- FIX goes to the PR that owns the file, even when the comment was posted on another PR (for example the integration PR). Find the owner with `gh pr diff <n> --name-only` on the stack.
- REPLY texts are short and factual: what is true, with the file and line that shows it. No thanks, no apology.
- A finding you are unsure about goes to the user with your recommendation, not to a FIX.

## 4. Apply

1. Launch one fresh subagent per PR that has FIX rows, from the bottom of each stack. Its brief: `subagent-rules.md`, the FIX rows for its PR, the branch. It pushes a new commit and does not resolve threads.
2. Check each fix: it does what the row says and nothing more. Drop extra changes, such as a second guard for a case already covered.
3. Merge each fixed branch up its stack before fixing the next PR (Step 8 of the skill).
4. Once a fix is pushed, resolve its thread: `gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "<thread id>"}) { thread { isResolved } } }'`. Leave REPLY threads open for the user.
5. Rebuild the integration branch if there is one.
6. Fill the "Status" section, and list the reply texts in the notes `README.md` pending items for the user. The user posts them: never post a reply as the user.
