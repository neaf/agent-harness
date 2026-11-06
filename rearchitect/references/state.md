# .rearch/ file formats

All files are Markdown, committed on the `rearch/<date>` branch.

```
.rearch/
  STATE.md           current stage, phase, decisions, next prompt
  baseline.md        build/test commands, results, manual checklist M1..Mn
  inventory.md       every file -> kind, lines, aspects
  audit/<aspect>.md  one report per aspect, plus seams.md
  requirements.md    consolidated functional requirements
  architecture.md    target design
  docs-plan.md       target docs and fate of every current doc
  phases.md          ordered phase plan
  deviations.md      plan changes found during execution
```

## STATE.md

```markdown
# Rearchitect state

Project: <one line>
Branch: rearch/2026-10-29
Base tag: rearch-base (<hash>)
Stage: 5 (phase execution)
Phase: 3 of 9 (MIDI engine), not started

## Done
- Stage 0 setup, <hash>
- Phase 2 test harness, <hash>

## Decisions
- 2026-10-29: drop arpeggiator experiment (FR candidate SEQ-07), user call.

## Next prompt
    Use the rearchitect skill. Continue from .rearch/STATE.md.
    Next: Phase 3 (MIDI engine).
```

## inventory.md

| File | Kind | Lines | Aspects |
|---|---|---|---|
| src/midi/out.cpp | source | 412 | midi |
| docs/push-notes.md | doc | 230 | push2, ui |

Totals per aspect at the bottom.

## requirements.md

```markdown
# Functional requirements

## <Area>
- FR-SEQ-01: The sequencer advances one step per 1/16 note at host tempo.
  Evidence: src/seq/clock.cpp:88, audit/sequencing.md#F3
  Status: kept

## Non-functional
- NFR-01: Audio thread does no allocation and takes no locks.

## Constraints from external systems
- CON-PUSH-01: Push 2 display frames are 960x160 BGR565, XOR-masked. See docs/Push 2.md.

## Dropped
- SEQ-07 arpeggiator experiment, dropped 2026-10-29.

## Open questions
- Q1: ...
```

Every FR carries evidence and a status: kept, dropped, or open.

## architecture.md

Sections: overview diagram (ASCII), modules with one responsibility each, data flow, threading and real-time model, interfaces between modules, error handling, external-system adapters (one per topic doc), FR to module traceability table, old to new file mapping, what gets deleted.

## docs-plan.md

| Current doc | Fate | Target |
|---|---|---|
| notes/push-reverse.md | fold facts, delete | docs/Push 2.md |
| TODO-old.md | delete | |

Plus the list of target docs with a one-line scope each.

## phases.md

```markdown
## Phase 3: MIDI engine
Goal: one MidiRouter replaces midi/out.cpp, midi/hack_bridge.cpp.
Covers: FR-MIDI-01..06, NFR-01
Touches: src/midi/*, src/plugin/processor.cpp
Deletes: src/midi/hack_bridge.cpp
Verify: build, unit tests, M2, M4
Exit: all listed FRs pass, no references to hack_bridge remain.
```
