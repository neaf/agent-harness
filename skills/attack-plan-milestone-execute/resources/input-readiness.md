# Is the milestone ready to build?

This skill gets its results from its input. A milestone with an approved product solution, a technical solution and precise tasks turns into PRs a reviewer accepts. A one-sentence ticket turns into guesses, rework and review threads. Grade the input before any code.

## Blocking gaps

Any of these stops the run:

1. **No product solution.** Nothing says who gets what: the rules per role, what each screen shows, what is out of scope. A ticket title is not a product solution.
2. **No technical solution for this milestone,** in the attack plan or the milestone spec. Nothing says which parts of the code change, in which order, what must not change (shared frameworks, code of other teams, generated files), and how it is released (flag, who it targets).
3. **Tickets that cannot become PRs.** A ticket is ready when an implementer could open its PR without asking the author. It names:
   - the area or files it changes;
   - each rule it adds and every place the rule applies, by name ("every endpoint that loads the record");
   - the tests that prove what must never, always or still happen;
   - the tickets that merge first.
4. **Open questions that block this milestone,** with no answer and no assumed default written down.
5. **Unmerged prerequisites** (an earlier milestone, shared plumbing) with no plan for stacking on them.

## Gaps to fix during the audit

These do not stop the run. Add them to the audit of Step 3:

- edge cases per endpoint or screen (nil, empty, hidden, confidential, out of scope);
- the reason behind each choice a reviewer will challenge;
- open PRs of other developers on the same files;
- QA personas and the data a review app needs;
- the commands to run after switching branches.

## How to grade

1. Grade the documents yourself: items 1, 2, 4 and 5.
2. Grade the tickets with read-only subagents, about six tickets each. Each returns one line per ticket: ready, or the missing parts of item 3.
3. Show the result as a table: item, verdict, what is missing, who can fill it (product, the author, another team).

## When the input is not ready

- Stop and say what is missing, in plain words. Suggest filling it with the `attack-plan-create` skill (the attack plan and its milestones), or by asking the person who owns each gap.
- When the user still wants to go on, write the accepted gaps in the notes `README.md`. Each accepted gap becomes a question of the audit in Step 3, answered before the PR it affects is briefed.
