"""install.py against a throwaway home. Never touches the real ~/.claude or ~/.config."""
import io, shutil, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"
PREAMBLE = REPO / "skills" / "harness-common" / "references" / "preamble.md"
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
        """Agents, the instructions file, skill links and the manifest, on both hosts."""
        agents = len(list((root / "agents").glob("*.md")))
        skills = len([d for d in (root / "skills").iterdir() if d.is_dir()])
        return 2 * (agents + 1 + skills + 1)

    def fake_root(self, agents=()):
        """A minimal harness checkout: the given agent files, global.md, the preamble, one skill."""
        root = self.home / "checkout"
        (root / "agents").mkdir(parents=True)
        for path in agents:
            shutil.copy(path, root / "agents" / Path(path).name)
        (root / "instructions").mkdir()
        (root / "instructions" / "global.md").write_text("# Global\n")
        (root / "skills" / "harness-common" / "references").mkdir(parents=True)
        shutil.copy(PREAMBLE, root / "skills" / "harness-common" / "references" / "preamble.md")
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
        self.assertEqual(code, 3)  # distinct from drift (FR-INST-08)
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

    # Defects fixed in Phase 3. Each test name carries its requirement ID.

    def test_FR_INST_11_description_with_colon_is_quoted(self):
        self.install()
        colon = [f for f in sorted((REPO / "agents").glob("*.md")) if ": " in source_meta(f)["description"]]
        self.assertTrue(colon)
        for f in colon:
            for rendered in (self.claude / "agents" / f.name, self.opencode / "agents" / f.name):
                line = next(l for l in rendered.read_text().splitlines() if l.startswith("description: "))
                self.assertIn(line[len("description: "):][:1], ('"', "'"), rendered)

    def test_FR_INST_09_removed_agent_is_pruned(self):
        root = self.fake_root([REPO / "agents" / "rearch-phase.md", REPO / "agents" / "rearch-auditor.md"])
        with mock.patch.object(install, "ROOT", root):
            self.install()
            (root / "agents" / "rearch-auditor.md").unlink()
            code, lines, _ = self.install("--check")
        self.assertEqual(code, 1)
        self.assertTrue(any(str(self.claude / "agents" / "rearch-auditor.md") in line for line in lines), lines)

    def test_FR_INST_12_symlinked_destination_is_not_written_through(self):
        outside = self.home / "outside.md"
        outside.write_text("mine\n")
        self.claude.mkdir()
        (self.claude / "CLAUDE.md").symlink_to(outside)
        self.assertEqual(self.install("--yes")[0], 0)
        self.assertEqual(outside.read_text(), "mine\n")
        self.assertFalse((self.claude / "CLAUDE.md").is_symlink())

    def test_FR_INST_10_bad_agent_file_is_named(self):
        for name in ("bad-fence.md", "bad-tier.md"):
            root = self.fake_root([FIXTURES / "agents" / name])
            with mock.patch.object(install, "ROOT", root):
                code, lines, err = self.install("--check")
            shutil.rmtree(root)
            self.assertNotIn(code, (0, 1))
            self.assertIn(name, err + "\n".join(lines))

    def test_FR_INST_08_declined_exit_differs_from_drift(self):
        self.install()
        (self.claude / "CLAUDE.md").write_text("mine\n")
        drift = self.install("--check")[0]
        declined = self.install(stdin=Tty(), answer="n")[0]
        self.assertEqual(drift, 1)
        self.assertNotEqual(declined, drift)

    def test_FR_AGT_02_no_model_line_on_either_host(self):
        self.install()
        for folder in (self.claude / "agents", self.opencode / "agents"):
            for rendered in folder.glob("*.md"):
                head = rendered.read_text().split("---\n")[1]
                self.assertFalse(any(l.startswith("model") for l in head.splitlines()), rendered)

    def test_FR_AGT_06_preamble_once_and_sandbox_line_on_opencode_only(self):
        self.install()
        style = PREAMBLE.read_text().splitlines()[0]
        for name in (f.name for f in (REPO / "agents").glob("*.md")):
            claude = (self.claude / "agents" / name).read_text()
            other = (self.opencode / "agents" / name).read_text()
            self.assertEqual((claude.count(style), other.count(style)), (1, 1), name)
            self.assertNotIn("`execute` sandbox", claude)
            self.assertIn("`execute` sandbox", other)

    def test_FR_AGT_04_opencode_gets_permissions_and_no_v1_keys(self):
        self.install()
        head = (self.opencode / "agents" / "rearch-auditor.md").read_text().split("---\n")[1].splitlines()
        keys = {l.split(":")[0] for l in head if not l.startswith(" ")}
        self.assertEqual(keys, {"description", "mode", "permissions"})
        self.assertIn('  - {action: subagent, resource: "*", effect: deny}', head)
        self.assertNotIn('  - {action: edit, resource: "*", effect: deny}', head)  # Write maps to edit

    def test_FR_INST_10_spawn_tool_and_missing_key_are_named(self):
        cases = {"tools: Read, Agent": "tools: Agent is a spawn tool", "tier: fast": "tier: missing"}
        for line, message in cases.items():
            with self.subTest(line=line):
                root = self.fake_root()
                text = (REPO / "agents" / "rearch-phase.md").read_text()
                if line.startswith("tools"):
                    text = text.replace("tools: Read, Grep, Glob, Bash, Write, Edit", line)
                else:
                    text = text.replace("tier: default\n", "")
                (root / "agents" / "rearch-phase.md").write_text(text)
                with mock.patch.object(install, "ROOT", root):
                    code, lines, err = self.install("--check")
                shutil.rmtree(root)
                self.assertEqual((code, lines), (4, []))
                self.assertIn(f"agents/rearch-phase.md: {message}", err)

    def test_FR_INST_14_missing_folder_is_named(self):
        root = self.fake_root()
        shutil.rmtree(root / "agents")
        with mock.patch.object(install, "ROOT", root):
            code, _, err = self.install("--check")
        self.assertEqual(code, 4)
        self.assertIn("agents/: missing folder", err)

    def test_FR_INST_09_manifest_lists_owned_items_and_removed_skill_link_is_pruned(self):
        root = self.fake_root()
        (root / "skills" / "two").mkdir()
        (root / "skills" / "two" / "SKILL.md").write_text("---\nname: two\ndescription: B.\n---\n")
        with mock.patch.object(install, "ROOT", root):
            self.install()
            manifest = install.json.loads((self.claude / install.MANIFEST).read_text())
            self.assertEqual(manifest["links"], ["skills/harness-common", "skills/one", "skills/two"])
            shutil.rmtree(root / "skills" / "two")
            code, lines, _ = self.install("--check")
            self.assertEqual(code, 1)
            self.assertIn(f"remove  {self.claude / 'skills' / 'two'}", lines)
            self.assertEqual(self.install("--yes")[0], 0)
            self.assertFalse((self.claude / "skills" / "two").is_symlink())
            self.assertEqual(self.install("--check")[:2], (0, ["0 change(s) needed"]))

    def test_FR_INST_09_dangling_link_into_checkout_is_pruned_other_links_stay(self):
        root = self.fake_root()
        skills = self.claude / "skills"
        skills.mkdir(parents=True)
        (skills / "gone").symlink_to(root / "skills" / "gone")
        elsewhere = self.home / "elsewhere"
        (skills / "theirs").symlink_to(elsewhere)  # dangling too, but not into the checkout
        with mock.patch.object(install, "ROOT", root):
            code, lines, _ = self.install("--check")
        self.assertIn(f"remove  {skills / 'gone'}", lines)
        self.assertFalse(any("theirs" in line for line in lines), lines)

    def test_FR_INST_13_real_skill_folder_moves_to_backup(self):
        folder = self.claude / "skills" / "ai-notes"
        folder.mkdir(parents=True)
        (folder / "mine.md").write_text("mine\n")
        with mock.patch.object(install.time, "strftime", return_value="20261125-120000"):
            code, lines, _ = self.install("--yes")
        backup = self.claude / install.BACKUP / "20261125-120000" / "skills" / "ai-notes"
        self.assertEqual(code, 0)
        self.assertIn(f"backup  {folder} -> {backup}", lines)
        self.assertEqual((backup / "mine.md").read_text(), "mine\n")
        self.assertEqual(folder.resolve(), (REPO / "skills" / "ai-notes").resolve())

    def test_FR_INST_12_folder_where_a_file_goes_moves_to_backup(self):
        (self.claude / "CLAUDE.md").mkdir(parents=True)
        code, lines, _ = self.install("--yes")
        self.assertEqual(code, 0)
        self.assertTrue(any(line.startswith(f"backup  {self.claude / 'CLAUDE.md'} -> ") for line in lines), lines)
        self.assertTrue((self.claude / "CLAUDE.md").is_file())


if __name__ == "__main__":
    unittest.main()
