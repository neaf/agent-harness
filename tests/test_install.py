"""install.py against a throwaway home. Never touches the real ~/.claude or ~/.config."""
import io, shutil, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"
sys.path.insert(0, str(REPO))
import install  # noqa: E402


class Tty(io.StringIO):
    def isatty(self):
        return True


def source_meta(path):
    """Frontmatter of a source agent file as written, without install.py's parser."""
    head = path.read_text().split("---\n")[1]
    return dict(line.split(": ", 1) for line in head.strip().splitlines())


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.claude = self.home / ".claude"
        self.opencode = self.home / ".config" / "opencode"

    def tearDown(self):
        shutil.rmtree(self.home)

    def install(self, *args, stdin=None, answer=None):
        out, err = io.StringIO(), io.StringIO()
        prompt = mock.patch("builtins.input", side_effect=EOFError if answer is None else [answer])
        with redirect_stdout(out), redirect_stderr(err), prompt, \
                mock.patch.object(sys, "stdin", stdin or io.StringIO()):
            code = install.main(["--claude", "1", "--opencode", "1", *args], home=self.home)
        return code, out.getvalue().splitlines(), err.getvalue()

    def planned_count(self, root=REPO):
        agents = len(list((root / "agents").glob("*.md")))
        skills = len([d for d in (root / "skills").iterdir() if d.is_dir()])
        return 2 * agents + 2 + 2 * skills

    def fake_root(self, agents=()):
        """A minimal harness checkout: the given agent files, global.md, the models map, one skill."""
        root = self.home / "checkout"
        (root / "agents").mkdir(parents=True)
        for path in agents:
            shutil.copy(path, root / "agents" / Path(path).name)
        (root / "instructions").mkdir()
        (root / "instructions" / "global.md").write_text("# Global\n")
        (root / "targets").mkdir()
        shutil.copy(REPO / "targets" / "models.json", root / "targets" / "models.json")
        (root / "skills" / "one").mkdir(parents=True)
        (root / "skills" / "one" / "SKILL.md").write_text("---\nname: one\ndescription: A skill.\n---\n")
        return root

    def test_empty_home_plans_every_item_and_writes_nothing(self):
        code, lines, _ = self.install("--check")
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], f"{self.planned_count()} change(s) needed")
        self.assertTrue(all(line.startswith("create") for line in lines[:-1]))
        self.assertEqual(len(lines) - 1, self.planned_count())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_install_then_second_run_is_a_no_op(self):
        code, lines, _ = self.install()
        self.assertEqual((code, lines[-1]), (0, f"{self.planned_count()} change(s) applied"))
        self.assertTrue((self.claude / "skills" / "ai-notes").is_symlink())
        self.assertEqual((self.opencode / "AGENTS.md").read_text(), (REPO / "instructions" / "global.md").read_text())
        self.assertEqual(self.install("--check")[:2], (0, ["0 change(s) needed"]))
        self.assertEqual(self.install()[:2], (0, ["0 change(s) applied"]))

    def test_check_exits_1_on_drift_and_names_the_item(self):
        self.install()
        (self.claude / "CLAUDE.md").write_text("mine\n")
        code, lines, _ = self.install("--check")
        self.assertEqual(code, 1)
        self.assertEqual(lines, [f"replace {self.claude / 'CLAUDE.md'}", "1 change(s) needed"])
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), "mine\n")

    def test_declined_prompt_changes_nothing(self):
        self.install()
        (self.claude / "CLAUDE.md").write_text("mine\n")
        code, lines, _ = self.install(stdin=Tty(), answer="n")
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "Nothing changed.")
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), "mine\n")

    def test_no_tty_without_yes_exits_2_and_changes_nothing(self):
        self.install()
        (self.claude / "CLAUDE.md").write_text("mine\n")
        code, _, err = self.install()
        self.assertEqual(code, 2)
        self.assertIn("Rerun with --yes", err)
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), "mine\n")

    def test_yes_replaces_without_asking(self):
        self.install()
        (self.claude / "CLAUDE.md").write_text("mine\n")
        self.assertEqual(self.install("--yes")[0], 0)
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), (REPO / "instructions" / "global.md").read_text())

    def test_claude_0_leaves_claude_out(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = install.main(["--check", "--claude", "0", "--opencode", "1"], home=self.home)
        self.assertEqual(code, 1)
        self.assertFalse(any(str(self.claude) in line for line in out.getvalue().splitlines()))
        self.assertTrue(any(str(self.opencode) in line for line in out.getvalue().splitlines()))

    def test_a_link_to_elsewhere_is_replaced(self):
        self.install()
        other = self.home / "other-skill"
        other.mkdir()
        link = self.claude / "skills" / "ai-notes"
        link.unlink()
        link.symlink_to(other)
        code, lines, _ = self.install("--check")
        self.assertEqual(lines, [f"replace {link} -> {REPO / 'skills' / 'ai-notes'}", "1 change(s) needed"])
        self.assertEqual(self.install("--yes")[0], 0)
        self.assertEqual(link.resolve(), (REPO / "skills" / "ai-notes").resolve())
        self.assertTrue(other.is_dir())

    # Known defects. Phase 3 fixes each and removes its marker.

    @unittest.expectedFailure
    def test_FR_INST_11_description_with_colon_is_quoted(self):
        self.install()
        colon = [f for f in sorted((REPO / "agents").glob("*.md")) if ": " in source_meta(f)["description"]]
        self.assertTrue(colon)
        for f in colon:
            for rendered in (self.claude / "agents" / f.name, self.opencode / "agents" / f.name):
                line = next(l for l in rendered.read_text().splitlines() if l.startswith("description: "))
                self.assertIn(line[len("description: "):][:1], ('"', "'"), rendered)

    @unittest.expectedFailure
    def test_FR_INST_09_removed_agent_is_pruned(self):
        root = self.fake_root([REPO / "agents" / "rearch-phase.md", REPO / "agents" / "rearch-auditor.md"])
        with mock.patch.object(install, "ROOT", root):
            self.install()
            (root / "agents" / "rearch-auditor.md").unlink()
            code, lines, _ = self.install("--check")
        self.assertEqual(code, 1)
        self.assertTrue(any(str(self.claude / "agents" / "rearch-auditor.md") in line for line in lines), lines)

    @unittest.expectedFailure
    def test_FR_INST_12_symlinked_destination_is_not_written_through(self):
        outside = self.home / "outside.md"
        outside.write_text("mine\n")
        self.claude.mkdir()
        (self.claude / "CLAUDE.md").symlink_to(outside)
        self.assertEqual(self.install("--yes")[0], 0)
        self.assertEqual(outside.read_text(), "mine\n")
        self.assertFalse((self.claude / "CLAUDE.md").is_symlink())

    @unittest.expectedFailure
    def test_FR_INST_10_bad_agent_file_is_named(self):
        for name in ("bad-fence.md", "bad-tier.md"):
            root = self.fake_root([FIXTURES / "agents" / name])
            with mock.patch.object(install, "ROOT", root):
                code, lines, err = self.install("--check")
            shutil.rmtree(root)
            self.assertNotIn(code, (0, 1))
            self.assertIn(name, err + "\n".join(lines))

    @unittest.expectedFailure
    def test_FR_INST_08_declined_exit_differs_from_drift(self):
        self.install()
        (self.claude / "CLAUDE.md").write_text("mine\n")
        drift = self.install("--check")[0]
        declined = self.install(stdin=Tty(), answer="n")[0]
        self.assertEqual(drift, 1)
        self.assertNotEqual(declined, drift)


if __name__ == "__main__":
    unittest.main()
