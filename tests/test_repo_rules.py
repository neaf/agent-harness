"""Rules over the whole repository: no model names, ignored caches, well-formed skills and agents."""
import codecs, re, subprocess, sys, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"
sys.path.insert(0, str(REPO))
import install  # noqa: E402  (one frontmatter parser: install.py's)

# Model names, families and id prefixes, ROT13-encoded so this file holds none (FR-AGT-08).
WORDS = ["fbaarg", "bchf", "unvxh", "qrrcfrrx", "trzvav", "yynzn", "zvfgeny", "djra", "xvzv"]
PREFIXES = ["tcg", "pynhqr"]  # followed by a version number
MODEL_NAME = re.compile(
    r"\b(?:" + "|".join(codecs.decode(w, "rot13") for w in WORDS) + r")\b"
    + r"|\b(?:" + "|".join(codecs.decode(p, "rot13") for p in PREFIXES) + r")-?\d",
    re.IGNORECASE,
)
# Run state records the model mapping the user confirmed (FR-AGT-07), so it is not scanned.
RUN_STATE = (".rearch/", ".attack-plan/", ".ai-notes/")
# Files that still name models. Phase 10 empties the set.
ALLOWED = {"skills/rearchitect/SKILL.md"}


def tracked_files():
    done = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, text=True)
    if done.returncode:
        raise unittest.SkipTest("not a git checkout")
    return [name for name in done.stdout.split("\0") if name and (REPO / name).is_file()]


def frontmatter(text):
    return install.frontmatter(text)[0]


def check_agent(path):
    return install.parse_agent(path)[0]


class ModelNameTest(unittest.TestCase):
    def setUp(self):
        self.files = [f for f in tracked_files() if not f.startswith(RUN_STATE)]
        self.hits = {}
        for name in self.files:
            text = (REPO / name).read_bytes().decode("utf-8", errors="ignore")
            found = sorted({m.group(0) for m in MODEL_NAME.finditer(text)})
            if found:
                self.hits[name] = found

    def test_no_model_name_outside_the_allowlist(self):
        self.assertEqual({name: found for name, found in self.hits.items() if name not in ALLOWED}, {})

    def test_every_allowlisted_file_still_names_a_model(self):
        self.assertEqual(sorted(ALLOWED - set(self.hits)), [])

    def test_every_skill_folder_is_scanned(self):
        scanned = {name.split("/")[1] for name in self.files if name.startswith("skills/") and name.count("/") >= 2}
        folders = {d.name for d in (REPO / "skills").iterdir() if d.is_dir()}
        self.assertEqual(sorted(folders - scanned), [])
        self.assertIn("skills/storyboard/references/skeleton.html", self.files)

    def test_the_pattern_finds_names_and_ids(self):
        for text in (codecs.decode("zbqry: bchf", "rot13"), codecs.decode("qrrcfrrx/qrrcfrrx-synfu", "rot13"),
                     codecs.decode("pynhqr-3-5", "rot13"), codecs.decode("TCG-4b", "rot13")):
            self.assertRegex(text, MODEL_NAME)
        for text in ("Claude Code", "opencode", "magnum-opusculum", "ollama"):
            self.assertNotRegex(text, MODEL_NAME)


class RepoRulesTest(unittest.TestCase):
    def test_bytecode_caches_are_ignored(self):
        for path in ("skills/feedback-watch/scripts/__pycache__/watch.cpython-39.pyc", "tests/stray.pyc"):
            done = subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", path])
            self.assertEqual(done.returncode, 0, path)

    def test_every_skill_has_a_skill_md_named_after_its_folder(self):
        for folder in sorted(d for d in (REPO / "skills").iterdir() if d.is_dir()):
            with self.subTest(skill=folder.name):
                meta = frontmatter((folder / "SKILL.md").read_text())
                self.assertEqual(meta.get("name"), folder.name)
                self.assertTrue(meta.get("description"))

    def test_every_agent_parses(self):
        agents = sorted((REPO / "agents").glob("*.md"))
        self.assertTrue(agents)
        for path in agents:
            with self.subTest(agent=path.name):
                check_agent(path)

    def test_the_agent_check_rejects_the_bad_fixtures(self):
        for name, reason in (("bad-fence.md", "opening"), ("bad-tier.md", "tier")):
            with self.subTest(fixture=name), self.assertRaisesRegex(ValueError, reason):
                check_agent(FIXTURES / "agents" / name)


if __name__ == "__main__":
    unittest.main()
