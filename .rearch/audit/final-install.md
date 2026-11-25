# Final audit: install

Files read in full: install.py 255, agents/*.md 233 (6), instructions/global.md 20, README.md 82, .gitignore 4, tests/ 482 + 3 fixtures, harness-common SKILL.md 48, claude_code.py 26, opencode.py 299, references 214 (5), test_adapters.py 257. Suites: tests 35 OK, harness-common 81 OK, no untracked files after the run.

Result: 54 rows: 52 mapped, 0 missing, 2 partial (NFR-09, FR-APE-15).

## 1. Traceability
| ID | file:line | Status |
|---|---|---|
| FR-INST-01 | claude_code.py:19-26, install.py:102 | mapped |
| FR-INST-02 | opencode.py:57-74, install.py:102 | mapped (adds `permissions`, deviation 3) |
| FR-INST-03 | install.py:103 | mapped |
| FR-INST-04 | install.py:94,104-105 | mapped |
| FR-INST-05 | install.py:227 | mapped (no test of autodetect, flag None) |
| FR-INST-06 | install.py:152-159,180; test_install.py:70 | mapped |
| FR-INST-07 | install.py:232-234 | mapped |
| FR-INST-08 | install.py:235-247 | mapped (exit 3) |
| FR-INST-09 | install.py:160-176,162-170 | mapped |
| FR-INST-10 | install.py:28-70 | mapped |
| FR-INST-11 | claude_code.py:24, opencode.py:58 | mapped |
| FR-INST-12 | install.py:147-155,197 | mapped |
| FR-INST-13 | install.py:147-150 | mapped (moves to backup) |
| FR-INST-14 | install.py:76-78,92-93 | mapped |
| FR-AGT-01 | install.py:19, README.md:61-70 | mapped |
| FR-AGT-02 | install.py:59, agents/*.md line 4, model-tiers.md:5-13 | mapped |
| FR-AGT-03 | agents/*.md line 4 (critic, designer, architect strong; reader, auditor fast; phase default) | mapped |
| FR-AGT-04 | agents/*.md line 5 (no Edit in four read-only agents) | mapped (opencode unenforced, deviation 2) |
| FR-AGT-05 | subagents.md:36-47 | mapped |
| FR-AGT-06 | preamble.md:1, opencode.py:23,74 | mapped (sandbox line opencode only) |
| FR-AGT-07 | model-tiers.md:27-49, opencode.py:105-147, state.md:18-36 | mapped |
| FR-AGT-08 | test_repo_rules.py:10-18,101-125; grep of group: 0 hits | mapped |
| FR-GLB-01 | global.md:1 | mapped |
| FR-GLB-02 | global.md:3-7 | mapped |
| FR-GLB-03 | global.md:8-10 | mapped |
| FR-GLB-04 | global.md:11-12 | mapped |
| FR-GLB-05 | global.md:13 | mapped |
| FR-GLB-06 | global.md:14 | mapped |
| FR-GLB-07 | global.md:15-16 | mapped |
| FR-GLB-08 | global.md:17 | mapped |
| FR-GLB-09 | global.md:18 | mapped |
| FR-GLB-10 | global.md:20 | mapped |
| FR-GLB-11 | global.md (no "Claude" outside :19) | mapped |
| FR-GLB-12 | global.md:19 | mapped |
| FR-XS-01 | preamble.md:1-7, subagents.md:12-22 | mapped |
| FR-XS-02 | tests/fixtures/markdown/fenced-headings.md (parser is markdown.py, other group) | mapped |
| FR-XS-03 | state.md:5-16 | mapped |
| FR-XS-04 | publishing.md:1-60 | mapped |
| FR-XS-05 | SKILL.md:46, install.py:8, README.md:51-57 | mapped |
| NFR-01 | install.py:1,10; README.md:43 | mapped |
| NFR-02 | README.md:43 | mapped |
| NFR-03 | install.py:231,250 | mapped |
| NFR-04 | install.py:254; tests/test_install.py; test_adapters.py | mapped |
| NFR-05 | .gitignore:3-4 | mapped |
| NFR-06 | install.py:152-159,232 | mapped |
| NFR-07 | README.md:59 | mapped |
| NFR-08 | README.md:3, both adapters | mapped |
| NFR-09 | agents/attack-plan-critic.md:12,14,16; designer:6,17,18; reader:13,15-17 | partial: same rules repeated across agents |
| NFR-10 | state.md:49-51, subagents.md:30-34 | mapped |
| NFR-13 | install.py:63-64, claude_code.py:9-11, opencode.py:21,53, preamble.md:7, subagents.md:5-10 | mapped |
| CON-CC-01 | claude_code.py:19-26 | mapped |
| CON-OC-01 | opencode.py:57-74 | mapped (V2 `permissions`, not `tools`) |
| CON-CC-04 | global.md:17 ("when available") | mapped |
| FR-APE-15 | README.md:17 only; build is in the execute skill, not this group | partial: README row says bot threads are resolved, not replied to |

## 2. Leftovers
1. README.md:82: no `@unittest.expectedFailure` test exists (grep: 0). Stale sentence. Doc edit.
2. opencode.py:78: `(A2)` cites an answer ID in requirements.md, which Stage 6 deletes. Comment edit.
3. Comments cite requirement IDs that vanish with `.rearch/`: claude_code.py:9,22; opencode.py:71; install.py:148,154. Decide: keep as ID labels or drop. Comment edit.
4. opencode.py:167-176: private `git()` helper duplicates `skills/harness-common/scripts/git.py` (deviation 10, Stage 6 candidate). Optional code change.
5. install.py:187: `verb` unpacked and unused in `apply`. Trivial.
6. tests/test_repo_rules.py:29-34: `frontmatter` and `check_agent` are one-line wrappers; `frontmatter` has one caller (:137). Optional.
7. agents/attack-plan-critic.md:16, reader:17: "Write nothing to any outside tool" repeated in 3 agents; critic:14, designer:17, reader:15 repeat the third-party-internals rule; critic:12 and reader:16 repeat the "start from sources" rule. Needs agent body edit if NFR-09 is enforced.
8. No reference to targets/models.json, models.py or old names found.

## 3. Doc and code mismatches
1. architecture.md:123-124: `render_agent(meta, body, preamble)` lacks the `model=None` parameter (opencode.py:66); `list_models(runner)` default is `run`.
2. architecture.md:138: opencode.py row says `apply-tiers`/`clear-tiers` "(conditional)", `apply-tiers --state F`. Built: `--general`, `--project` (opencode.py:270-275). Exit text lacks the stdout reload line.
3. architecture.md:112, :216: "task tool denied" and "C3 denies task". Built: the `subagent` action (opencode.py:21).
4. architecture.md:100: "install.py prepends the preamble" holds. architecture.md:52 C3 says "tools mapped to permissions": holds.
5. requirements.md CON-CC-03 (wrong, deviation 1), CON-OC-01 (`tools`, `model` text; deviation 3), FR-INST-02 (omits `permissions`), FR-INST-08 ("today both are 1"): stale, file is deleted in Stage 6.
6. deviations.md Phase 9 item 6 ("resolve after the user says the reply is posted") is superseded by FR-APE-15. README.md:17 must say the orchestrator replies to bot REPLY threads when FR-APE-15 is built.
7. README.md:76 test list matches tests/test_repo_rules.py (model names, caches, SKILL.md, agents, Spawns). OK.
8. README.md rows 10, 59, 72 match install.py and opencode.py. OK.

## 4. Model names and ids (FR-AGT-08)
0 hits in the group files. The only name-like string is test_repo_rules.py:124 (`magnum-opusculum`, a negative case, not a model). The regex covers 9 names and 2 id prefixes (:11-12); it misses other vendors' names. No change needed.

## Needs a code or doc change
- README.md:82 stale sentence.
- README.md:17 after FR-APE-15 is built.
- architecture.md:112,123-124,138,216 (deleted with `.rearch/`, so none if Stage 6 deletes it first).
- opencode.py:78 stale `(A2)`; comments citing IDs (item 2.3).
- opencode.py:167-176 git helper duplicate (optional).
- agent bodies, NFR-09 duplicates (optional).
