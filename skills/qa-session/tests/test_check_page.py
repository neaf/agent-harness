import subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_page import scan  # noqa: E402

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_page.py"

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "markdown" / "fenced-headings.md"

GOOD = """# QA session: Example (2026-01-05)

One walk-through, admin first, then member.

<details>
<summary>Setup for the lead developer</summary>

- [ ] Environment: https://qa.example.com runs build abc1234.
- [ ] Data: `./seed.sh` ran. It printed:
  - Reports: 3, the seeded rows

</details>

## Scenarios

### 1. The admin sees the reports

As admin (`admin@example.com`):

Start: https://qa.example.com/home

Context: the seed creates 3 reports for the admin's team.

1. Open the menu.
   - [x] The menu shows Reports.
2. Select **Reports**.
   - [ ] The Reports list shows 3 rows.

### 2. The member sees less

As member (`member@example.com`):

Context: the member is not an admin.

1. Open the menu.
   - [ ] The menu hides Reports.

## Findings
"""


class CheckPageTest(unittest.TestCase):
    def rules(self, text):
        findings, counts = scan(text.splitlines())
        return [(level, message) for _, level, message in findings], counts

    def test_good_page_has_no_fail_and_no_warn(self):
        findings, counts = self.rules(GOOD)
        self.assertEqual(findings, [])
        self.assertEqual(counts, {"scenarios": 2, "checks": 5, "ticked": 1, "findings": 0})

    def test_internal_id_fails(self):
        findings, _ = self.rules(GOOD.replace("is not an admin.", "is not an admin, see R4."))
        self.assertIn(("FAIL", "internal id 'R4': name the case, or backtick an exact label"), findings)

    def test_placeholder_fails_but_html_tags_pass(self):
        findings, _ = self.rules(GOOD.replace("admin@example.com", "<user email>"))
        self.assertTrue(any(level == "FAIL" and "placeholder" in message for level, message in findings))
        self.assertIn("FAIL", [level for level, _ in self.on_line(GOOD.replace("Example", "[feature]"), "[feature]")])
        findings, _ = self.rules(GOOD.replace("3 rows.", "3 rows.<br>"))
        self.assertFalse(any("placeholder" in message for _, message in findings))

    def test_links_and_checkboxes_are_not_bracket_placeholders(self):
        findings, _ = self.rules(GOOD.replace("Select **Reports**.", "Select [Reports](https://qa.example.com/r)."))
        self.assertEqual(findings, [])

    def test_emoji_fails(self):
        findings, _ = self.rules(GOOD.replace("then member.", "then member. \U0001F9EA"))
        self.assertIn(("FAIL", "emoji"), findings)

    def test_unfinished_marker_fails(self):
        findings, _ = self.rules(GOOD.replace("is not an admin.", "is not an admin. TODO"))
        self.assertIn(("FAIL", "unfinished marker"), findings)

    def test_bare_today_and_now_warn(self):
        findings, _ = self.rules(GOOD.replace("is not an admin.", "is not an admin today, and now sees less."))
        self.assertIn(("WARN", "bare 'today': say 'on production' or 'in this test environment'"), findings)
        self.assertIn(("WARN", "bare 'now': say 'on production' or 'in this test environment'"), findings)

    def test_check_before_the_persona_line_fails(self):
        text = GOOD.replace("As admin (`admin@example.com`):\n\n", "")
        findings, _ = self.rules(text)
        self.assertIn(("FAIL", "first line of the scenario is not its persona line 'As <persona> (`<email>`):'"), findings)

    def test_persona_line_follows_the_template(self):
        for line in ("As expected, the admin starts.", "As admin:", "As admin (admin@example.com):"):
            with self.subTest(line=line):
                findings, _ = self.rules(GOOD.replace("As admin (`admin@example.com`):", line))
                self.assertTrue(any("persona line" in message for _, message in findings), findings)

    def test_scenario_numbers_must_be_in_order(self):
        findings, _ = self.rules(GOOD.replace("### 2. The member", "### 3. The member"))
        self.assertTrue(any("scenario numbers" in message for _, message in findings))

    def test_scenario_without_checks_warns(self):
        findings, _ = self.rules(GOOD.replace("   - [ ] The menu hides Reports.\n", ""))
        self.assertIn(("WARN", "scenario without checkboxes"), findings)

    def test_missing_collapsed_setup_fails(self):
        start, end = GOOD.index("<details>"), GOOD.index("</details>") + len("</details>")
        findings, _ = self.rules(GOOD[:start] + GOOD[end:])
        self.assertIn(("FAIL", "no collapsed setup: put it in a <details> block before the scenarios"), findings)

    def test_missing_findings_section_fails(self):
        findings, _ = self.rules(GOOD.split("## Findings")[0])
        self.assertIn(("FAIL", "no 'Findings' section"), findings)

    def test_findings_heading_matches_exactly(self):
        findings, _ = self.rules(GOOD.replace("## Findings", "## Findings from earlier sessions"))
        self.assertIn(("FAIL", "no 'Findings' section"), findings)

    def test_FR_QA_15_findings_with_a_table_or_text_fails_at_create(self):
        message = ("FAIL", "Findings is not empty: it starts empty, with no table (use --live during a session)")
        for extra in ("\n| # | Scenario | What you saw |\n|---|---|---|\n", "\nEmpty at the start.\n"):
            with self.subTest(extra=extra):
                findings, _ = self.rules(GOOD + extra)
                self.assertIn(message, findings)

    def test_live_session_counts_findings(self):
        text = GOOD + "\n- Scenario 1: the menu was empty.\n- Scenario 2: slow load.\n"
        findings, counts = scan(text.splitlines(), live=True)
        self.assertEqual(findings, [])
        self.assertEqual(counts["findings"], 2)

    def test_template_example_page_parses(self):
        """The template's own example is the shape check_page enforces: no structural FAIL once filled."""
        template = (Path(__file__).resolve().parent.parent / "references" / "page-template.md").read_text()
        page = template.split("````markdown\n", 1)[1].split("\n````", 1)[0]
        findings, counts = scan(page.splitlines())
        self.assertEqual(counts["scenarios"], 2)
        structural = [m for _, level, m in findings if level == "FAIL" and "placeholder" not in m]
        self.assertEqual(structural, [])

    def on_line(self, text, needle):
        """Findings on the first line that holds needle."""
        number = next(n for n, line in enumerate(text.splitlines(), 1) if needle in line)
        return [(level, message) for n, level, message in scan(text.splitlines())[0] if n == number]

    # Defects fixed in Phase 8.

    def test_FR_QA_09_backticked_label_is_not_an_internal_id(self):
        findings, _ = self.rules(GOOD.replace("The menu shows Reports.", "The menu shows `Q4 Budget` and `Today`."))
        self.assertEqual(findings, [])

    def test_FR_QA_09_bracketed_template_placeholder_fails(self):
        text = GOOD.replace("- [ ] The menu hides Reports.", "- [ ] [Next fact.]")
        self.assertIn("FAIL", [level for level, _ in self.on_line(text, "[Next fact.]")])

    def test_FR_QA_09_malformed_scenario_heading_is_flagged(self):
        text = GOOD.replace("### 2. The member", "### 2 The member")
        self.assertTrue(self.on_line(text, "### 2 The member"))

    def test_FR_XS_02_fenced_lines_are_not_headings_or_checks(self):
        text = FIXTURE.read_text()
        _, counts = self.rules(text)
        self.assertEqual(counts["checks"], 0)
        self.assertEqual(self.on_line(text, "# seeds three tasks"), [])


class MainTest(unittest.TestCase):
    def run_script(self, text, *args):
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder, "session.md")
            page.write_text(text)
            return subprocess.run([sys.executable, "-I", str(SCRIPT), str(page), *args],
                                  capture_output=True, text=True, timeout=60)

    def test_summary_line_and_exit_code(self):
        done = self.run_script(GOOD)
        self.assertEqual((done.returncode, done.stdout),
                         (0, "qa page: 2 scenarios, 5 checks, 1 ticked, 0 findings, 0 FAIL, 0 WARN\n"))
        done = self.run_script(GOOD + "- the menu was empty\n", "-v")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAIL line 39: Findings is not empty", done.stdout)
        self.assertEqual(self.run_script(GOOD + "- the menu was empty\n", "--live").returncode, 0)


if __name__ == "__main__":
    unittest.main()
