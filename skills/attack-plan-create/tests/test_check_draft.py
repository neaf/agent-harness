import shutil, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_draft import CheckDraft, headings, section_text  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "markdown" / "fenced-headings.md"

QUESTIONS = """**Q1. Overdue tasks**
- **Context**
  - The widget counts tasks due this week.
- **Question:** **Count overdue tasks from earlier weeks?**
  - **Count them:** a red badge shows them.
  - **Leave them out:** only this week counts.
- **Recommendation:** **Count them**, the design shows a red badge.
"""
PRODUCT = "Users see the tasks of their clients.\n"
TECHNICAL = "1. Add the widget.\n"


def plan(product=PRODUCT, questions=QUESTIONS, technical=TECHNICAL):
    return (f"# 0. Summary\n- Goal: show tasks on the homepage.\n# 1. Product solution\n{product}"
            f"# 2. Open questions\n{questions}# 3. Technical solution\n{technical}"
            "# 4. Milestones and verification\n- M1: the week widget.\n# 5. Risks\n1. **Query cost**\n")


class CheckDraftTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.folder)

    def run_check(self, text, stage="full", **files):
        if text is not None:
            (self.folder / "attack-plan.md").write_text(text)
        for name, content in files.items():
            (self.folder / f"{name.replace('_', '-')}.md").write_text(content)
        return CheckDraft(self.folder, stage).run()

    def messages(self, results, level):
        return [message for lvl, _, message in results if lvl == level]

    def test_passes_a_well_formed_draft(self):
        self.assertEqual(self.run_check(plan()), [("PASS", "all", "no blocking issue")])

    def test_fails_without_an_attack_plan(self):
        self.assertEqual(self.messages(self.run_check(None), "FAIL"), ["missing"])

    def test_fails_when_open_questions_follow_the_technical_solution(self):
        text = f"# Summary\n# Product solution\n# Technical solution\n# Open questions\n{QUESTIONS}# Milestones\n# Risks\n"
        self.assertIn("Open questions must sit after Product solution and before Technical solution",
                      self.messages(self.run_check(text), "FAIL"))

    def test_names_a_missing_section(self):
        text = "# Summary\n# Product solution\n# Open questions\n# Technical solution\n# Milestones\n"
        self.assertEqual(self.messages(self.run_check(text), "FAIL"), ["no risks section"])

    def test_fails_on_an_effort_estimate(self):
        failures = self.messages(self.run_check(plan(technical="1. Add it, about 3 engineer-days.\n")), "FAIL")
        self.assertEqual(failures, ['line 14: effort estimate "engineer-days"'])

    def test_does_not_take_a_product_rule_for_an_estimate(self):
        failures = self.messages(self.run_check(plan(product="Tasks due within 30 days show.\n")), "FAIL")
        self.assertEqual(failures, [])

    def test_warns_on_code_terms_in_the_product_solution(self):
        warnings = self.messages(self.run_check(plan(product="The `TasksController` endpoint filters.\n")), "WARN")
        self.assertIn("inline code in the product solution", warnings)
        self.assertIn('code term "endpoint" in the product solution', warnings)

    def test_fails_on_a_question_without_recommendation(self):
        questions = "**Q1. Overdue tasks**\n- **Context**\n  - One fact.\n- **Question:** **Count them?**\n"
        self.assertEqual(self.messages(self.run_check(plan(questions=questions)), "FAIL"), ["Q1 has no Recommendation"])

    def test_fails_when_questions_skip_a_number(self):
        questions = "".join(f"**Q{n}. Title**\n- **Context**\n- **Question:** **Q?**\n- **Recommendation:** **Yes**\n"
                            for n in (1, 3))
        self.assertEqual(self.messages(self.run_check(plan(questions=questions)), "FAIL"),
                         ["questions are not numbered 1 to 2 in order: 1, 3"])

    def test_warns_on_an_inline_cross_reference(self):
        warnings = self.messages(self.run_check(plan(technical="1. Add it, see 2.4 for the rules.\n")), "WARN")
        self.assertEqual(warnings, ['line 14: inline cross-reference "see 2.4"'])

    def test_fails_on_named_options(self):
        failures = self.messages(self.run_check(plan(technical="1. Option B: reuse the index query.\n")), "FAIL")
        self.assertEqual(failures, ['line 14: "Option A/B" belongs in the alternatives'])

    def test_ignores_code_blocks(self):
        text = plan(technical="```ruby\n# Risks of the query\nputs '`'\n```\n")
        self.assertEqual(self.run_check(text), [("PASS", "all", "no blocking issue")])

    def test_fails_on_a_decision_log(self):
        failures = self.messages(self.run_check(plan(), technical_solution="# Overview\n# Decision log\n"), "FAIL")
        self.assertEqual(failures, ["a decision log section"])

    def test_fails_on_an_estimate_column(self):
        failures = self.messages(self.run_check(plan(technical="| Milestone | Tasks | Estimate |\n")), "FAIL")
        self.assertEqual(failures, ["a task table has an estimate column"])

    def test_product_stage_passes_without_later_sections(self):
        text = f"# Summary\n- Goal.\n# Product solution\n{PRODUCT}# Open questions\n{QUESTIONS}"
        self.assertEqual(self.run_check(text, "product"), [("PASS", "all", "no blocking issue")])

    def test_product_stage_accepts_empty_later_headings(self):
        text = f"# Summary\n# Product solution\n{PRODUCT}# Open questions\n{QUESTIONS}# Technical solution\n# Milestones\n"
        self.assertEqual(self.messages(self.run_check(text, "product"), "FAIL"), [])

    def test_product_stage_fails_on_later_content(self):
        failures = self.messages(self.run_check(plan(), "product"), "FAIL")
        self.assertEqual(sorted(failures), [
            "the milestones section has content before the product solution is approved",
            "the technical section has content before the product solution is approved",
        ])

    def test_product_stage_fails_on_a_technical_page(self):
        text = f"# Summary\n# Product solution\n{PRODUCT}# Open questions\n{QUESTIONS}"
        failures = self.messages(self.run_check(text, "product", technical_solution="# Overview\n"), "FAIL")
        self.assertEqual(failures, ["exists before the product solution is approved"])

    def test_fenced_lines_are_not_headings(self):
        text = FIXTURE.read_text()
        self.assertEqual([title for _, title, _ in headings(text)], ["product solution", "glossary", "setup", "week widget"])
        self.assertIn("After the seed, the list shows 3 tasks.", section_text(text, r"\bsetup\b"))


if __name__ == "__main__":
    unittest.main()
