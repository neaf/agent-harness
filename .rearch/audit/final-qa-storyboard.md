# Final audit: qa-storyboard

Result: 37 requirements: 36 mapped, 1 partial, 0 missing. 0 model names. Tests: qa-session 22 OK, storyboard 24 OK.
Paths below are under skills/. Line numbers are real file lines. FR-APE-15 is outside this group (execute skill); not checked here.

## 1. Traceability

| ID | file:line | Status |
|---|---|---|
| FR-QA-01 | qa-session/SKILL.md:26-34 | mapped |
| FR-QA-02 | qa-session/SKILL.md:14-24 | mapped |
| FR-QA-03 | qa-session/SKILL.md:36-46,62 | partial (code ok; requirement text stale, see 3.1) |
| FR-QA-04 | qa-session/SKILL.md:48-57 | mapped |
| FR-QA-05 | qa-session/SKILL.md:59-67; references/briefs.md:76-78 | mapped |
| FR-QA-06 | qa-session/SKILL.md:69-74 | mapped |
| FR-QA-07 | qa-session/SKILL.md:8,80-81; references/page-template.md:3-55 | mapped |
| FR-QA-08 | SKILL.md:85; page-template.md:64; setup-checklist.md:11; briefs.md:37 | mapped |
| FR-QA-09 | scripts/check_page.py:17-31,34-107; tests/test_check_page.py:57-167 | mapped |
| FR-QA-10 | SKILL.md:90-97 -> harness-common/references/publishing.md:14-47 | mapped |
| FR-QA-11 | references/setup-checklist.md:1-47 | mapped |
| FR-QA-12 | SKILL.md:99-107; references/briefs.md:1-11 | mapped |
| FR-QA-13 | SKILL.md:108 | mapped |
| FR-QA-14 | SKILL.md:110-117 | mapped |
| FR-QA-15 | check_page.py:95-105; test_check_page.py:122-127 | mapped |
| FR-SB-01 | storyboard/SKILL.md:14-22 | mapped |
| FR-SB-02 | SKILL.md:24-32 | mapped |
| FR-SB-03 | SKILL.md:34-50 | mapped |
| FR-SB-04 | SKILL.md:42-50 | mapped |
| FR-SB-05 | SKILL.md:52-63; references/page.md:1-60; skeleton.html:116,226 | mapped |
| FR-SB-06 | SKILL.md:65-75; page.md:1-60 | mapped |
| FR-SB-07 | SKILL.md:72; skeleton.html:22,263-274 | mapped |
| FR-SB-08 | SKILL.md:73; skeleton.html:94-98,276-278; test_shoot.py:219 | mapped |
| FR-SB-09 | scripts/shoot.py:1-8,96-119 | mapped |
| FR-SB-10 | shoot.py:38-55; test_shoot.py:62-111 | mapped |
| FR-SB-11 | shoot.py:84-93,96-119,121-134; test_shoot.py:186-212 | mapped |
| FR-SB-12 | shoot.py:67-76; test_shoot.py:169,174 | mapped |
| FR-SB-13 | SKILL.md:77-81 | mapped |
| FR-SB-14 | SKILL.md:83-90; references/brief.md:1-37 | mapped |
| FR-SB-15 | SKILL.md:10; brief.md:15-17 | mapped |
| FR-SB-16 | SKILL.md:92-101 | mapped |
| CON-NOTION-01 | harness-common/topics/Notion MCP.md:9-95 (all 8 quirks) | mapped (code locations overclaim, see 3.3) |
| CON-CHROME-01 | Chrome headless shell.md:9-14; SKILL.md:74 | mapped |
| CON-CHROME-02 | Chrome headless shell.md:16-33 | mapped |
| CON-CHROME-03 | Chrome headless shell.md:35-44 | mapped |
| CON-CHROME-04 | Chrome headless shell.md:46-55; shoot.py:17 | mapped (checked to 200000) |
| CON-CHROME-05 | Chrome headless shell.md:57-65; skeleton.html:8-11 | mapped (checked in headless shell) |
| NFR-14 / NFR-15 (evidence) | shoot.py:38-55,84-93,96-119 | mapped |

Counts: FR-QA 15, FR-SB 16, CON-NOTION 1, CON-CHROME 5 = 37.

## 2. Leftovers

1. storyboard/scripts/shoot.py:62-64 `page_height` is dead in production. `shot_height` (67-76) repeats its regex lookup. Used only by tests/test_shoot.py:10,52,55. Needs code change: delete it, test `shot_height`.
2. storyboard/tests/test_shoot.py:140-142 handles `SystemExit` with a str code. `shoot.main` now exits with int 1 only (shoot.py:134). Stale branch. Needs code change.
3. storyboard/scripts/shoot.py:105,118-119 `lines` is built and returned; the caller (line 131) ignores it. Harmless. Optional code change.
4. storyboard/references/skeleton.html:97 `.reduced .run, .reduced *` : `.run` is already inside `*`. Optional code change.
5. No references to deleted files, old names or old behavior in the group. Checked: `finding_rows`, "Keyboard only" (only in a negative test, test_shoot.py:233), Known limits, Product questions, After the session, findings table, old publishing.md paths, "strongest model tier". Notion MCP.md:5 names the old path on purpose (tag `rearch-base`).
6. `__pycache__` in qa-session/scripts is ignored by .gitignore:3. No action.

## 3. Doc/code mismatches

1. requirements.md:335-337 FR-QA-03 lists `previous.md` in the session folder. Code puts it at `.ai-notes/.qa-previous/<slug>.md` (qa-session/SKILL.md:62,67; briefs.md:11,78) and adds `derivation.md` (SKILL.md:44). Logged in phases.md:156, not in deviations.md. Doc change only (Stage 6).
2. requirements.md:357 FR-QA-09 still says "check before As line" and "Known limits" checks; code has the persona-line rule and `--live` (check_page.py:81-82,6). requirements.md:470-482 FR-SB-12 and CON-CHROME-04/05 (lines 536-537) still say "Phase 1 check"/unverified; both were checked (deviations.md:9, Chrome topic doc 46-65). Doc change only.
3. harness-common/topics/Notion MCP.md:25,32,39,46,53,60,67,74,81,88,95 ("Code:" lines) name `publishing.md` "Notion" steps as holding each workaround. publishing.md:41-48 holds only: `<callout>`, `<table>` tags, small anchored `update_content` edits, re-fetch. Missing there: probe tools before a long write, append sections in order, tabs for nested lists, scan for ` • `, balanced backticks, anchor around a mention, re-fetch bold-with-code, discussion-urls, lookbehind. Needs change: either add the workarounds to publishing.md:43-48 or fix the Code lines to say "this doc".
4. architecture.md:135 CLI row `check_page.py <page> [-v]` lacks `[--live]` (deviations.md:142 said Stage 6 fixes it). Doc change.
5. harness-common/topics/Chrome headless shell.md:20 calls `npx playwright install chromium-headless-shell` `unverified`; storyboard/SKILL.md:74 and shoot.py:14 state it as the install step. Consistent only if SKILL.md says "unverified" or the command is run once. Optional.
6. Chrome headless shell.md:44 cites `shoot.py:105-117` for the loop; the loop is shoot.py:107-118. Off by 2. Doc change.
7. README.md:20-21,32,34 rows match the code. No stale README row.

## 4. Model names and ids (FR-AGT-08)

0 hits in the group's files (grep for sonnet, opus, haiku, deepseek, gpt-, gemini, claude-<digit>, `model:`). Tiers appear only as `strong` (qa-session/SKILL.md:103-104; storyboard/SKILL.md:87).

## Code changes needed

1. shoot.py:62-64 remove dead `page_height`; update test_shoot.py:10,52,55.
2. test_shoot.py:139-142 remove the str `SystemExit` branch.
3. Notion MCP.md Code lines (or publishing.md:43-48): make them true.
