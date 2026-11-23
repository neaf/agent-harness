# An executable plan

The plan is executable when an AI, given one task and the pinned code, opens a pull request that a reviewer accepts without the author explaining anything. Each gap below caused rework or a human intervention on an earlier project.

## Milestones

- M1 onward are the delivery slices the author approved in the product solution: same order, same content. Changing them reopens the `delivery` section.
- A foundation milestone (M0) holds the shared plumbing two or more slices need: the flag, shared helpers, the guard that keeps every later endpoint closed by default. It ships nothing users see.
- When the slice order is still open with product, recommend the most complex slice first, so its surprises show early.
- Each milestone ends with a QA step on a review app (named personas, the checks they run) and a release step.

## Split for review in isolation

Each pull request must be reviewable by someone who never read the plan: a reviewer from the team that owns the code it touches. Split the work so that:

- **One owner per pull request.** Cut along code ownership (`CODEOWNERS`, or the teams Stage 1 found for each path). A change to shared code (permissions, the data model, a shared component, configuration) goes in its own small pull request, so its owners review only that.
- **One concern per pull request.** It does one thing a reviewer can name in a sentence. No drive-by refactor, rename or formatting: those go in a separate pull request, or nowhere.
- **Safe alone.** Merged alone, it changes nothing for anyone outside the flag, and closes by default what it opens. A reviewer judges it without knowing the later pull requests.
- **Small enough to read in one sitting.** When a task touches many files for one mechanical change, say so, so the reviewer can skim the repeats.
- **Readable in order.** Stacked pull requests read bottom-up, each one building on what the one below states.

## Tasks

One task is one pull request. Each task block in the technical solution holds:

- **Title** with the milestone prefix in planned merge order: `[<project code> M<n>-<k>] <what it does>`, a short project code used on every pull request. The pull requests are opened in that order, so the host's list, newest first, shows each milestone as one unbroken sequence.
- **Base:** the default branch, or the task it is stacked on. Stacks stay short, and an unstacked task is preferred when it can merge alone.
- **Files:** the paths to create and the paths to change, at the pinned SHA. For a lower task in a stack, the files it must not touch.
- **Rule, applied everywhere:** when a rule spans several places ("every endpoint that loads the record checks the new scope"), list each place by name. A rule stated once and applied in part shipped a leak.
- **Invariants and their tests:** each invariant (`never`, `always`, `keep`) names the test file and the case that proves it, such as a matrix row per role: own data, in scope, out of scope, other tenant.
- **Edge cases per endpoint or component:** the nil and empty cases (no parent record, empty list against nil, missing configuration), the confidential or hidden variant, an out-of-scope record (404 or 403, and why), error ordering.
- **Ordering inside the milestone** for guard-sensitive changes: what makes CI stay green after each merge (for example, a feature that starts with no actions, each endpoint task adding its own).
- **Reviewers:** the owners of the touched paths, and what each must check ("the permission matrix rows", "the query plan on large accounts").
- **Context for an outside reviewer:** two or three sentences on why this change exists and what stays unchanged, written for someone who has not read the plan. It becomes the opening of the pull request description.
- **Reviewer-facing rationale:** every decision a reviewer or a review bot will challenge ("no plan entry", "no new permission action"), with the one-line reason and the source. Without it, the review thread waits for the author.
- **QA:** one to three steps a reviewer follows on a review app.
- **Depends on:** the tasks that merge first. They become the `blocked-by` relations of the tracker tickets.
- **Tracker ticket:** one per task, its description holding this block, so an agent can start from the ticket alone.

## Project-wide sections

Write these once, in the technical solution:

- **Colliding work:** the open pull requests of others that touch the same files, and the decision on merge order or coordination.
- **Environment:** the commands an implementer runs after switching branches (code generation, test database migrations), the lint and type-check commands, and fixed-date rules for tests (no current date near a year boundary, no random flags).
- **Seeds and QA data:** how a review app gets the personas and the data each QA check needs, idempotent on a second run.
- **Merge policy:** bottom-up for stacks. Branches follow the default branch by merging it into the bottom of each stack, then up; never rebase or force-push.
- **Human-only gates:** the steps an agent stops at and hands to a person: re-running CI, posting review replies (including replies to review bots), triaging security alerts, merging, enabling the flag for real customers.
