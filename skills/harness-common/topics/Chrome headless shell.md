# Chrome headless shell

Facts about `chrome-headless-shell`, the only browser `shoot.py` runs. Checked on 2026-11-25 on an arm64 Mac with the Playwright shell at build 1248 (`Google Chrome for Testing 156.0.8078.4`), output in `mktemp -d` folders. Docs: [Playwright, Browsers](https://playwright.dev/docs/browsers), [Chrome headless shell](https://developer.chrome.com/blog/chrome-headless-shell).

Code: `skills/storyboard/scripts/shoot.py`.

## Which binary

### Quirk: a browser app takes focus

- Symptom: Google Chrome.app or Chromium.app started with `--headless` registers with macOS and takes the user's focus.
- Cause: the app bundle registers as an application even in headless mode. `unverified`: not reproduced, on purpose, because the test would steal the user's focus.
- Workaround: run `chrome-headless-shell` only, never a browser app.
- Code: `shoot.py:8-9` (docstring), `:24-33` (`find_chrome`); `skills/storyboard/SKILL.md:74`.

| Fact | Source |
|---|---|
| Playwright ships a separate Chromium headless shell for headless runs, beside its regular Chromium build. | Playwright docs, "Chromium: headless shell" |
| `npx playwright install --only-shell` installs the shell without the full Chromium. | Playwright docs |
| `npx playwright install chromium-headless-shell` also installs it. | `shoot.py:15`, `unverified` as a command (the shell on this Mac exists, the command that installed it is not recorded) |
| The shell is not on `PATH` after a Playwright install. | Scripted check (`which chrome-headless-shell`) |

## Where Playwright puts it

| Fact | Source |
|---|---|
| Playwright's cache is `~/Library/Caches/ms-playwright` on macOS. | Playwright docs, "Managing browser binaries" |
| `PLAYWRIGHT_BROWSERS_PATH` moves the cache, both for install and for use. | Playwright docs, "Managing browser binaries" |
| The shell sits at `<cache>/chromium_headless_shell-<build>/chrome-headless-shell-mac-<arch>/chrome-headless-shell`, `<arch>` being `arm64` here. | Directory listing (build 1248, `mac-arm64`) |
| Several builds can sit side by side; the highest `<build>` is the newest. | `shoot.py:19-21` (`version`) |
| The x64 folder name is `chrome-headless-shell-mac-x64`. | `unverified` (not present on this Mac) |

Code: `shoot.py:14` (`PLAYWRIGHT` glob), `:24-33`. Today the lookup ignores `PLAYWRIGHT_BROWSERS_PATH` and the host architecture (FR-SB-10, Phase 8).

## Rendering

| Fact | Source |
|---|---|
| `--dump-dom` with `--virtual-time-budget=3000` prints the DOM after the page's scripts and `document.fonts.ready` ran, so the `data-h` attribute the skeleton sets is in the output. | `shoot.py` on `skeleton.html`, both themes 1440x3048 (`.rearch/architecture.md` "Verification") |
| `matchMedia` listeners, `document.fonts.ready` and the `?theme=` query work headless. | Same run |
| The dump runs in a 900 px tall window, so `data-h` (`scrollHeight`) is the content height only when the content is taller than 900 px. | `shoot.py:71`; code reasoning |

Code: `shoot.py:45-49` (`run`), `:70-77`. The page side: `skills/storyboard/references/skeleton.html:280-283`.

## Tall screenshots

| Fact | Source |
|---|---|
| `--screenshot` with `--window-size=1440,<H>` writes a PNG exactly `<H>` px tall for every `<H>` tried: 16384, 16385, 20000, 40000, 65536, 100000, 200000. | Scripted check |
| The pixels are painted to the bottom: a red-to-blue gradient page reads red at the top, purple in the middle and blue at the bottom, at 16384, 20000 and 40000 (full decode) and at 65536, 100000 and 200000 (decoded strips). | Scripted check |
| The 16384 px limit often cited for GPU contexts does not apply to this shell with `--disable-gpu`. No limit was found up to 200000 px. Above that: `unverified`. | Scripted check |
| A 200000 px shot took 6.6 s and wrote 3.5 MB. | Scripted check |

Code: `shoot.py:72-77` passes any height. Phase 8 caps it at 200000, the largest height measured, and marks the line `clipped from <H>` (SB-Q7).

## Fonts from `file://`

| Fact | Source |
|---|---|
| A `file://` page loads a font by a relative `url()`: `@font-face { src: url("fonts/<file>.ttf") }` with the file copied from `/System/Library/Fonts/Supplemental` gives `document.fonts.check(...) == true` and status `loaded` in `--dump-dom`. | Scripted check, headless shell |
| A relative `url()` to a missing file gives status `error`, and the page still renders. | Scripted check |
| The same in a desktop browser opening the page by double-click: `unverified`. | none |

Code: `skills/storyboard/references/skeleton.html:8-11` (the commented-out font block).
