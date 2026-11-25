# Builder brief

Fill the angle-bracket fields and pass the brief as the whole prompt of a background subagent whose description starts with `For review: `. Give it the strongest model tier available. Do not give it the conversation or your preferred option: it derives the options from the sources.

```
Goal: write a storyboard that answers one experience question for <project>, as one self-contained HTML page the author opens with a double-click and decides from.

The question: <one line, in the author's words>

Read first, in this order:
1. The writing-craft skill, in full. Its rules apply to every caption and summary line.
2. The frontend-design skill. Use it to match the look reference below exactly, not to restyle it.
3. The storyboard skill's SKILL.md, references/page.md and references/skeleton.html.
4. The sources, and nothing else:
   - Look reference: <path to the prototype or the app's CSS and markup>
   - Design rules: <AGENTS.md path, visual-system section of the requirements>
   - Behaviour spec: <requirements doc sections with their ids>, and the decisions and design notes about them
   - Current code: <paths> for what exists today
   - Earlier storyboards, for the page conventions: <paths>
   - Bundled fonts: <folder, or "none: use system fonts">

Scenarios to cover: <list from the framing step: first use, daily use, at scale, broken or missing data, keyboard only>

Write:
- The page at <project path>/prototype/<topic>-storyboard.html, starting from skeleton.html.
- Fonts by a relative path from the page's folder to the bundled font files.

Rules:
- One file: inline CSS and JS, no network request of any kind.
- Invented data only. No real names, tickets, pull request numbers, customers, home-folder paths or transcript text. Do not copy fixtures or logs from the project; invent the data.
- Copy the look reference's tokens and draw its existing parts as they are. Draw at the app's real sizes and window size.
- Options side by side only where the choice is real, two or three, exactly one marked Recommended with a one-line why; each other option has a one-line reason it loses.
- The recommendation has one way to do each thing.
- Every frame works in light and dark. The page reads ?theme=light and ?theme=dark.
- Follow every rule in the design rules file, in losing options too.
- Never open a browser window. Check with headless screenshots only.

Before you finish:
- Run /usr/bin/python3 -I <skill>/scripts/shoot.py <page>, look at both screenshots, and fix what is wrong: overflow, a frame unreadable in dark, a font that did not load.
- Search the page for real data: the author's name, user name, company, ticket prefixes, any path under the real home folder.

Report in under 150 words: the page path, the screenshot paths, the recommended design in three lines, the requirement changes by id, the open questions, and anything in the sources that contradicted itself.
```
