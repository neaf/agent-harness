import io, shutil, sys, tempfile, unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gate import Gate, Refused, main  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "markdown" / "fenced-headings.md"

PLAN = "# Product solution\n## Glossary\n- **Task:** a to-do.\n## Week widget\n- Shows 3 tasks.\n# Open questions\n"


class GateTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "draft").mkdir()
        self.write(PLAN)
        self.gate = Gate(self.folder)

    def tearDown(self):
        shutil.rmtree(self.folder)

    def write(self, text):
        (self.folder / "draft" / "attack-plan.md").write_text(text)

    def open_section(self, gate_id, heading):
        return self.gate.open("product", gate_id, file="draft/attack-plan.md", heading=heading)

    def pass_gate(self, gate_id, stage, heading=None):
        self.gate.open(stage, gate_id, file=heading and "draft/attack-plan.md", heading=heading)
        self.gate.grilled(gate_id, 1, 0)
        self.gate.approve(gate_id, "Author")

    def test_refuses_an_unknown_stage(self):
        with self.assertRaisesRegex(Refused, "unknown stage design"):
            self.gate.open("design", "overview")

    def test_refuses_the_next_section_while_the_previous_one_is_in_progress(self):
        self.open_section("glossary", "Glossary")
        with self.assertRaisesRegex(Refused, "skip them first: glossary"):
            self.gate.open("product", "week-widget")

    def test_refuses_the_technical_stage_before_the_product_review(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.gate.open("product-review", "ready-for-review")
        with self.assertRaisesRegex(Refused, "skip them first: ready-for-review"):
            self.gate.open("technical", "overview")

    def test_opens_the_technical_stage_once_earlier_gates_are_approved(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.pass_gate("ready-for-review", "product-review")
        self.assertEqual(self.gate.open("technical", "overview"), "opened overview (technical)")

    def test_refuses_to_reopen_an_approved_gate_silently(self):
        self.pass_gate("glossary", "product", "Glossary")
        with self.assertRaisesRegex(Refused, "is approved: reopen it first"):
            self.gate.open("product", "glossary")

    def test_grilled_needs_a_round_and_no_open_findings(self):
        self.open_section("glossary", "Glossary")
        with self.assertRaisesRegex(Refused, "challenge round"):
            self.gate.grilled("glossary", 0, 0)
        with self.assertRaisesRegex(Refused, "1 open findings"):
            self.gate.grilled("glossary", 2, 1)

    def test_approve_needs_grilling_a_name_and_the_section(self):
        self.open_section("glossary", "Glossary")
        with self.assertRaisesRegex(Refused, "must be grilled"):
            self.gate.approve("glossary", "Author")
        self.gate.grilled("glossary", 1, 0)
        with self.assertRaisesRegex(Refused, "--by"):
            self.gate.approve("glossary", " ")
        self.write("# Product solution\n")
        with self.assertRaisesRegex(Refused, 'section "Glossary" not found'):
            self.gate.approve("glossary", "Author")

    def test_reports_an_approved_section_edited_afterwards(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.pass_gate("week-widget", "product", "Week widget")
        self.write(PLAN.replace("3 tasks", "5 tasks"))
        self.assertEqual(self.gate.problems(), ["week-widget changed after its approval: reopen it"])

    def test_ignores_edits_to_other_sections(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.write(PLAN + "- Q1 added.\n")
        self.assertEqual(self.gate.problems(), [])

    def test_reopen_marks_later_approved_gates_stale(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.pass_gate("week-widget", "product", "Week widget")
        self.assertEqual(self.gate.reopen("glossary", "renamed a term"), "reopened glossary\nweek-widget is now stale")
        self.assertEqual(self.gate.problems(), ["week-widget is stale: re-review it"])
        self.gate.grilled("glossary", 1, 0)
        self.gate.approve("glossary", "Author")
        self.assertEqual(self.gate.open("product", "week-widget"), "opened week-widget (product)")

    def test_reports_a_technical_draft_written_before_its_stage(self):
        (self.folder / "draft" / "technical-solution.md").write_text("# Overview\n")
        self.assertEqual(self.gate.problems(), ["draft/technical-solution.md exists before the technical stage was opened"])

    def test_skip_lets_the_next_sections_open_without_a_problem(self):
        self.open_section("glossary", "Glossary")
        self.assertEqual(self.gate.skip("glossary"), "glossary not reviewed, moving on")
        self.assertEqual(self.gate.open("technical", "overview"), "opened overview (technical)")
        self.assertEqual(self.gate.problems(), [])

    def test_a_skipped_section_can_be_reviewed_later(self):
        self.open_section("glossary", "Glossary")
        self.gate.skip("glossary")
        self.assertEqual(self.open_section("glossary", "Glossary"), "opened glossary (product)")

    def test_skip_keeps_an_approved_section_approved(self):
        self.pass_gate("glossary", "product", "Glossary")
        with self.assertRaisesRegex(Refused, "is approved"):
            self.gate.skip("glossary")

    def test_status_persists_between_runs(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.open_section("week-widget", "Week widget")
        self.gate.skip("week-widget")
        self.assertEqual(Gate(self.folder).status(),
                         "product / glossary: approved by Author\nproduct / week-widget: not reviewed")

    # Known defects. Phase 7 fixes each and removes its marker.

    @unittest.expectedFailure
    def test_FR_APC_06_open_accepts_a_reopened_gate(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.gate.reopen("glossary", "renamed a term")
        self.assertEqual(self.open_section("glossary", "Glossary"), "opened glossary (product)")

    @unittest.expectedFailure
    def test_FR_APC_05_section_hash_ignores_a_fenced_heading(self):
        text = FIXTURE.read_text()
        self.write(text)
        self.pass_gate("setup", "product", "Setup")
        self.write(text.replace("the list shows 3 tasks", "the list shows 5 tasks"))
        self.assertEqual(self.gate.problems(), ["setup changed after its approval: reopen it"])

    @unittest.expectedFailure
    def test_FR_APC_08_non_numeric_rounds_is_refused_by_name(self):
        self.open_section("glossary", "Glossary")
        with redirect_stderr(io.StringIO()) as err:
            code = main(["grilled", str(self.folder), "glossary", "--rounds", "abc"])
        self.assertNotEqual(code, 0)
        self.assertIn("rounds", err.getvalue())


if __name__ == "__main__":
    unittest.main()
