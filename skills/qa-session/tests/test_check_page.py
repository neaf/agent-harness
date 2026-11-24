import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_page import scan  # noqa: E402

GOOD = """# QA session: Example (2026-01-05)

> Intro line.

## Known limits, not bugs

- Data store X is not fed in this test environment.

## Walk-through

### 1. The admin sets the baseline

As admin (`admin@example.com`):

Baseline: nothing changed yet.

- [x] The menu shows Reports.
- [ ] The Reports list shows 3 rows.

> **Why:** the seed creates 3 rows.

### 2. The member sees less

As member (`member@example.com`):

What changed: the member is not an admin.

- [ ] The menu hides Reports.

## Product questions

### Should members export?

- **A. No.** Currently in this test environment, scenario 2.
- **B. Yes.**

## Findings

| # | Scenario | What you saw | What was expected | Status |
|---|---|---|---|---|
"""


class CheckPageTest(unittest.TestCase):
    def rules(self, text):
        findings, counts = scan(text.splitlines())
        return [(level, message) for _, level, message in findings], counts

    def test_good_page_has_no_fail(self):
        findings, counts = self.rules(GOOD)
        self.assertEqual([f for f in findings if f[0] == "FAIL"], [])
        self.assertEqual(counts["scenarios"], 2)
        self.assertEqual(counts["checks"], 3)
        self.assertEqual(counts["ticked"], 1)
        self.assertEqual(counts["finding_rows"], 0)

    def test_internal_id_fails(self):
        findings, _ = self.rules(GOOD.replace("scenario 2.", "see R4 for this."))
        self.assertIn(("FAIL", "internal id 'R4': name the case instead"), findings)

    def test_placeholder_fails_but_html_tags_pass(self):
        findings, _ = self.rules(GOOD.replace("admin@example.com", "<user email>"))
        self.assertTrue(any(level == "FAIL" and "placeholder" in message for level, message in findings))
        findings, _ = self.rules(GOOD.replace("3 rows.", "3 rows.<br>"))
        self.assertFalse(any("placeholder" in message for _, message in findings))

    def test_emoji_fails(self):
        findings, _ = self.rules(GOOD.replace("Intro line.", "Intro line. \U0001F9EA"))
        self.assertIn(("FAIL", "emoji"), findings)

    def test_bare_today_warns(self):
        findings, _ = self.rules(GOOD.replace("Baseline: nothing changed yet.", "Baseline: nothing changed today."))
        self.assertIn(("WARN", "bare 'today': say 'on production' or 'in this test environment'"), findings)

    def test_check_before_as_line_fails(self):
        text = GOOD.replace("As admin (`admin@example.com`):\n\nBaseline: nothing changed yet.\n\n", "")
        findings, _ = self.rules(text)
        self.assertIn(("FAIL", "check before the 'As <user>:' line of its scenario"), findings)

    def test_scenario_numbers_must_be_in_order(self):
        findings, _ = self.rules(GOOD.replace("### 2. The member", "### 3. The member"))
        self.assertTrue(any("scenario numbers" in message for _, message in findings))

    def test_missing_findings_section_fails(self):
        findings, _ = self.rules(GOOD.split("## Findings")[0])
        self.assertIn(("FAIL", "no Findings section"), findings)

    def test_filled_findings_rows_are_counted(self):
        _, counts = self.rules(GOOD + "| 1 | 1. The admin sets the baseline | Menu empty | Reports | Open |\n")
        self.assertEqual(counts["finding_rows"], 1)


if __name__ == "__main__":
    unittest.main()
