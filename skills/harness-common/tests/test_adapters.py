"""claude_code.py and opencode.py: install paths and agent rendering."""
import json, sys, unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
