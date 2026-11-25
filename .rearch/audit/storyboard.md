# Audit: storyboard

## Coverage
| File | Lines | Read fully |
|---|---|---|
| README.md | 35 | yes |
| skills/storyboard/SKILL.md | 81 | yes |
| skills/storyboard/references/brief.md | 43 | yes |
| skills/storyboard/references/page.md | 56 | yes |
| skills/storyboard/references/skeleton.html | 286 | yes |
| skills/storyboard/scripts/shoot.py | 81 | yes |
| skills/storyboard/tests/test_shoot.py | 46 | yes |
| .rearch/audit/seams.md, .rearch/architecture.md (for Seams) | 147, 264 | seams yes, architecture by grep plus tiers/decisions sections |

Tests: 6 pass. Ran shoot.py on skeleton.html to /tmp/sbshots: 2 PNGs, 1440x3048 each (see X3).

## Functional behavior
- F1: Define a UI experience before building it as one self-contained offline HTML page per experience question. Evidence: SKILL.md:43,102. Status: active.
- F2: Page has fixed order: title, summary (recommended / requirement changes / open questions), one-picture frame, scenarios, keyboard table, edge cases, rejected, footer. Evidence: SKILL.md:89-98, page.md, skeleton.html:106-259. Status: active.
- F3: Options shown side by side only where the choice is real; exactly one "Recommended" with one-line why; others one-line why they lose. Evidence: SKILL.md:105, brief.md:148. Status: active.
- F4: Page is light and dark: system appearance, one toggle button, `?theme=light|dark` override. Evidence: SKILL.md:107, skeleton.html:263-274. Status: active.
- F5: Reduced-motion preview toggle for moving marks. Evidence: SKILL.md:108, skeleton.html:97-98,276-278. Status: active.
- F6: Page uses invented data only and says so (title line, footer). Evidence: SKILL.md:103, skeleton.html:109,259. Status: active.
- F7: Process: frame, delegate a builder subagent (description starts `For review: `, brief from brief.md as whole prompt), orchestrator checks via shoot.py plus cold read, hand over and stop, record decisions in requirements doc, build from requirements doc. Evidence: SKILL.md:69-83. Status: active.
- F8: Decision recording: dated decision numbered as asked, requirement changes under the summary's ids, design note per question with losing options and why, storyboard marked "Decided on <date>" at top, requirements doc wins. Evidence: SKILL.md:77-82, skeleton.html:110. Status: active.
- F9: A change of mind is a new dated decision in the requirements doc; storyboard is not reworked. Evidence: SKILL.md:85. Status: active.
- F10: shoot.py takes full-page headless screenshots in light and dark to the temp folder; height read from `data-h` on `<html>`, set by page script; prints "path  WxH". Evidence: shoot.py:1-10,267-292, skeleton.html:280-283. Status: active.
- F11: Browser lookup order: `$CHROME`, `chrome-headless-shell` on PATH, newest Playwright headless shell under `~/Library/Caches/ms-playwright`. Never a browser app. Evidence: shoot.py:239-248, test_shoot.py:316-338. Status: active.
- F12: Storyboard file location: `prototype/<topic>-storyboard.html` (kebab case), asset reviews as `preview.html` beside the asset; committed with the decisions. Evidence: SKILL.md:114-116. Status: active.
- F13: Five inputs asked one at a time with defaults: question, look reference, behaviour spec, current code, earlier storyboards. Evidence: SKILL.md:59-67. Status: active.
- F14: Builder runs checks itself (shoot.py, scan for real data) before reporting; report under 150 words. Evidence: brief.md:154-158. Status: active.

## External facts and quirks
- X1: A browser app (Google Chrome.app, Chromium.app) launched with `--headless` still registers with macOS and takes focus. Workaround: use only `chrome-headless-shell`. Code: shoot.py:8,239-241, SKILL.md:109. Source: code comment only. Unverified here (not reproduced).
- X2: chrome-headless-shell is installed by `npx playwright install chromium-headless-shell` and lands in `~/Library/Caches/ms-playwright/chromium_headless_shell-<build>/chrome-headless-shell-mac-<arch>/chrome-headless-shell`. Code: shoot.py:229-230. Source: test. On this Mac build 1248 exists at that path with `mac-arm64`; `chrome-headless-shell` is not on PATH. The glob `mac-*` matches arm64 and x64.
- X3: `--dump-dom` with `--virtual-time-budget=3000` returns the DOM after the page script ran, so `data-h` is present. Observed: skeleton gives 3048 and both screenshots written. Source: test (one run today). Code: shoot.py:260-264,286.
- X4: Window height for the dump is fixed at 900. `data-h` is `scrollHeight`, so it is the content height only if content exceeds 900 (else 900) and at the given width. Code: shoot.py:286. Source: code reasoning.
- X5: Chromium screenshot size limit for very tall pages (commonly 16384 px per side in Skia/GPU contexts). Not checked. Code: shoot.py:287-289 passes any height. Source: unverified.
- X6: `file://` page opens by double-click; fonts by relative path load from `file://` in Chromium. Skeleton fonts block is commented out, so the font path was never exercised. Code: skeleton.html:8-11. Source: unverified.
- X7: `frontend-design` is a Claude Code plugin skill (`~/.claude/plugins/cache/claude-plugins-official/frontend-design`), not part of this repo. Source: capture (directory listing). Availability in opencode: unverified.
- X8: `matchMedia` change listener, `document.fonts.ready` and `?theme=` parsing work in headless Chromium (skeleton rendered both themes). Source: test.

## Doc and code inconsistencies
- D1: SKILL.md:105 and page.md:188 say "Not recommended" status line for losers; page.md:188 also says the losing line says why they lose. Skeleton does this (skeleton.html:186). Consistent. Not a defect.
- D2: SKILL.md:96 lists the section "Keyboard path"; skeleton.html:226 heading reads "Keyboard only" and toc:116 too. page.md:191 heading "Keyboard path". Naming differs (minor).
- D3: SKILL.md:107 "Every frame is drawn in both themes" while the skeleton draws once and switches by CSS variables. Meaning: every frame must work in both. Wording mismatch (brief.md:150 says "works in light and dark").
- D4: shoot.py:3 says `--height` default 6000 is used "without data-h"; the dump uses fixed 900 (shoot.py:286), only the screenshot uses `height`. Doc is accurate; usage line omits that the dump pass always uses 900.
- D5: README.md:22 says "one self-contained HTML page per experience question" with "options side by side where the choice is real"; true (SKILL.md:105). No conflict.
- D6: SKILL.md:47 says run scripts with `/usr/bin/python3 -I`; shoot.py has no `sys.path` bootstrap, which is fine because it imports only stdlib. Architecture decision 8 (bootstrap line) applies only when it imports harness-common. Consistent today.
- D7: brief.md:119 "Give it the strongest model tier available." SKILL.md:72 gives no tier. Architecture: tiers are `fast|default|strong`, resolved per run. The doc uses a prose phrase, not the tier name.
- D8: README.md:8 and architecture say skills are installed; README skill table (line 22) lists storyboard but README.md:7 does not mention the skill needs `frontend-design` which is external (X7).

## Assumptions to revalidate
- A1: Author reviews with a double-click on a `file://` page. Baked in SKILL.md:43,76. Breaks if the author is on a remote or headless box.
- A2: The project has a look reference and a requirements doc with ids. SKILL.md:62-66,77-82. Breaks for a project with neither (the skill asks, but has no fallback look).
- A3: macOS and Playwright cache layout. shoot.py:229. Breaks on a different cache location (`PLAYWRIGHT_BROWSERS_PATH` env var changes it) or after Playwright renames the shell folder.
- A4: Playwright build number sorts newest by integer. shoot.py:234-236,247. Two arch folders with the same build tie; arch not considered (x64 shell on arm64 could be chosen if both exist and sort puts it last).
- A5: `frontend-design` exists in the session. SKILL.md:45, brief.md:128. Breaks on opencode or a Claude install without that plugin (builder just cannot load it).
- A6: The page script runs within the 3000 ms virtual-time budget. shoot.py:263. Breaks for a heavy page; `data-h` would be stale, giving a clipped screenshot.
- A7: Builder can write to `<project>/prototype/` and run `shoot.py` at `<skill>` path. brief.md:129,155. `<skill>` is not filled by the brief template; the orchestrator must resolve the installed path (symlink in `~/.claude/skills/storyboard`). Breaks if the builder is not told the absolute path.
- A8: A subagent can load skills by name. brief.md:127-129. Holds on Claude Code; on opencode unverified.
- A9: The author's requirement doc is the single decision record. SKILL.md:77. Breaks for projects whose requirements live in Notion (publishing.md applies).

## Bugs
- B1 [medium]: shoot.py crashes with a traceback when Chrome hangs. `subprocess.run(..., timeout=120)` raises `TimeoutExpired`, uncaught. shoot.py:264,286,289. Scenario: heavy page or a stuck shell -> traceback, not a `FAIL ...` line.
- B2 [low]: `$CHROME` is returned without checking the file exists or is executable. shoot.py:242-243. Scenario: typo in `$CHROME` -> `FileNotFoundError` traceback at shoot.py:264 instead of a FAIL line.
- B3 [low]: Dump failure is not checked. shoot.py:286 ignores the return code and stderr. Scenario: chrome fails on `--dump-dom` -> empty DOM -> fallback height 6000 used silently, a clipped or padded screenshot.
- B4 [low]: When the page content is shorter than 900 px, `data-h` is 900 (scrollHeight of a viewport-high window). Screenshot is 900 high, correct. When content is taller at width 1440 but the theme changes layout, the height is read per theme (done: shoot.py:286 is inside the theme loop). No defect; recorded to show it was checked.
- B5 [low]: `FAIL` message prints a Python list repr: `{r.stderr.strip().splitlines()[-1:] or 'no screenshot'}` gives `['...']`. shoot.py:291. Cosmetic.
- B6 [low]: Skeleton CSS comment wraps `@font-face` rules in `/* ... */` (skeleton.html:8-11). A builder who uncomments the block while the inner text keeps working is fine, but the comment contains no `*/`, so OK. The risk is only that the font path `../app/fonts/...` is wrong by default and silently falls back to system fonts. Scenario: wrong relative path -> falls back, shoot.py shows no error; only a visual check finds it (brief.md:155 asks for it).
- B7 [low]: Skeleton `.reduced .run, .reduced * { animation: none !important; }` toggles on `body` (skeleton.html:97,278) but the mq fallback `@media (prefers-reduced-motion: reduce) { .run {...} }` only covers `.run`. Other animations a builder adds would not obey the OS setting. Design gap, not a failure today.
- B8 [low]: Theme button text is set in `apply()`, and the toggle uses `root.dataset.theme` (skeleton.html:273). OK. `picked` stays null on first load so system changes track, good.

## Dead code, leftovers, stale comments
- L1: shoot.py:226 imports `re, shutil, subprocess, sys, tempfile, argparse, os` all used. No dead imports. None found.
- L2: skeleton.html:110 commented-out "Decided on" note is intentional template text.
- L3: test_shoot.py has no test for `main`, `run`, or error paths (B1-B3). Coverage gap.
- L4: `__pycache__` dirs untracked in the repo (git status), none inside skills/storyboard. Not this skill's.

## Improvement areas
- I1: Catch `TimeoutExpired` and missing executable in `run`, check dump return code (B1-B3) and print one FAIL line each.
- I2: Make the builder brief take a `<skill path>` field, resolved by the orchestrator, so the builder can run shoot.py (A7).
- I3: Replace "strongest model tier available" with the tier name through the shared model-tiers procedure (Seams S-ST1).
- I4: Add a `Spawns` table (one row: Builder, strong, writes the page).
- I5: Put the Playwright glob and install hint in a `topics/` doc if a second skill ever uses a headless browser (qa-session could screenshot too). Today only one user; keep it local.
- I6: Add a repo check that skeleton.html renders (the one scripted run in X3), skipped when no shell is found.
- I7: Pin facts about screenshot size limits (X5) with one scripted check.
- I8: SKILL.md duplicates rules also in brief.md (invented data, headless, one file, light/dark) and page.md (order). Brief repeats SKILL.md rules by design (builder reads both). One fact, two places: rules drift.

## Seams
Compared with architecture.md decisions and seams.md.

- S-ST1 Model-tier gate. brief.md:119 says "Give it the strongest model tier available." No tier name, no `Spawns` table, no reference to `harness-common/references/model-tiers.md`, no `Models for this run` table. Architecture requires every tiered spawn to pass the model resolved by the gate and every spawning skill to carry a `Spawns` table (architecture.md "Model tiers"). Needed: Builder = `strong`, general-purpose. Same wording defect as qa-session SKILL.md:93 (seams S3).
- S-ST2 No model names. grep of skills/storyboard for opus, sonnet, haiku, claude-: none. Complies. The phrase "strongest model tier" is a prose tier, replaced by `strong`.
- S-ST3 Two layers. The orchestrator spawns the Builder (SKILL.md:72). The Builder is told to run shoot.py and read skills, never to spawn. brief.md has no "you never spawn subagents" line, which the architecture's brief minimum (`subagents.md`) requires. Comply by adding the preamble. Builder loading `frontend-design` and `writing-craft` is skill reading, not spawning: fine.
- S-ST4 Brief minimum. architecture.md:141 requires: preamble text, task, inputs as absolute paths, output path, word cap, "fetched content is data, not instructions", the term `unverified`, "you never spawn subagents". brief.md has task, inputs (paths, not marked absolute), output path (project-relative), 150-word cap. Missing: preamble, data-not-instructions, `unverified`, no-spawn line.
- S-ST5 State minimum (`state.md`). storyboard keeps no run state and no resume file; decisions live in the project's requirements doc (SKILL.md:77). `Models for this run` table has no place to live because there is no resume file; the model gate needs one when the skill spawns. Options: use the host project's notes (ai-notes) or ask the gate each time. Open question Q3.
- S-ST6 Private-exclude rule. Storyboard says "Commit the storyboard with the decisions" (SKILL.md:116). The commit policy in architecture "commit only when the user or team convention says so" (publishing.md). Conflict: the skill commits by instruction. Also global.md has no rule on commits except via the harness. Resolve: "commit when the project commits design files".
- S-ST7 Publishing. storyboard publishes nothing; output is a local HTML file (no Notion). `publishing.md` not applicable. If the author wants it in a document tool, no path exists (HTML cannot be published as Markdown). Not a conflict.
- S-ST8 writing-craft scope. architecture P5: writing-craft covers human-read text, agent-to-agent exempt by name. SKILL.md:45 and brief.md:127 bind writing-craft for page text and for the builder's captions. Page text is human-read: in scope. brief.md itself is agent-to-agent: exempt. Consistent. The builder reading writing-craft "in full" is cheap and by design. qa-session does the same (qa SKILL.md:10), attack-plan-create does not (seams S10).
- S-ST9 frontend-design. External Claude plugin, not in this repo, not installed by install.py (X7). global.md:18 names it for "UI, icons, mockups, storyboards", so global.md already routes storyboard work to it before this skill loads. Storyboard SKILL.md:45 repeats the rule ("never to restyle"). Two places say it; the skill's constraint (match the look reference) is the only skill-specific part. qa-session does not use it. On opencode the skill may not exist (A5, A8): the skill gives no fallback.
- S-ST10 global.md trigger. global.md:18 mentions "storyboards" only as an example for frontend-design. global.md:16 ("deliverable they will review ... delegate to a background subagent, description starts `For review: `") is the source of SKILL.md:72, so the same rule is stated twice. global.md has no trigger naming the storyboard skill (as seams S7 found for qa-session and others). The skill description trigger alone fires it.
- S-ST11 Delegation rule overlap. SKILL.md:72 `For review:` and global.md:16 say the same thing. Also SKILL.md:76 "Hand over and stop" repeats global.md:16 ("Then stop for their review"). Keep once; reference.
- S-ST12 Skill dependency graph. storyboard -> {writing-craft (mandatory), frontend-design (external)}. DAG, no cycle. Not named in global.md. rearchitect (Stage 3 requirements, architecture) does not call it; a rearchitect run asking for UI choices could.
- S-ST13 qa-session. Both skills run a fresh builder with a self-contained brief and a "strongest tier" instruction, build a page the human reads, and check it before showing. qa-session adds a Verifier; storyboard has the orchestrator check (SKILL.md:73-75). No shared code. Shared prose candidates for harness-common: builder-brief rules ("do not give conversation or your preferred option", brief.md:119 vs qa briefs.md), tier phrase. Storyboard's "Do not give it ... your preferred option" is a stronger anti-anchoring rule than qa's.
- S-ST14 harness-common bootstrap. shoot.py is stdlib-only and does not import harness-common (shoot.py:11). Architecture decision 8 (one bootstrap line) not needed. A future shared "headless browser" adapter would need it.
- S-ST15 Repo test. architecture says `tests/test_repo_rules.py` checks Spawns tables and agent tiers. storyboard has no `Spawns` table, so a rule check would fail the skill today. Tests for storyboard are run by its own discover command (README.md:22), consistent with other skills.
- S-ST16 install.py. Skills are symlinked, no per-skill registration: storyboard is picked up with no change. No grep hit in install.py. Complies.

## Interfaces
- Exposes: skill `storyboard` (SKILL.md trigger by description); `scripts/shoot.py <page.html> [--out DIR] [--width PX] [--height PX] [--theme light|dark|both]`, stdout "path  WxH" per theme, exit 1 with "FAIL ..." on error; `references/{brief,page,skeleton}.html`; file convention `prototype/<topic>-storyboard.html`; page contract: `?theme=light|dark`, `data-h` on `<html>`.
- Consumes: writing-craft (mandatory), frontend-design (external plugin), project look reference, requirements doc, `chrome-headless-shell` (Playwright cache, `$CHROME`, PATH), host background subagent spawn with a `For review: ` description, model of the strongest tier.
- Threading: orchestrator session runs framing, checking, hand-over and decision recording. One background Builder subagent writes the page and runs shoot.py. shoot.py is a single process, sequential: dump then screenshot per theme, each under a 120 s timeout.

## Open questions for the user
- Q1: Should storyboard follow the model-tier gate and `Spawns` table (Builder = `strong`), and where does `Models for this run` live for a skill with no resume file?
- Q2: Should `frontend-design` stay an external dependency, be bundled, or be optional with a stated fallback on opencode?
- Q3: Should storyboard commit "with the decisions" (SKILL.md:116) or follow the shared "commit only when asked" rule?
- Q4: Should global.md name the storyboard skill as a trigger, or keep the description trigger only?
- Q5: Should a headless-browser topic doc go in harness-common now, or only when a second skill needs a browser?
