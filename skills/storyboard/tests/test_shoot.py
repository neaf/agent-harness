import io, os, platform, re, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
SKELETON = SKILL / "references" / "skeleton.html"
sys.path.insert(0, str(SKILL / "scripts"))
import shoot  # noqa: E402
from shoot import find_chrome, page_height, page_url  # noqa: E402

ARCH = "arm64" if platform.machine() == "arm64" else "x64"
OTHER_ARCH = "x64" if ARCH == "arm64" else "arm64"


def executable(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n")
    os.chmod(path, 0o755)
    return str(path)


def playwright_shell(cache, build, arch=ARCH):
    return executable(Path(cache, f"chromium_headless_shell-{build}", f"chrome-headless-shell-mac-{arch}",
                           "chrome-headless-shell"))


class FakeChrome:
    """Stands in for subprocess.run: a --dump-dom pass returns `dom`, a screenshot pass writes the file."""

    def __init__(self, dom='<html lang="en" data-h="3048"><head>', dump_code=0, dump_err="", shot_code=0,
                 shot_err="", error=None):
        self.dom, self.dump_code, self.dump_err = dom, dump_code, dump_err
        self.shot_code, self.shot_err, self.error = shot_code, shot_err, error
        self.calls = []

    def __call__(self, cmd, **options):
        self.calls.append(cmd)
        if self.error:
            raise self.error
        if "--dump-dom" in cmd:
            return subprocess.CompletedProcess(cmd, self.dump_code, self.dom if not self.dump_code else "", self.dump_err)
        shot = next(arg for arg in cmd if arg.startswith("--screenshot="))[len("--screenshot="):]
        if not self.shot_code:
            Path(shot).write_bytes(b"\x89PNG")
        return subprocess.CompletedProcess(cmd, self.shot_code, "", self.shot_err)


class ShootTest(unittest.TestCase):
    def test_height_from_data_h(self):
        self.assertEqual(page_height('<html lang="en" data-theme="dark" data-h="3048"><head>', 6000), 3048)

    def test_height_fallback(self):
        self.assertEqual(page_height("<html><head>", 6000), 6000)

    def test_url_has_theme(self):
        url = page_url("/tmp/x/topic-storyboard.html", "dark")
        self.assertTrue(url.startswith("file:///"))
        self.assertTrue(url.endswith("topic-storyboard.html?theme=dark"))

    def test_chrome_from_env(self):
        with tempfile.TemporaryDirectory() as folder:
            chrome = executable(Path(folder, "chrome"))
            self.assertEqual(find_chrome({"CHROME": chrome}), chrome)

    def test_FR_SB_10_chrome_from_env_must_be_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            plain = Path(folder, "chrome")
            plain.write_text("")
            for chrome in ("/nonexistent/chrome", str(plain), folder):
                with self.subTest(chrome=chrome), self.assertRaisesRegex(shoot.Fail, "not an executable file"):
                    find_chrome({"CHROME": chrome})

    def test_newest_playwright_shell(self):
        with tempfile.TemporaryDirectory() as home:
            cache = Path(home, "Library/Caches/ms-playwright")
            playwright_shell(cache, 998)
            newest = playwright_shell(cache, 1248)
            playwright_shell(cache, 1100)
            self.assertEqual(find_chrome({"PATH": ""}, home=home), newest)

    def test_FR_SB_10_non_executable_shells_are_skipped(self):
        with tempfile.TemporaryDirectory() as home:
            cache = Path(home, "Library/Caches/ms-playwright")
            working = playwright_shell(cache, 1100)
            broken = Path(playwright_shell(cache, 1248))
            os.chmod(broken, 0o644)
            self.assertEqual(find_chrome({"PATH": ""}, home=home), working)

    def test_never_a_browser_app(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as bin_dir:
            for name in ("google-chrome", "chromium"):
                exe = Path(bin_dir, name)
                exe.write_text("")
                os.chmod(exe, 0o755)
            self.assertIsNone(find_chrome({"PATH": bin_dir}, home=home))

    # Defects fixed in Phase 8.

    def test_FR_SB_10_playwright_browsers_path_is_honoured(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as cache:
            shell = playwright_shell(cache, 1248)
            self.assertEqual(find_chrome({"PATH": "", "PLAYWRIGHT_BROWSERS_PATH": cache}, home=home), shell)

    def test_FR_SB_10_host_architecture_shell_is_preferred(self):
        with tempfile.TemporaryDirectory() as home:
            cache = Path(home, "Library/Caches/ms-playwright")
            host = playwright_shell(cache, 1248)
            playwright_shell(cache, 1300, OTHER_ARCH)
            self.assertEqual(find_chrome({"PATH": ""}, home=home), host)


class MainTest(unittest.TestCase):
    """main() with subprocess.run replaced by FakeChrome, or by nothing where the test says so."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.chrome = executable(self.tmp / "bin" / "chrome-headless-shell")
        self.out = self.tmp / "shots"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def main(self, fake, *args, page=SKELETON, env=None):
        """Returns (exit code, stdout lines, stdout and stderr lines)."""
        out, err = io.StringIO(), io.StringIO()
        argv = ["shoot.py", str(page), "--out", str(self.out), *args]
        patches = [mock.patch.object(sys, "argv", argv),
                   mock.patch.dict(os.environ, env if env is not None else {"CHROME": self.chrome})]
        if fake:
            patches.append(mock.patch.object(shoot.subprocess, "run", fake))
        code = 0
        with redirect_stdout(out), redirect_stderr(err):
            for patch in patches:
                patch.start()
            try:
                shoot.main()
            except SystemExit as stop:
                code = stop.code if isinstance(stop.code, int) or stop.code is None else 1
                if isinstance(stop.code, str):
                    err.write(stop.code + "\n")
            finally:
                for patch in reversed(patches):
                    patch.stop()
        return code or 0, out.getvalue().splitlines(), (out.getvalue() + err.getvalue()).splitlines()

    def assert_one_fail_line(self, code, lines):
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].startswith("FAIL "), lines)

    def test_one_line_per_theme_at_the_data_h_height(self):
        fake = FakeChrome()
        code, stdout, _ = self.main(fake)
        self.assertEqual(code, 0)
        self.assertEqual(stdout, [f"{self.out / 'skeleton-light.png'}  1440x3048",
                                  f"{self.out / 'skeleton-dark.png'}  1440x3048"])
        dumps = [cmd for cmd in fake.calls if "--dump-dom" in cmd]
        self.assertEqual(len(dumps), 2)
        self.assertTrue(all("--window-size=1440,900" in cmd for cmd in dumps))
        self.assertTrue(all(cmd[0] == self.chrome for cmd in fake.calls))
        self.assertTrue(fake.calls[0][-1].endswith("skeleton.html?theme=light"))

    def test_one_theme_and_width(self):
        code, stdout, _ = self.main(FakeChrome(), "--theme", "dark", "--width", "800")
        self.assertEqual((code, stdout), (0, [f"{self.out / 'skeleton-dark.png'}  800x3048"]))

    def test_a_dump_without_data_h_uses_the_height_option(self):
        code, stdout, _ = self.main(FakeChrome(dom="<html><head>"), "--theme", "light", "--height", "5000")
        self.assertEqual(code, 0)
        self.assertEqual(stdout, [f"{self.out / 'skeleton-light.png'}  1440x5000 (no data-h, used --height)"])

    def test_FR_SB_12_a_page_taller_than_the_limit_is_clipped(self):
        fake = FakeChrome(dom='<html data-h="250000"><head>')
        code, stdout, _ = self.main(fake, "--theme", "light")
        self.assertEqual(code, 0)
        self.assertEqual(stdout, [f"{self.out / 'skeleton-light.png'}  1440x200000 (clipped from 250000)"])
        self.assertIn("--window-size=1440,200000", fake.calls[-1])

    def test_a_failed_screenshot_without_stderr_names_the_cause(self):
        code, _, lines = self.main(FakeChrome(shot_code=1), "--theme", "light")
        self.assert_one_fail_line(code, lines)
        self.assertEqual(lines[0], "FAIL light: no screenshot")

    def test_a_missing_page_fails(self):
        code, _, lines = self.main(FakeChrome(), page=self.tmp / "missing.html")
        self.assert_one_fail_line(code, lines)
        self.assertIn("not found", lines[0])

    def test_no_shell_fails_with_the_install_hint(self):
        code, _, lines = self.main(FakeChrome(), env={"CHROME": "", "PATH": "", "HOME": str(self.tmp)})
        self.assert_one_fail_line(code, lines)
        self.assertIn("playwright install", lines[0])

    def test_FR_SB_11_chrome_timeout_gives_one_fail_line(self):
        code, _, lines = self.main(FakeChrome(error=subprocess.TimeoutExpired(["chrome"], 120)))
        self.assert_one_fail_line(code, lines)

    def test_FR_SB_10_non_executable_chrome_gives_a_fail_line(self):
        code, _, lines = self.main(None, env={"CHROME": str(self.tmp / "nonexistent")})
        self.assert_one_fail_line(code, lines)

    def test_FR_SB_11_failed_dump_is_reported(self):
        code, _, lines = self.main(FakeChrome(dump_code=1, dump_err="starting\ndump crashed\n"), "--theme", "light")
        self.assert_one_fail_line(code, lines)
        self.assertIn("dump crashed", lines[0])

    def test_FR_SB_11_fail_reason_is_plain_text(self):
        code, _, lines = self.main(FakeChrome(shot_code=1, shot_err="starting\nrenderer crashed\n"), "--theme", "light")
        self.assert_one_fail_line(code, lines)
        self.assertTrue(lines[0].endswith("renderer crashed"), lines)


class SkeletonTest(unittest.TestCase):
    def setUp(self):
        self.html = SKELETON.read_text()

    def test_FR_SB_08_os_reduced_motion_stops_every_animation(self):
        rules = []
        for start in [m.end() for m in re.finditer(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{", self.html)]:
            depth, end = 1, start
            while depth:
                depth += {"{": 1, "}": -1}.get(self.html[end], 0)
                end += 1
            rules += re.findall(r"([^{}]+)\{([^{}]*)\}", self.html[start:end - 1])
        self.assertTrue(rules)
        self.assertTrue(any(any(sel.strip().startswith("*") for sel in selectors.split(","))
                            and re.search(r"animation(-name)?\s*:\s*none", body)
                            for selectors, body in rules), rules)

    def test_FR_SB_05_keyboard_section_is_named_keyboard_path(self):
        self.assertNotIn("Keyboard only", self.html)
        self.assertRegex(self.html, r'<a href="#keys">Keyboard path</a>')
        self.assertRegex(self.html, r"<h2[^>]*>Keyboard path</h2>")


class RealShellTest(unittest.TestCase):
    """The skeleton through the real headless shell. Skipped when none is installed (SB-Q11)."""

    def test_skeleton_renders_in_both_themes(self):
        if not find_chrome():
            self.skipTest("no chrome-headless-shell found")
        with tempfile.TemporaryDirectory() as out:
            done = subprocess.run([sys.executable, "-I", str(SKILL / "scripts" / "shoot.py"), str(SKELETON), "--out", out],
                                  capture_output=True, text=True, timeout=600)
            self.assertEqual(done.returncode, 0, done.stderr)
            lines = done.stdout.splitlines()
            self.assertEqual(len(lines), 2, lines)
            for line, theme in zip(lines, ("light", "dark")):
                match = re.fullmatch(r"(.+\.png)  1440x(\d+)", line)
                self.assertTrue(match, line)
                self.assertTrue(match.group(1).endswith(f"skeleton-{theme}.png"))
                self.assertGreater(int(match.group(2)), 900)
                self.assertEqual(Path(match.group(1)).read_bytes()[:4], b"\x89PNG")


if __name__ == "__main__":
    unittest.main()
