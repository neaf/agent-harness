import os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from shoot import find_chrome, page_height, page_url  # noqa: E402


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
        self.assertEqual(find_chrome({"CHROME": "/opt/chrome"}), "/opt/chrome")

    def shell(self, home, build):
        d = Path(home, "Library/Caches/ms-playwright", f"chromium_headless_shell-{build}", "chrome-headless-shell-mac-arm64")
        d.mkdir(parents=True)
        (d / "chrome-headless-shell").write_text("")
        return str(d / "chrome-headless-shell")

    def test_newest_playwright_shell(self):
        with tempfile.TemporaryDirectory() as home:
            self.shell(home, 998)
            newest = self.shell(home, 1248)
            self.shell(home, 1100)
            self.assertEqual(find_chrome({"PATH": ""}, home=home), newest)

    def test_never_a_browser_app(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as bin_dir:
            for name in ("google-chrome", "chromium"):
                exe = Path(bin_dir, name)
                exe.write_text("")
                os.chmod(exe, 0o755)
            self.assertIsNone(find_chrome({"PATH": bin_dir}, home=home))


if __name__ == "__main__":
    unittest.main()
