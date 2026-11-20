# Work folder formats

```
.tech-explo/<slug>/
  STATE.md                 stage, inputs, constraints, scope, SHA, page URLs, next step
  gates.json               one gate per section, written only by scripts/gate.py
  ledger.md                facts, gaps, contradictions, questions and answers
  sources/<family>.md      one digest per source family
  draft/attack-plan.md
  draft/technical-solution.md
  draft/evidence.md
  draft/design-proposal.md the Designer's proposed steps, input to the overview
  draft/alternatives.md    ruled-out designs, appendix of the technical solution
  audit/claims.md          numbered claims, audit/claims-<topic>.md verdicts
  audit/scope.md           scope items, audit/scope-verdicts.md
  reviews/round-<n>-<lens>.md   breaker findings per round
```

## STATE.md

```markdown
# <Project> tech exploration

Need: <one line>
Stage: 3 (technical solution), breaker round 2
Pinned SHA: <sha> (origin/<default branch>, <date>)
Pages: attack plan <url>, technical solution <url>, evidence <url>

## Inputs
- Product doc: <url>
- Designs: <paths>
- Earlier explorations: <urls>
- PRs of this project: <numbers>; reference PRs: <numbers>

## Hard constraints
- <constraint>, from <who>, <date>

## Scope
<five lines: who, what changes for them, what is in, what is out, what it depends on>

## Next
Stage 4, section step-2, loop step 4: ask question 3 of 5.
```

Gate status lives in `gates.json`, not in STATE: run `/usr/bin/python3 -I <skill>/scripts/gate.py status <work folder>`. Never edit `gates.json` by hand.

## Section ids

`intake`, `scope`, then `glossary`, `product-rules`, `page-<name>`, `out-of-scope`, `delivery`, `open-questions`, then `ready-for-review`, then `overview`, `step-<n>`, `data-and-rollout`, `verification`, then `milestones`, `tasks-m<n>`, then `audit`, `publish`. Each `--heading` is the section's heading text as written in the draft, without the `#` marks.

## ledger.md

```markdown
## Facts
- F12 · DESIGN · The week widget shows at most 3 tasks, most urgent due date first · sources/design-1.md · 2026-11-20

## Questions
- Q3 · product · open · Count overdue tasks from earlier weeks? · default: yes, shown as a red count
- Q4 · engineering · answered · Reuse the tasks index query? · yes, author in chat 2026-11-20
```
