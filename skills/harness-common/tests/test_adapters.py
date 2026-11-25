"""claude_code.py and opencode.py: install paths, agent rendering, model listing and tier overrides."""
import io, json, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import claude_code, opencode  # noqa: E402

META = {"name": "a", "description": 'Audits one aspect: reads "files"', "tier": "fast",
        "tools": ["Read", "Grep", "Glob", "Bash", "Write"]}
PREAMBLE = "Preamble line.\n"
BODY = "Role text.\n"


def head(text):
    """Frontmatter lines between the fences."""
    lines = text.split("\n")
    return lines[1:lines.index("---", 1)]


class ClaudeCodeTest(unittest.TestCase):
    def test_paths(self):
        p = claude_code.paths("/h")
        self.assertEqual((p["agents"], p["skills"], p["instructions"]),
                         (Path("/h/.claude/agents"), Path("/h/.claude/skills"), Path("/h/.claude/CLAUDE.md")))

    def test_render_quotes_description_keeps_tools_and_writes_no_model(self):
        text = claude_code.render_agent(META, BODY, PREAMBLE)
        self.assertEqual(head(text), ["name: a", f"description: {json.dumps(META['description'])}",
                                      "tools: Read, Grep, Glob, Bash, Write"])
        self.assertTrue(text.endswith("---\n\nPreamble line.\n\nRole text.\n"))
        self.assertNotIn("execute", text)

    def test_quoted_description_reads_back(self):
        line = head(claude_code.render_agent(META, BODY, PREAMBLE))[1]
        self.assertEqual(json.loads(line[len("description: "):]), META["description"])


class OpencodeTest(unittest.TestCase):
    def test_paths(self):
        p = opencode.paths("/h")
        self.assertEqual((p["agents"], p["skills"], p["instructions"]),
                         (Path("/h/.config/opencode/agents"), Path("/h/.config/opencode/skills"),
                          Path("/h/.config/opencode/AGENTS.md")))

    def test_every_claude_tool_has_an_action(self):
        self.assertEqual(set(opencode.ACTIONS), set(claude_code.TOOLS))

    def test_permissions_deny_unlisted_actions_and_the_spawn(self):
        rules = opencode.permissions(META["tools"])
        self.assertEqual([r["action"] for r in rules], ["skill", "webfetch", "websearch", "subagent"])
        self.assertTrue(all(r == {"action": r["action"], "resource": "*", "effect": "deny"} for r in rules))

    def test_all_tools_leave_only_the_spawn_denied(self):
        self.assertEqual(opencode.permissions(list(claude_code.TOOLS)),
                         [{"action": "subagent", "resource": "*", "effect": "deny"}])

    def test_unknown_tool_raises(self):
        with self.assertRaisesRegex(ValueError, "Agent"):
            opencode.permissions(["Read", "Agent"])

    def test_render_is_v2_with_sandbox_line_and_no_model(self):
        text = opencode.render_agent(META, BODY, PREAMBLE)
        lines = head(text)
        self.assertEqual(lines[:3], [f"description: {json.dumps(META['description'])}", "mode: subagent",
                                     "permissions:"])
        self.assertEqual(lines[-1], '  - {action: subagent, resource: "*", effect: deny}')
        top = {l.split(":")[0] for l in lines if not l.startswith(" ")}
        self.assertEqual(top, {"description", "mode", "permissions"})
        self.assertTrue(text.endswith(f"---\n\nPreamble line.\n\n{opencode.SANDBOX_LINE}\n\nRole text.\n"))

    def test_render_with_a_model_puts_it_after_mode(self):
        lines = head(opencode.render_agent(META, BODY, PREAMBLE, "prov/m"))
        self.assertEqual(lines[1:4], ["mode: subagent", 'model: "prov/m"', "permissions:"])


STATE = """# State

## Models for this run

Confirmed by the user on 2026-11-25 in opencode.

| Tier | Agents | Model |
|---|---|---|
| fast | reader | `prov/cheap` |
| default | phase | prov/mid |
| strong | critic | Big (`prov/big#high`) |

## Next
"""


class Runner:
    """Stands in for the opencode CLI: records calls, returns `out` or raises `fail`."""
    def __init__(self, out="", fail=None):
        self.calls, self.out, self.fail = [], out, fail

    def __call__(self, args, cwd=None, timeout=60):
        self.calls.append(args)
        if self.fail:
            raise opencode.Failed(self.fail)
        return self.out


def cli(*args, runner):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = opencode.main(list(args), runner=runner)
    return code, out.getvalue().splitlines(), err.getvalue()


class ModelsTest(unittest.TestCase):
    def test_models_prints_one_id_per_line(self):
        code, out, _ = cli("models", runner=Runner("prov/a\n\n  prov/b\n"))
        self.assertEqual((code, out), (0, ["prov/a", "prov/b"]))

    def test_missing_opencode_is_one_line_and_exit_1(self):
        with mock.patch.object(opencode.shutil, "which", return_value=None):
            code, out, err = cli("models", runner=opencode.run)
        self.assertEqual((code, out, err), (1, [], "opencode.py: opencode not found on PATH\n"))

    def test_empty_list_fails(self):
        self.assertEqual(cli("models", runner=Runner(""))[0], 1)

    def test_a_failing_cli_names_its_last_stderr_line(self):
        done = subprocess.CompletedProcess([], 2, "", "warn\nno providers\n")
        with mock.patch.object(opencode.shutil, "which", return_value="/x/opencode"), \
                mock.patch.object(opencode.subprocess, "run", return_value=done):
            with self.assertRaisesRegex(opencode.Failed, "^opencode models failed: no providers$"):
                opencode.list_models()


class TierTableTest(unittest.TestCase):
    TIERS = ("fast", "default", "strong")

    def test_reads_tier_and_model_columns(self):
        self.assertEqual(opencode.tier_models(STATE, self.TIERS),
                         {"fast": "prov/cheap", "default": "prov/mid", "strong": "prov/big#high"})

    def test_bad_tables_name_the_problem(self):
        table = "## Models for this run\n\n| Tier | Model |\n|---|---|\n"
        for text, reason in (("# x\n", "heading"), (table, "no rows"),
                             (table + "| fast | an alias |\n", "provider/model"),
                             (table + "| quick | `p/m` |\n", "unknown tier"),
                             (table + "| fast | `p/m` |\n| fast | `p/n` |\n", "twice"),
                             ("## Models for this run\n\n| Tier | Name |\n|---|---|\n| fast | p/m |\n", "column")):
            with self.subTest(reason=reason), self.assertRaisesRegex(opencode.Failed, reason):
                opencode.tier_models(text, self.TIERS)


class TierOverridesTest(unittest.TestCase):
    """apply-tiers and clear-tiers in a throwaway git repository."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.project = self.tmp / "project"
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        self.exclude = self.project / ".git" / "info" / "exclude"
        self.exclude.parent.mkdir(parents=True, exist_ok=True)
        self.exclude.write_text("own-line\n")
        self.state = self.tmp / "STATE.md"
        self.state.write_text(STATE)
        self.agents = self.project / ".opencode" / "agents"
        self.names = sorted(p.name for p in (opencode.CHECKOUT / "agents").glob("*.md")) + ["general.md"]

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def apply(self, *extra, runner=None):
        return cli("apply-tiers", "--state", str(self.state), "--project", str(self.project), *extra,
                   runner=runner or Runner())

    def test_apply_writes_every_agent_and_general_with_its_tier_model(self):
        runner = Runner()
        code, out, _ = self.apply("--general", "strong", runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in self.agents.iterdir()), sorted(self.names))
        sources = {p.stem: opencode.CHECKOUT / "agents" / p.name for p in (opencode.CHECKOUT / "agents").glob("*.md")}
        models = opencode.tier_models(STATE, ("fast", "default", "strong"))
        for name, src in sources.items():
            tier = next(l for l in src.read_text().splitlines() if l.startswith("tier: "))[6:]
            self.assertIn(f"model: {json.dumps(models[tier])}", head((self.agents / f"{name}.md").read_text()))
        general = (self.agents / "general.md").read_text()
        self.assertIn('model: "prov/big#high"', head(general))
        self.assertIn('  - {action: subagent, resource: "*", effect: deny}', head(general))
        self.assertIn(opencode.SANDBOX_LINE, general)
        self.assertEqual(runner.calls, [["reload"]])
        self.assertEqual(out[-1], "reloaded")
        text = self.exclude.read_text()
        self.assertTrue(text.startswith("own-line\n"))
        for name in self.names:
            self.assertIn(f"/.opencode/agents/{name}\n", text)

    def test_overrides_match_the_installed_agent_plus_the_model_line(self):
        self.apply()
        installed = (opencode.CHECKOUT / "agents" / "rearch-phase.md")
        sys.path.insert(0, str(opencode.CHECKOUT))
        import install
        meta, body = install.parse_agent(installed)
        preamble = (opencode.CHECKOUT / "skills" / "harness-common" / "references" / "preamble.md").read_text()
        plain = opencode.render_agent(meta, body, preamble).split("\n")
        written = (self.agents / "rearch-phase.md").read_text().split("\n")
        self.assertEqual([l for l in written if not l.startswith("model: ")], plain)

    def test_rerun_replaces_its_own_files_and_keeps_one_block(self):
        self.apply()
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.exclude.read_text().count(opencode.BEGIN), 1)

    def test_a_foreign_override_is_refused_before_any_write(self):
        self.agents.mkdir(parents=True)
        (self.agents / "general.md").write_text("mine\n")
        code, _, err = self.apply()
        self.assertEqual(code, 1)
        self.assertIn("not written by apply-tiers", err)
        self.assertEqual(sorted(p.name for p in self.agents.iterdir()), ["general.md"])
        self.assertEqual(self.exclude.read_text(), "own-line\n")

    def test_failed_reload_keeps_the_files_and_exits_1(self):
        code, out, _ = self.apply(runner=Runner(fail="opencode not found on PATH"))
        self.assertEqual(code, 1)
        self.assertTrue(out[-1].startswith("reload failed: opencode not found on PATH. Restart opencode"))
        self.assertTrue((self.agents / "general.md").is_file())

    def test_clear_removes_only_its_files_and_its_block(self):
        self.apply()
        (self.agents / "mine.md").write_text("mine\n")
        runner = Runner()
        code, out, _ = cli("clear-tiers", "--project", str(self.project), runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual([p.name for p in self.agents.iterdir()], ["mine.md"])
        self.assertEqual(self.exclude.read_text(), "own-line\n")
        self.assertEqual(runner.calls, [["reload"]])

    def test_clear_removes_the_empty_folders(self):
        self.apply()
        cli("clear-tiers", "--project", str(self.project), runner=Runner())
        self.assertFalse((self.project / ".opencode").exists())

    def test_clear_without_overrides_runs_nothing(self):
        runner = Runner()
        code, out, _ = cli("clear-tiers", "--project", str(self.project), runner=runner)
        self.assertEqual((code, out, runner.calls), (0, ["no tier overrides"], []))

    def test_outside_git_fails(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        code, _, err = cli("clear-tiers", "--project", str(plain), runner=Runner())
        self.assertEqual(code, 1)
        self.assertIn("not a git repository", err)


if __name__ == "__main__":
    unittest.main()
