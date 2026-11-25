# Page template

The shape of a QA session page. Square brackets are placeholders the builder fills in; the finished page has none. Section order is fixed because the tester reads top to bottom with the app open. Add nothing that is not on this list unless the content needs it.

````markdown
# QA session: [feature in plain words] ([date of the session])

> [One or two sentences: what this session walks through, the order of the personas, and that the tester ticks each check as they go.]

## Before the session

- [ ] Environment: [URL] runs build [commit or pull request]. Check: [the first thing the tester sees that proves the build].
- [ ] Feature switch [name in the UI, not the code name] is on for [scope]. Check: [where to see it].
- [ ] Data: run [exact command] and compare the output with "Expected seed output".
- [ ] Sign-in: each user below signs in once before the session. [How impersonation or sign-in works, if not obvious.]
- [ ] Users, in order: [email] (scenarios 1, 3); [email] (scenario 2); [email] (scenario 4).

### Expected seed output

- [label as printed]: [value], [what it means in one phrase]
- [one line for every printed value the checks rely on]

## Known limits, not bugs

> - **[Surprise in the words the tester will use]:** [what they will see]. [Why it is so here, with the source of the reason.] [What to do: carry on, or the check that is skipped.]
> - [One line per surprise. Environment gaps, production behavior kept on purpose, real data next to seeded data.]

## Walk-through

One story, one persona at a time, in this order. Tick each check as you see it. Anything unexpected goes into Findings at the end.

### 1. [Scenario title that advances the story]

As [user label in the UI's words] (`[email]`):

Baseline: [only for the first scenario, what the tester sees before any change].

What changed since the previous scenario: [one sentence, only the difference].

- [ ] [One observable fact: what is on screen, or what a value is.]
- [ ] [Next fact.]

> **Why:** [only if the result needs a reason].
> **Caveat:** [only if a limit applies here].
> **Product assumption:** [only if the result depends on a decision not yet made; link the question below by its heading.]

### 2. [Next scenario title]

As [user label] (`[email]`):

What changed since the previous scenario: [one sentence].

- [ ] [Fact.]

## Product questions

Each question is for a product person who has not seen the project. Only the questions the session can answer.

### [The question, as a question, in plain words]

[Context: only what is needed to answer. Two or three sentences.]

- **A. [option].** Currently in this test environment, scenario [n]: [consequence].
- **B. [option].** [Consequence.]

## Findings

Empty at the start of each session.

| # | Scenario | What you saw | What was expected | Status |
|---|---|---|---|---|

## After the session

- [ ] [Restore anything the walk-through changed, for example the feature switch.]
- [ ] [Record the answers to the product questions in [where the team tracks decisions].]
````

## Notes on the shape

- Scenario numbers are positions in the walk-through, so "scenario 2" is allowed. Spec or decision ids are not.
- The Known limits section comes before the walk-through, because the surprise must be said before it happens.
- A check is one fact the tester can see. Two facts become two checks; the same fact in two places becomes one sentence that says why the two places differ.
- When a scenario has no product assumption, the assumption line is left out, not written as "none".
- Callouts are blockquotes here. A document tool maps them to its own callout block (see [publishing.md](../../harness-common/references/publishing.md)).
