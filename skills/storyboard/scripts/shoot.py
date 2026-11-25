#!/usr/bin/python3
"""Takes full-page headless screenshots of a storyboard, in light and dark.

Usage: shoot.py <page.html> [--out DIR] [--width PX] [--height PX] [--theme light|dark|both]
Prints one line per screenshot: its path and size. Never opens a window.
The page reads ?theme=light|dark. Its full height comes from the data-h attribute the
skeleton sets on <html>; without it, --height (default 6000) is used.
Browser: $CHROME, else chrome-headless-shell on PATH, else the newest Playwright headless shell.
Never a browser app: Google Chrome.app takes focus on macOS even with --headless.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

PLAYWRIGHT = "Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac-*/chrome-headless-shell"
INSTALL = "install it with: npx playwright install chromium-headless-shell"
HEIGHT = re.compile(r'<html[^>]*\bdata-h="(\d+)"')


def version(path):
    m = re.search(r"chromium_headless_shell-(\d+)", str(path))
    return int(m.group(1)) if m else -1


def find_chrome(env=os.environ, home=None):
    """chrome-headless-shell only. A browser app (Google Chrome.app, Chromium.app) registers
    with macOS and takes focus even with --headless, so it is never a candidate."""
    if env.get("CHROME"):
        return env["CHROME"]
    found = shutil.which("chrome-headless-shell", path=env.get("PATH"))
    if found:
        return found
    shells = sorted(Path(home or Path.home()).glob(PLAYWRIGHT), key=version)
    return str(shells[-1]) if shells else None


def page_url(page, theme):
    return Path(page).resolve().as_uri() + f"?theme={theme}"


def page_height(dom, fallback):
    m = HEIGHT.search(dom)
    return int(m.group(1)) if m else fallback


def run(chrome, profile, width, height, *args):
    cmd = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", f"--user-data-dir={profile}",
           f"--window-size={width},{height}", "--virtual-time-budget=3000", *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "storyboard-shots"))
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=6000)
    ap.add_argument("--theme", choices=("light", "dark", "both"), default="both")
    a = ap.parse_args()
    chrome = find_chrome()
    if not chrome:
        sys.exit(f"FAIL no chrome-headless-shell found; {INSTALL}")
    if not os.path.isfile(a.page):
        sys.exit(f"FAIL {a.page} not found")
    os.makedirs(a.out, exist_ok=True)
    stem = Path(a.page).stem
    themes = ("light", "dark") if a.theme == "both" else (a.theme,)
    with tempfile.TemporaryDirectory() as profile:
        for theme in themes:
            url = page_url(a.page, theme)
            dom = run(chrome, profile, a.width, 900, "--dump-dom", url).stdout
            height = page_height(dom, a.height)
            shot = os.path.join(a.out, f"{stem}-{theme}.png")
            r = run(chrome, profile, a.width, height, f"--screenshot={shot}", url)
            if r.returncode or not os.path.isfile(shot):
                sys.exit(f"FAIL {theme}: {r.stderr.strip().splitlines()[-1:] or 'no screenshot'}")
            print(f"{shot}  {a.width}x{height}")


if __name__ == "__main__":
    main()
