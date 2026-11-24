# Subagent briefs

Fill the angle-bracket fields and pass the brief as the whole prompt. Give each subagent the strongest model tier available. Neither subagent receives the conversation, a previous version of the page, or the orchestrator's conclusions. Only the sources, the decisions file and the paths below.

## Builder

```
Goal: write a QA session page for the milestone described below. The page is the script a team walks through live, on a deployed test environment with seeded users and data.

Read first, in this order:
1. The writing-craft skill, in full. Its rules apply to every sentence you write.
2. The qa-session skill's references/page-template.md, references/setup-checklist.md and this brief's rules below.
3. The sources listed here, and nothing else from earlier work:
   - Spec or plan: <paths>
   - Code under test, at commit <sha>: <paths or areas, read with git show <sha>:<path> or from a checkout at that commit>
   - Seed: <seed file path>, with its tests, and its expected output <path or "derive from the seed code">
   - Environment: <URL>, build <commit or pull request>, feature switch <UI label and where to see it>
   - Personas and order: <list, or "derive the order from the spec, most powerful first">
   - Decisions already made by the user: <content of decisions.md, or "none">

Write:
- The page at <page path>, following page-template.md. Its Findings table is empty.
- A derivation file at <derivation path>: one line per checkbox or expected value on the page, giving the source that settles it: file and line of the code, the seed line that creates the data, or "unverified: <the check that would settle it>". Working notes, not for the tester.

Rules:
- One linear story, persona after persona. Each scenario: a title that advances the story, "As <user>:", one sentence on what changed since the previous scenario, checkboxes with one observable fact each, then only the note lines that apply.
- Every expected result comes from the code under test and the seed, verified in the source before you write it. Never from memory, from a previous page, or from what seems plausible. Label what you could not verify; never write it as a step.
- Every value the tester needs is resolved on the page: real URLs, real ids printed by the setup, real emails. No placeholders.
- Every word that names something on screen (menu item, page title, column, filter, button, empty-state text, error page) is the exact string that scenario's user sees: resolve it from the component that renders it for that user, through its translation key, in that user's language. Never paraphrase a column ("budget used" is not "Budget consumed (%)"). The same screen can differ by persona: check the label for each user who sees it, and write the persona's version.
- No internal reference ids (spec rule numbers, decision ids, question ids). Name the case instead.
- Say "on production" or "in this test environment" explicitly. Never a bare "today" or "now".
- Put each surprise the team could hit in "Known limits, not bugs", before the walk-through.
- Product questions: the question as a heading, short context, option A marked as what the test environment currently does with the scenario where it shows, option B, each with its consequence. No history, no names of people, no deadlines unless they change the answer.
- No emoji. US English.

Before you finish, run: /usr/bin/python3 -I <skill>/scripts/check_page.py <page path> -v
Fix every FAIL. Do not edit the derivation file to match a page you have not checked.

Report in at most 120 words: the page path, the derivation path, counts (scenarios, checks, product questions, unverified checks), and anything you could not settle from the sources. Do not paste the page.
```

## Verifier

```
Goal: check a QA session page against its sources, then read it cold as the tester. You are a fresh reader. Your findings decide whether the page is ready for the session.

Read only:
- The page: <page path>
- The sources: <spec paths>, the code under test at commit <sha> (<paths or areas>), the seed file <seed path> with its expected output, and the environment notes <path>.
- The decisions file <decisions path>, only to know which product choices are already made.
Do not read any derivation file, previous version of the page, or other notes.

Pass 1, facts. For every checkbox, expected value, printed seed line, URL, user and product-question option on the page, decide:
- verified: give file and line, or seed line, that shows it;
- wrong: say what the source shows, with file and line;
- unverifiable: say which check in the test environment would settle it.
Also check that each user on the page is created by the seed with the role the scenario needs, and that each printed seed value follows from the seed code.
Also check every on-screen word on the page (menu items, titles, columns, filters, buttons, empty-state and error texts): trace it to the component that renders it for that scenario's user and to its translation in that user's language. A paraphrase, a label from another page, or a label another persona sees is wrong.

Pass 2, cold read. Walk the page in order, as a tester with only the page open and busy hands. For each step, ask what they do next and what they should see. Report only a place where the page fails them: a step that uses something introduced later, a term never defined, a control the UI does not have, a value still to look up, a check with two facts, a missing "what changed" sentence, a surprise not said before it happens. Do not propose extra text unless a step cannot be performed without it.

Report in at most 300 words:
- Pass 1 counts: verified, wrong, unverifiable.
- Each wrong check: the page line, what the source shows, file and line.
- Each unverifiable check: the check that settles it.
- Pass 2: each failure point as page line, what fails, and the smallest change that fixes it.
```

## Carry-over (orchestrator, not a subagent)

The orchestrator does this itself after the rework builder and the verifier report. It reads the previous page only for its live state. Match by scenario title and check text. A tick carries over only when the new check means the same thing; otherwise the tick is removed and the change is stated in the reply. Findings the user has asked to keep go into the new Findings table with their original wording. Nothing else from the previous page is copied.
