# Audit: install-and-config

## Coverage
| File | Lines | Read fully |
|---|---|---|
| .gitignore | 2 | yes |
| README.md | 34 | yes |
| install.py | 109 | yes |
| targets/models.json | 4 | yes |
| instructions/global.md | 20 | yes |
Also read: head of agents/*.md (6 files), installed state in ~/.claude and ~/.config/opencode. `install.py --check` run: 0 changes needed (read-only).

## Functional behavior
- F1: Generate Claude agents from agents/*.md: frontmatter name, description, model (tier mapped), tools. Evidence: install.py:24-27. Status: active.
- F2: Generate opencode agents: description, mode: subagent, model only if tier maps to non-null; tools dropped. Evidence: install.py:30-35. Status: active.
- F3: Agent source format: `key: value` lines between `---` fences; required keys name, description, tier, tools. Evidence: install.py:17-21, 26-27, 31. Status: active. All 6 agents/*.md conform (tiers: strong x3, fast x2, default x1).
- F4: Tier map claude fast=sonnet, default=inherit, strong=opus; opencode fast=deepseek/deepseek-flash, default=null (omit model), strong=deepseek/deepseek-v4-pro. Evidence: targets/models.json:2-3. Status: active.
- F5: Copy instructions/global.md to ~/.claude/CLAUDE.md and ~/.config/opencode/AGENTS.md. Evidence: install.py:45-47. Status: active.
- F6: Symlink every dir in skills/ into both tools' skills/. Evidence: install.py:48-51. Status: active.
- F7: Tool detection: tool used if config dir exists or binary on PATH; override `--claude 0|1`, `--opencode 0|1`. Evidence: install.py:62-65. Status: active.
- F8: Idempotent plan: write only if content differs, link only if symlink target differs. Evidence: install.py:69-76. Status: active.
- F9: `--check` prints plan, exits 1 if changes, writes nothing. Evidence: install.py:81-83. Status: active.
- F10: Replacing existing items needs y at prompt or `--yes`; no TTY without --yes exits 2; declined exits 1. Evidence: install.py:84-94. Status: active.
- F11: Replace of existing real dir uses rmtree; existing file/symlink unlinked for links only; write overwrites. Evidence: install.py:97-104. Status: active.
- F12: Global instructions: 17 working rules (Serena, verify, secrets, delegation, notes, watcher, writing-craft, PR links). Evidence: instructions/global.md:1-20. Status: active.
- F13: .gitignore ignores .serena/ and .DS_Store. Evidence: .gitignore:1-2. Status: active.

## External facts and quirks
- X1: Claude Code agent frontmatter takes name, description, model (sonnet/opus/inherit), tools. Source: code (install.py:26-27), installed files work. Not verified against vendor doc.
- X2: opencode agent frontmatter takes description, mode, model as `provider/model`; agent name comes from file name. Source: code (install.py:32-35). Unverified vs vendor doc.
- X3: opencode model ids `deepseek/deepseek-flash`, `deepseek/deepseek-v4-pro` are not checkable offline. Source: unverified.
- X4: `/usr/bin/python3` hardcoded shebang (install.py:1); README says 3.9+ and macOS CLT Python. Source: README:30.
- X5: Descriptions of 3 agents contain a second `: ` and are emitted unquoted into YAML (install.py:26, 32). Strict YAML rejects this ("mapping values not allowed"). Claude Code and opencode apparently load them (installed 6 agents). Source: code + grep. Parser leniency unverified.

## Doc and code inconsistencies
- D1: README:8 lists agent keys `name`, `description`, `tier`, `tools`; code needs exactly these (KeyError otherwise). Consistent. True.
- D2: README:11 "Writes the global config of each tool found". True (install.py:62-65).
- D3: README:11 `--check` exits 1 on drift. True (install.py:83).
- D4: README:32 "Without a terminal and without --yes it stops and changes nothing." True, exits 2 (install.py:85-87). README does not state `--yes` in the table or usage line.
- D5: install.py:6 usage omits `--yes`, though it exists (install.py:60). Stale docstring.
- D6: README:30 "tools with no config folder and no binary on the PATH are skipped". True. Wrinkle: `--check` and install treat a tool as present if the folder exists, even with no binary.
- D7: README:8 says tools column exists; for opencode `tools` is ignored (install.py:30-35), so opencode subagents get default tool set. README does not say this.
- D8: README:34 "Rerun install.py after a pull that changes agents/, instructions/ or targets/". True. New skills dirs also need a rerun (links created per dir, install.py:48-51); README omits it.
- D9: README skill table lists 6 skills; skills/ has 7 dirs (ai-notes, attack-plan-create, attack-plan-milestone-execute, feedback-watch, qa-session, rearchitect, writing-craft). Table has 7 rows. Consistent.
- D10: README table omits the 6 agents (no agent list). Doc gap, not conflict.

## Assumptions to revalidate
- A1: Frontmatter lines all contain `: ` (install.py:20). Blank line, comment, multi-line value, or `key:` with empty value crashes with ValueError.
- A2: Frontmatter fence is exactly `---\n` and file starts with it (install.py:19). CRLF or missing fence -> ValueError unpack.
- A3: Body containing `---\n` is safe (maxsplit 2). A body starting before the first fence breaks: `text.split` first element is discarded silently.
- A4: Tier key is one of fast/default/strong (install.py:25, 31). Unknown tier -> KeyError traceback, no message.
- A5: Description is single-line, YAML-safe unquoted (install.py:26, 32). Quotes, leading `*`, `#`, `[`, trailing `:` would break the output.
- A6: Tool dir presence = tool installed (install.py:63-64). A stale ~/.config/opencode without opencode still gets writes.
- A7: `dest.parents` test picks base tool (install.py:70, 74). Works only because CLAUDE and OPENCODE paths are disjoint.
- A8: `/usr/bin/python3` exists (Linux/other hosts lack it). Mac-only by design.
- A9: Agents in global dirs are shared with user-owned agents; same file name is overwritten (with prompt). No namespace.
- A10: opencode `default: null` means inherit the global model; claude `inherit` is the equivalent. Unverified.

## Bugs
- B1 [medium]: No pruning. Renamed or removed agents/*.md and skills dirs leave stale files and dangling symlinks in ~/.claude and ~/.config/opencode; `--check` reports 0 changes. install.py:41-51 only adds. Scenario: delete skills/foo -> ~/.claude/skills/foo remains as a broken link.
- B2 [medium]: Broken symlink detection on replace path. `dest.exists()` false for dangling link, but `is_symlink()` handled in `replaced` (install.py:77). OK there. But line 97 `dest.is_dir() and not dest.is_symlink()` rmtree on an existing real skills folder that a user copied by hand: confirmed by prompt, but `--yes` deletes it with no backup. install.py:97-98. Scenario: user's hand-edited ~/.claude/skills/ai-notes with extra files -> deleted irrecoverably under `--yes`.
- B3 [medium]: `write` to dest that is an existing symlink (e.g. ~/.claude/CLAUDE.md symlinked to a repo file) writes through the link and modifies the link target. install.py:71, 102. Also `dest.read_text()` on a directory raises IsADirectoryError (install.py:71). Scenario: ~/.claude/CLAUDE.md is a symlink to another file -> that file is overwritten.
- B4 [medium]: Unquoted description with `: ` produces invalid strict YAML (X5). install.py:26, 32. Scenario: attack-plan-critic, rearch-auditor, rearch-phase descriptions.
- B5 [low]: Bad agent file gives a raw traceback with no file name (A1-A4). install.py:17-21.
- B6 [low]: No mkdir race issue, but running with `--check` when `skills/` or `agents/` is missing raises FileNotFoundError (install.py:41, 48).
- B7 [low]: `sys.exit(main())` at module level without `if __name__ == "__main__"` (install.py:109). Importing for tests executes main and exits. No tests for install.py exist (no tests dir at repo root).
- B8 [low]: `--check` returns 1 and writes nothing, but when the user declines, return 1 too (install.py:94) -> same code for "drift" and "declined".
- B9 [low]: `.gitignore` lacks `__pycache__/` and `*.pyc`. git status shows 5 untracked __pycache__ dirs (root and skills/*/scripts). `git ls-files` has no tracked pycache. Scenario: `git add -A` commits bytecode.
- B10 [low]: `.rearch/` is not ignored and not documented; unclear if intended committed (recent commits "rearch: inventory" suggest committed).

## Dead code, leftovers, stale comments
- L1: install.py:6 usage line omits `--yes`.
- L2: install.py:39 docstring says "Yields", function returns a tuple of dicts.
- L3: `import argparse, json, shutil, sys` all used. No dead imports.
- L4: .gitignore `.serena/` is a tool-specific leftover; harmless.
- L5: README:15 notes `.ai-notes/` committed by default; global.md:11 matches. Fine.

## Improvement areas
- I1: Add prune of managed outputs (track a manifest or detect symlinks pointing into ROOT that no longer have a source). Fixes B1.
- I2: Quote or block-scalar descriptions on render (json.dumps style double-quoted YAML). Fixes B4/A5.
- I3: Real frontmatter validation with named errors (file, key); required-key and tier check. Fixes A1-A4, B5.
- I4: Add `if __name__ == "__main__"` and unit tests (parse, render, plan) with `-I -m unittest`, matching other skills' test pattern. B7.
- I5: Backup instead of rmtree under `--yes`, or refuse to delete dirs that are not symlinks. B2.
- I6: Resolve symlink at dest before write or replace it (unlink first). B3.
- I7: Add `__pycache__/` to .gitignore; or run tests with `PYTHONDONTWRITEBYTECODE=1`. Note skills tests run with `-I`, which does not stop bytecode writes.
- I8: Map `tools` to opencode permissions, or document that it is ignored. D7.
- I9: Duplicate global instructions: ~/.claude/CLAUDE.md is the user's private file and also generated from instructions/global.md (content identical to install now). Installing overwrites local edits (prompt-guarded).
- I10: README should list agents and `--yes`.

## Interfaces
- Exposes: CLI `install.py [--check] [--claude 0|1] [--opencode 0|1] [--yes]`; exit codes 0 ok, 1 drift or declined, 2 non-tty unconfirmed. Agent source schema (name, description, tier, tools). targets/models.json schema (tool -> tier -> model|null). Installed paths: ~/.claude/{agents,skills,CLAUDE.md}, ~/.config/opencode/{agents,skills,AGENTS.md}.
- Consumes: agents/*.md (6 files, other aspects' prompts), skills/* dir names, instructions/global.md. Agent bodies refer to skills by name (rearchitect, attack-plan-create); global.md names skills ai-notes, feedback-watch, writing-craft.
- Threading: single synchronous process, no threads.

## Open questions for the user
- Q1: Should installs prune removed agents and skills?
- Q2: Is the opencode `tools` omission intended (opencode agents get all tools)?
- Q3: Are `deepseek/deepseek-flash` and `deepseek/deepseek-v4-pro` the exact opencode model ids?
- Q4: Should `.rearch/` be committed or ignored after the rearchitecture?
- Q5: Should ~/.claude/CLAUDE.md stay overwritten by the generated copy, or allow local additions?
