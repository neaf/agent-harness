---
name: open-items
description: Keeps the loose ends of a session in one ledger, `.ai-notes/<area>/open-items.md`, so nothing waiting on the user or on the agent drops out of sight across turns, sessions and handoffs. Every turn the agent closes what the user's message answered, opens what its reply leaves open (decisions, the user's tasks, follow-ups, defaults that go ahead, results to review), re-checks due follow-ups, and ends the reply with the "Waiting on you" block printed from the ledger. Use whenever a reply leaves anything waiting on the user or on the agent, and when a session starts in an area that has a ledger.
---

# Open items

A long session leaves loose ends on both sides: a decision you need, a task only the user can do, something you will check again later, a proposal that goes ahead unless the user objects. This skill keeps them in one file per area, the ledger, so the reply's "Waiting on you" list is printed from it instead of retyped, and nothing falls out between turns or sessions.

The user never maintains the list. You find the items in the conversation, the user's words and yours, and close them when they are answered or done, from plain prose.

`<skill>` below is the folder holding this file. Run the script as `/usr/bin/python3 -I <skill>/scripts/ledger.py`.

## The ledger

- It lives at `.ai-notes/<area>/open-items.md`, in the area the work already uses ([ai-notes](../ai-notes/SKILL.md)). One ledger per area; sessions that share an area share its ledger and its ids.
- With no area, create one the first time a reply ends with an item still open, named after the work, with the README ai-notes requires. `ledger.py init .ai-notes/<area>/open-items.md` writes the empty ledger.
- The grammar is in [references/format.md](references/format.md). Each item is one line plus `  - key: value` fields. `ledger.py check` says whether the file fits; run it after every edit.
- When the session has an `open_items` tool (Synopia), record items through it instead of editing the file: Synopia owns the list and writes the file between turns.

## Items

An item is one loose end with an owner. Its id is `Y<n>` when it waits on the user, `A<n>` when it waits on you. Numbers count up per ledger and are never reused: take the next one from `ledger.py next <file> Y|A`, right before you write.

| Kind | Who acts | Closes when |
|---|---|---|
| `decision` | the user chooses, you act | the user answers |
| `your task` | the user | the user says it's done, or the work shows it (threads resolved, PR approved) |
| `default` | you, unless the user objects | it went ahead at its `goes ahead` point, or the user objected |
| `review` | the user looks at what a `For review: ` subagent made | the user responds about it, or marks it reviewed |
| `follow-up` (an `A` item) | you, on a `trigger` | you checked and acted |

States: open; `answered` (heard, you haven't acted yet); `due` (a follow-up's trigger fired); `later` (deferred: it returns at its trigger or the next session). Closed lines say answered, done, went ahead, dropped (always with why) or superseded by another id. Never drop an item silently.

## Every turn

At the start:

1. Read the ledger. It is short: the newest 30 closed lines at most (`ledger.py prune`).
2. Read the user's message for answers, asks and promises. Close what it answers, by id, by quote or by plain reference. Open what it asks for or promises: "I'll review it tonight" is a `your task`, "remind me" a follow-up, "later" sets `later`.
3. Check the follow-ups whose trigger can be checked now (a PR's state, a CI run, a file). A fired trigger makes the item `due`: act on it in this turn.

During the turn:

4. When a trigger can be watched, arm a watcher for it ([feedback-watch](../feedback-watch/SKILL.md) for pull requests, a monitor for a command or a file) and name it in the item's `watch` field.

At the end:

5. Open what the reply leaves open: each question you ask, each proposal you will act on unless told otherwise, each "I'll check after…". Not a question the same reply answers.
6. Close what the turn did: a decision you acted on, a follow-up you checked, a default that went ahead.
7. Write the ledger. Stamp this turn's changes with one time, `date '+%Y-%m-%d %H:%M'`, in each new `from` field and closed line. Run `ledger.py check`, then end the reply with the block.

## Answering

Plain prose is the main path; ids are a shortcut.

| The user writes | What closes |
|---|---|
| A quote of one line, then "Run it" | the quoted item, answered "Run it" |
| "Run it" with one decision open whose options include it | that decision |
| "Y1 run it, Y3 later" | Y1 answered "run it"; Y3 set to later |
| "done with the review threads" | the `your task` about the review threads |
| "skip the worktrees" | the worktree decision, dropped, "you said skip" |
| "go" after a list of three proposals | all three defaults go ahead |
| "Run it" with two decisions open that both fit | nothing yet: ask in one line which one |

An answer that could mean two items is asked about, never guessed. A wrong close costs more than one short question. When the user says a close was wrong ("Y2 isn't done"), reopen it.

## The reply's block

The reply ends with one block, printed by `ledger.py block <file> --since "<this turn's time>"` after the ledger is written, and pasted as it is. For the ledger in [references/format.md](references/format.md), at 15:10 with `--show A1`:

```markdown
**Waiting on you** (4)
- **Y1** decision: Run `bin/schema-lint --fix` now, or look at the 14 warnings first? (I'd look first)
- **Y2** your task: Answer the 2 review threads from Mira on #812.
- **Y4** default: Mark #812 to #815 ready in this order: #812, #814, #813, #815. (goes ahead when CI is green on all four, unless you object)
- **Y5** decision: Can I remove the worktrees ~/dev/shop-wt-cart and ~/dev/shop-wt-tax?

**Claude will check** (1)
- **A1** after the M2 stack merges: Re-check #820, which GitHub shows as conflicting.

Closed this turn: Y6 (dropped: #818 was closed); Y7 (superseded by Y5).
```

- Every open `Y` item is listed, in id order, every turn. Items opened at or after `--since` say "(new)"; lines closed at or after it go in "Closed this turn".
- `A` items are listed only when new, due, or named with `--show A1,A2` because they changed this turn.
- With nothing open, the block is one line: "Nothing waits on you."
- Above the block, write the reply as usual. Don't retype items in it.

## Subagents

Only you, the main agent, and Synopia's reader write the ledger. A subagent never edits it and never calls the `open_items` tool.

- **A brief names the ids the subagent owns**, with their text: `Open items: Y5 (keep main's Norway rates, answered "Main's"), A2 (re-run the tax specs on #818)`. Set each owned item's `subagent` field to the subagent's name. The brief asks the report for one line per closed id, `Closed: Y5 (done: rebased with main's rates, pushed)`, and for its questions to the user. The rule is in [subagents.md](../harness-common/references/subagents.md) "Brief minimum".
- **When the report comes back**, close the ids it says it closed, and remove `subagent` from the ones it didn't. Treat the report as claims, as ai-notes says: close on the evidence.
- **A question in the report becomes a `Y` item** with `raised by: <subagent name>`. The user answers it in the main conversation, like any item: the subagent has finished and can't hear it.
- **A finished `For review: ` subagent opens a `review` item**, text `Review: <name>` without the prefix, `subagent: <name>`. It closes when the user responds about it ("the copy is fine", "Y8: shorter subject line") or marks it reviewed.

## A new session and a handoff

- A new session in the area reads `open-items.md` with the area README. Its first reply that touches the work ends with the block.
- A handoff (ai-notes "Handing off to a new session") lists `open-items.md` first under "Where to read". The old session's last reply says which ids moved: "Handed off: Y1, Y2, Y4, Y5 and A1 are in <new session's title>". The ids stay as they are. `ledger.py check` prints the open ids.
- Before a handoff, drop a `Y` item untouched for 3 sessions, with a closed line saying so.

## Task tools are not the ledger

The host's task or todo tools are your working list for the job in front of you: steps you plan, work through and tick. The ledger is the contract with the user across turns and sessions. A task that waits on the user becomes a `Y` item; a ticked task is not an item. The ledger can't be built on the task tools: they are off by default on some models and hosts, and their lists live outside the repository ([Claude Code](<../harness-common/topics/Claude Code.md>) "Task tools").

## ledger.py

| Command | Prints | Exit |
|---|---|---|
| `check <file> [-v]` | `ok: <n> open (<ids>), <n> closed`, or `FAIL: <n> problems in <file>`; `-v` adds `line N: <problem>` per problem | 0, 1 FAIL |
| `next <file> Y\|A` | the next free id; `Y1` for a missing file | 0 |
| `block <file> [--since "YYYY-MM-DD HH:MM"] [--show ID,...]` | the reply's block | 0, 1 FAIL |
| `prune <file> [--keep 30]` | `pruned <n> closed lines, <n> kept` or `nothing to prune: <n> closed`; keeps the line of each prefix's highest id, so `next` never reuses one | 0, 1 FAIL |
| `init <file> [--area NAME]` | `created <file>`; refuses an existing file | 0, 2 |

A bad command line or a missing file prints `ledger.py: <cause>` on stderr and exits 2. `block` and `prune` refuse a file `check` fails; fix the lines `check -v` names first.
