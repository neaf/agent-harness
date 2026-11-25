# Audit: qa-session

## Coverage
| File | Lines | Read fully |
|---|---|---|
| README.md | 34 | yes (qa-session row line 21 checked; rest skimmed for claims about this skill) |
| skills/qa-session/SKILL.md | 111 | yes |
| skills/qa-session/references/briefs.md | 71 | yes |
| skills/qa-session/references/page-template.md | 85 | yes |
| skills/qa-session/references/publishing.md | 29 | yes |
| skills/qa-session/references/setup-checklist.md | 45 | yes |
| skills/qa-session/scripts/check_page.py | 114 | yes |
| skills/qa-session/tests/test_check_page.py | 100 | yes |

Tests: 9 run, OK. Regex behaviors below were reproduced with scan().

## Functional behavior
- F1: Three modes (Create, Rework, Live edit), chosen from state; never rebuild a page with ticks or findings without asking. Evidence: SKILL.md:26-34. Status: active (prompt-only).
- F2: Required inputs: spec, code at a commit, seed, environment; optional publishing target; ask one question at a time. Evidence: SKILL.md:14-24. Status: active.
- F3: Session folder `.ai-notes/qa-<slug>/` with README.md, sources.md, decisions.md, rework-log.md; page never holds history. Evidence: SKILL.md:36-45. Status: active.
- F4: Create flow: sources, Builder subagent, check_page, Verifier subagent, show shape, publish after go-ahead. Evidence: SKILL.md:47-56. Status: active.
- F5: Rework: Builder re-derives in a fresh subagent that never sees the previous page; carry over ticks/findings by scenario title and check text; change report. Evidence: SKILL.md:58-66, briefs.md:69-71. Status: active.
- F6: Live edit: targeted edits, keep ticks, untick on meaning change, run check_page after. Evidence: SKILL.md:68-73. Status: active.
- F7: Page shape fixed: Before the session, Known limits, Walk-through, Product questions, Findings, After the session. Evidence: page-template.md:5-77. Status: active.
- F8: Exact-label rule: every on-screen word is the label that scenario's user sees, in their language, traced to code; no paraphrase; per-persona labels. Evidence: SKILL.md:86, briefs.md:29, briefs.md:58. Status: active, prompt-only (no script check).
- F9: check_page.py decides mechanical rules: emoji, internal ids, `<placeholder>`, TODO/TBD/FIXME/XXX, bare "today" (WARN), "(cont.)" (WARN), check before "As" line, scenario numbering, scenario without checks (WARN), missing Known limits (WARN), Findings (FAIL), Product questions (WARN). Exit 1 on FAIL. Evidence: check_page.py:11-20, 48-87, 110. Status: active.
- F10: Publishing: markdown file default (`docs/qa/<slug>/session.md`), or MCP document tool with template mapping, read-back count check, fetch before update. Evidence: publishing.md:5-23. Status: active.
- F11: Setup checklist: seed idempotent, one labeled line per check, "found N of N", values printed before session, no passwords on page. Evidence: setup-checklist.md:5-45. Status: active.
- F12: Fallback without subagents: run briefs yourself, separate passes, note in README. Evidence: SKILL.md:94. Status: active.
- F13: Stop/resume handoff text. Evidence: SKILL.md:96-103. Status: active.

## External facts and quirks
- X1: check_page.py uses `#!/usr/bin/python3` and is run with `/usr/bin/python3 -I`; macOS system Python is 3.9 (pycache is cpython-39). Code uses no 3.10+ syntax. Source: code (check_page.py:1, SKILL.md:12, README.md:30).
- X2: Document-tool quirks (cell limits, mention escaping, dropped blocks) are deliberately kept out of the skill and recorded per session in `sources.md` "Tool notes". Source: publishing.md:23. Unverified; no examples recorded.
- X3: Emoji regex covers U+1F000-1FAFF, U+2600-27BF, U+2B00-2BFF. It flags dingbats such as the check mark and cross, and arrows in 2B00 block. Source: code (check_page.py:11).

## Doc and code inconsistencies
- D1: Exact-label rule (SKILL.md:86, briefs.md:29,58) vs page-template.md. The template has no statement of the rule. Only line 34 says "user label in the UI's words" and line 40 "what is on screen". setup-checklist.md also silent. The recent commits (27c2f5a, d4b56d4) touched only SKILL.md and briefs.md. A Builder reads template first and gets no reminder; the rule appears only in the brief.
- D2: Exact-label rule vs check_page.py. The script FAILs on `Q4`, `S3`, `D2` etc. (INTERNAL_ID, check_page.py:12,50-51) and WARNs on "today" (check_page.py:15). A UI label "Q4 Budget", "S3 bucket" or a "Today" button, written exactly as required, trips the script. Reproduced: "Menu shows Q4 Budget and S3" gives two FAILs. No override or exemption (for example inside backticks or quotes) exists. SKILL.md:52 says "fix every FAIL", so the builder is pushed to paraphrase, which the label rule forbids.
- D3: Briefs.md:31 bans bare "today" and bare "now". Script checks only "today" (check_page.py:15). SKILL.md:87 says only "bare today".
- D4: SKILL.md:89 lists what the script checks. It omits "(cont.)" (check_page.py:58), unfinished markers (check_page.py:14,54), and scenario numbering.
- D5: briefs.md:34 says "US English". SKILL.md:86 and briefs.md:29 say labels are in the persona's language. Prose vs labels is not separated; a non-English UI conflicts on its face.
- D6: page-template.md:3 says the finished page has no square-bracket placeholders. check_page.py detects only `<...>` (check_page.py:13). A leftover `[Fact.]` passes (reproduced). Template placeholders are `[...]`, so the check misses exactly the template's own placeholders. SKILL.md:89 claims "placeholders" are checked.
- D7: SKILL.md:87 "Each session starts with an empty Findings table." Script counts rows (check_page.py:60-61) but never warns when rows exist at Create. Only reported in the summary line.
- D8: SKILL.md:8 describes the page as "setup, walk-through, product questions, findings". Template also has "Known limits" (before walk-through) and "After the session" (page-template.md:73-77). Not in SKILL.md section list; script ignores After.
- D9: SKILL.md:52 writes `check_page.py <page> -v` without the interpreter or `<skill>/scripts/` prefix defined at SKILL.md:12. briefs.md:36 uses `<skill>/scripts/...` but "Fill the angle-bracket fields" (briefs.md:3) does not list `<skill>` as a field to fill.
- D10: briefs.md:11 tells the Builder to read "the qa-session skill's references/..." with no path. A subagent without the skill folder path cannot resolve it. Same for "writing-craft skill" (briefs.md:10).
- D11: README.md:21 matches SKILL.md in substance. README test command matches the one in the task. True.

## Assumptions to revalidate
- A1: Subagents can be spawned as "general-purpose on the strongest model tier" (SKILL.md:93, briefs.md:3). Claude Code and opencode name tiers differently (targets/models.json: fast/default/strong). If a tool lacks tier selection, the skill has only the self-run fallback (SKILL.md:94).
- A2: writing-craft skill exists at `../writing-craft/SKILL.md` (SKILL.md:10). True now (skills/writing-craft). Breaks if skills are installed individually.
- A3: ai-notes skill conventions (SKILL.md:38). Exists. Breaks if the notes layout changes in the rearchitecture.
- A4: Scenario headings are exactly `### N. Title` (check_page.py:16). `### 1 Title` is silently ignored (reproduced: 0 scenarios, no FAIL, no WARN).
- A5: Page is plain markdown with no fenced code. A fenced block containing `# comment` lines is read as a heading (check_page.py:19,34-47), resets `current`, and ends `in_findings`. Setup-checklist.md:29-33 mentions console snippets, which on a page would be fenced. Inferred from code, not reproduced end to end.
- A6: A line starting "As " is the persona line (check_page.py:18). "As expected, ..." before the real line satisfies it, and the reverse check passes (reproduced the opposite direction only).
- A7: Verifier can trace labels to translation keys in code (briefs.md:29,58). Needs the code checkout and translation files in the subagent's reach; sources list only "paths or areas".
- A8: Findings table lives in the same markdown file during the session (publishing.md:9), while SKILL.md:64 matches ticks by title and check text. Duplicate check text in two scenarios makes the match ambiguous.

## Bugs
- B1 [medium]: INTERNAL_ID false positives on real UI labels and common words. check_page.py:12,50. Scenario: check text "The menu shows Q4 Budget" or "S3 bucket", "D2C", "R2" -> FAIL "internal id". Case-sensitive but no context filter; no exemption. Conflicts with the exact-label rule (D2).
- B2 [medium]: Leftover `[...]` template placeholders pass. check_page.py:13. Scenario: page keeps "- [ ] [Next fact.]" -> counted as a check, zero findings (reproduced).
- B3 [medium]: Heading `### 1 Title` or `### 1) Title` not recognized as scenario; its checks count toward totals but no scenario/order/As-line validation. check_page.py:16,39-45. Scenario: 0 scenarios reported, exit 0.
- B4 [low]: Fenced code lines starting `#` or `- [ ]` are parsed as headings and checks. check_page.py:34,63.
- B5 [low]: AS_LINE `^As \S` matches ordinary prose such as "As expected, ...". check_page.py:18,73. Scenario: prose line before the first check masks a missing persona line.
- B6 [low]: After the first "check before As" FAIL, `current["as"]` is set True (check_page.py:71), so later checks in that scenario pass. One FAIL per scenario, fine; but a persona line placed after the checks is accepted silently for later checks.
- B7 [low]: BARE_TODAY WARN fires on a legitimate "Today" UI label or "today" inside a quoted label. check_page.py:15,56.
- B8 [low]: PLACEHOLDER lookahead excludes tags by prefix with `\b`; `<input>`, `<table>`, `<div>` and a label like `<All users>` are flagged as placeholders. check_page.py:13. Only the whitelisted tag set passes.
- B9 [low]: "Findings" is detected by heading prefix (check_page.py:38,84); "### Findings from earlier sessions" or any heading starting "findings" satisfies it. Row count includes only rows starting with a digit cell (check_page.py:20), so a row with `| # |`-less format is missed.

## Dead code, leftovers, stale comments
- L1: skills/qa-session/scripts/__pycache__/ (untracked, git status shows `?? __pycache__/` dirs elsewhere; this one is present on disk). Leftover from a run without PYTHONDONTWRITEBYTECODE.
- L2: check_page.py:5 docstring says "Facts ... are the verifier's job". Still true. No stale claims found.
- L3: README.md:21 and SKILL.md:12 both define the test/run command separately. Duplicate but consistent.

## Improvement areas
- I1: Exact-label rule has no mechanical support. Add an optional labels file (strings the Builder resolved from translation keys) and have check_page.py compare every quoted or bold label on the page against it, or at least list unmatched `**bold**` and backticked words. Removes reliance on the Verifier alone for the newest rule.
- I2: Give INTERNAL_ID and BARE_TODAY an exemption for text in quotes or backticks, so exact labels pass. Fixes D2/B1/B7.
- I3: Detect `[...]` placeholders outside link syntax and outside checkbox markers. Fixes D6/B2.
- I4: Strip fenced code blocks before scanning. Fixes B4.
- I5: Warn on any heading `### <digits>` that is not `### N. `. Fixes B3.
- I6: Add "now" to BARE_TODAY, add "(cont.)" and unfinished markers to SKILL.md:89. Fixes D3/D4.
- I7: Add the exact-label rule to page-template.md (As line, Check line, Known limits entries) and to setup-checklist.md. Fixes D1.
- I8: Test gaps: no tests for UNFINISHED, "(cont.)", scenario without checks, missing Known limits, missing Product questions, `main()` exit code and summary line, `-v` output format, order of FAIL/WARN, INTERNAL_ID false positives. 9 tests cover about half the rules.
- I9: Move shared rules (page rules appear in SKILL.md:77-87, briefs.md:25-34, template notes) into one place; today the Builder rule list and SKILL page rules are two copies that already drift (D3, D5).
- I10: Define `<skill>` and the reference paths in briefs.md so a subagent can resolve them (D9/D10).

## Interfaces
- Exposes: skill `qa-session` (SKILL.md frontmatter name/description); CLI `check_page.py <page.md> [-v]`, summary line to stdout, exit 0/1; function `scan(lines) -> (findings, counts)` used by tests; two subagent briefs (Builder, Verifier) in references/briefs.md; session folder layout `.ai-notes/qa-<slug>/`; handoff text SKILL.md:100-103.
- Consumes: writing-craft skill (mandatory, SKILL.md:10); ai-notes skill (folder conventions, SKILL.md:38); subagent spawning with tier selection; MCP document tools discovered by tool search (publishing.md:14); git (code at commit via `git show`); `/usr/bin/python3` 3.9.
- Threading: no threads. Orchestrator runs steps sequentially; Builder and Verifier run as separate fresh subagents; check_page.py runs as a short subprocess.

## Open questions for the user
- Q1: Should exact UI labels be exempt from check_page.py FAIL rules (Q4, S3, "Today")? If yes, by what marker (backticks, quotes, bold)?
- Q2: Should the exact-label rule be enforced by script via a Builder-written labels file, or stay with the Verifier?
- Q3: "US English" vs persona-language labels: confirm prose is US English and labels follow the UI language.
- Q4: Is "After the session" part of the required shape? Script and SKILL.md ignore it.
- Q5: Should a non-empty Findings table at Create be a FAIL?
