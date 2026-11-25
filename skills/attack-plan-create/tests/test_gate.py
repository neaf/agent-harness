import hashlib, io, json, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
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
        return self.gate.open("product", gate_id, [("draft/attack-plan.md", heading)])

    def pass_gate(self, gate_id, stage, heading=None):
        self.gate.open(stage, gate_id, [("draft/attack-plan.md", heading)] if heading else ())
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

    def test_FR_APC_06_open_accepts_a_reopened_gate(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.gate.reopen("glossary", "renamed a term")
        self.assertEqual(self.open_section("glossary", "Glossary"), "opened glossary (product)")

    def test_FR_APC_06_the_loop_reruns_from_open_after_a_reopen(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.pass_gate("week-widget", "product", "Week widget")
        self.gate.reopen("glossary", "renamed a term")
        self.assertEqual(self.open_section("glossary", "Glossary"), "opened glossary (product)")
        self.gate.grilled("glossary", 1, 0)
        self.gate.approve("glossary", "Author")
        with self.assertRaisesRegex(Refused, "skip them first: week-widget"):
            self.gate.open("product", "out-of-scope")
        self.assertEqual(self.open_section("week-widget", "Week widget"), "opened week-widget (product)")

    def test_open_without_pairs_keeps_the_gate_s_sections(self):
        self.pass_gate("glossary", "product", "Glossary")
        self.gate.reopen("glossary", "renamed a term")
        self.gate.open("product", "glossary")
        self.gate.grilled("glossary", 1, 0)
        self.gate.approve("glossary", "Author")
        self.write(PLAN.replace("a to-do", "a chore"))
        self.assertEqual(self.gate.problems(), ["glossary changed after its approval: reopen it"])

    def test_FR_APC_05_section_hash_ignores_a_fenced_heading(self):
        text = FIXTURE.read_text()
        self.write(text)
        self.pass_gate("setup", "product", "Setup")
        self.write(text.replace("the list shows 3 tasks", "the list shows 5 tasks"))
        self.assertEqual(self.gate.problems(), ["setup changed after its approval: reopen it"])

    def test_staleness_follows_the_order_sections_were_opened(self):
        self.pass_gate("week-widget", "product", "Week widget")
        self.pass_gate("glossary", "product", "Glossary")
        self.assertEqual(self.gate.reopen("week-widget", "new count"), "reopened week-widget\nglossary is now stale")

    def test_one_gate_hashes_several_sections(self):
        (self.folder / "draft" / "technical-solution.md").write_text("# M1 tasks\n- [WK M1-1] Add the widget.\n# M2 tasks\n")
        self.pass_gate("ready", "product-review")
        self.pass_gate("overview", "technical")
        self.gate.open("milestones", "tasks-m1", [("draft/technical-solution.md", "M1 tasks"),
                                                  ("draft/attack-plan.md", "Week widget")])
        self.gate.grilled("tasks-m1", 1, 0)
        self.gate.approve("tasks-m1", "Author")
        self.assertEqual(self.gate.problems(), [])
        self.write(PLAN.replace("3 tasks", "4 tasks"))
        self.assertEqual(self.gate.problems(), ["tasks-m1 changed after its approval: reopen it"])
        self.write(PLAN)
        (self.folder / "draft" / "technical-solution.md").write_text("# M1 tasks\n- [WK M1-1] Add the widget.\n# M2 tasks\n- more\n")
        self.assertEqual(self.gate.problems(), [])

    def test_approve_names_a_missing_file(self):
        self.gate.open("product", "glossary", [("draft/gone.md", None)])
        self.gate.grilled("glossary", 1, 0)
        with self.assertRaisesRegex(Refused, "file gone.md not found"):
            self.gate.approve("glossary", "Author")

    def test_gates_json_records_the_pairs(self):
        self.pass_gate("glossary", "product", "Glossary")
        data = json.loads((self.folder / "gates.json").read_text())
        self.assertEqual(data["version"], 2)
        self.assertEqual(data["gates"][0]["pairs"], [{"file": "draft/attack-plan.md", "heading": "Glossary"}])


class LegacyGatesTest(unittest.TestCase):
    """gates.json written by the gate.py before Phase 7: one file and heading, fence-blind hashes."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "draft").mkdir()
        self.text = FIXTURE.read_text()
        (self.folder / "draft" / "attack-plan.md").write_text(self.text)
        # The old slicing ended "Setup" at the "# seeds ..." line inside the fence.
        old_setup = self.text[self.text.index("## Setup"):self.text.index("# seeds")]
        old_glossary = self.text[self.text.index("## Glossary"):self.text.index("## Setup")]
        gates = [
            {"id": "glossary", "stage": "product", "file": "draft/attack-plan.md", "heading": "Glossary",
             "status": "approved", "approved_by": "Author", "approved_at": "2026-11-20T10:00:00+00:00",
             "hash": hashlib.sha256(old_glossary.strip().encode()).hexdigest()},
            {"id": "setup", "stage": "product", "file": "draft/attack-plan.md", "heading": "Setup",
             "status": "approved", "approved_by": "Author", "approved_at": "2026-11-20T10:00:00+00:00",
             "hash": hashlib.sha256(old_setup.strip().encode()).hexdigest()},
            {"id": "ready-for-review", "stage": "product-review", "file": None, "heading": None, "status": "drafting"},
        ]
        (self.folder / "gates.json").write_text(json.dumps({"gates": gates}, indent=2) + "\n")

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_an_old_file_loads_and_reads_unchanged(self):
        gate = Gate(self.folder)
        self.assertEqual(gate.status(), "product / glossary: approved by Author\n"
                                        "product / setup: approved by Author\n"
                                        "product-review / ready-for-review: drafting")
        self.assertEqual(gate.problems(), [])

    def test_the_next_write_moves_to_the_fence_aware_hash(self):
        gate = Gate(self.folder)
        gate.skip("ready-for-review")
        data = json.loads((self.folder / "gates.json").read_text())
        self.assertEqual(data["version"], 2)
        self.assertNotIn("file", data["gates"][1])
        edited = self.text.replace("the list shows 3 tasks", "the list shows 5 tasks")
        (self.folder / "draft" / "attack-plan.md").write_text(edited)
        self.assertEqual(Gate(self.folder).problems(), ["setup changed after its approval: reopen it"])

    def test_an_old_hash_that_no_longer_matches_stays_changed(self):
        (self.folder / "draft" / "attack-plan.md").write_text(self.text.replace("a to-do", "a chore"))
        gate = Gate(self.folder)
        gate.skip("ready-for-review")
        self.assertEqual(Gate(self.folder).problems(), ["glossary changed after its approval: reopen it"])


class CommandLineTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "draft").mkdir()
        (self.folder / "draft" / "attack-plan.md").write_text(PLAN)

    def tearDown(self):
        shutil.rmtree(self.folder)

    def run_main(self, *args):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = main([a if a != "<f>" else str(self.folder) for a in args])
        return code, out.getvalue(), err.getvalue()

    def test_FR_APC_08_non_numeric_rounds_is_refused_by_name(self):
        self.run_main("open", "<f>", "product", "glossary")
        code, _, err = self.run_main("grilled", "<f>", "glossary", "--rounds", "abc")
        self.assertEqual(code, 2)
        self.assertIn("--rounds needs a whole number, got 'abc'", err)

    def test_missing_positionals_are_named(self):
        code, _, err = self.run_main("open", "<f>", "product")
        self.assertEqual(code, 2)
        self.assertIn("open needs <work folder> <stage> <section>, got 2 argument(s)", err)

    def test_bad_command_lines_exit_2_with_one_line(self):
        for args, text in ((("launch", "<f>"), "unknown command 'launch'"),
                           (("skip", "<f>", "glossary", "--by", "me"), "skip takes no option, not --by"),
                           (("approve", "<f>", "glossary", "--by"), "--by needs a value"),
                           (("open", "<f>", "product", "g", "--heading", "Glossary", "--heading", "Week widget"),
                            "has no --file of its own"),
                           (("status", str(Path(tempfile.gettempdir()) / "no-such-work-folder")), "no work folder"),
                           ((), "no command")):
            with self.subTest(args=args):
                code, out, err = self.run_main(*args)
                self.assertEqual((code, out), (2, ""))
                self.assertIn(text, err)
                self.assertEqual(len(err.splitlines()), 1)

    def test_help_prints_the_usage_and_exits_0(self):
        code, out, _ = self.run_main("--help")
        self.assertEqual(code, 0)
        self.assertIn("gate.py open <work folder> <stage> <section>", out)

    def test_repeated_pairs_and_the_old_option_order(self):
        self.assertEqual(self.run_main("open", "<f>", "product", "glossary", "--heading", "Glossary",
                                       "--file", "draft/attack-plan.md")[0], 0)
        self.assertEqual(self.run_main("open", "<f>", "product", "glossary", "--file", "draft/attack-plan.md",
                                       "--heading", "Glossary", "--file", "draft/attack-plan.md",
                                       "--heading", "Week widget")[0], 0)
        pairs = json.loads((self.folder / "gates.json").read_text())["gates"][0]["pairs"]
        self.assertEqual([p["heading"] for p in pairs], ["Glossary", "Week widget"])

    def test_a_refusal_exits_1_on_stderr(self):
        code, out, err = self.run_main("approve", "<f>", "glossary", "--by", "Author")
        self.assertEqual((code, out, err), (1, "", "REFUSED: no gate glossary\n"))

    def test_runs_from_another_folder_with_I(self):
        script = Path(__file__).resolve().parent.parent / "scripts" / "gate.py"
        done = subprocess.run(["/usr/bin/python3", "-I", str(script), "status", str(self.folder)],
                              capture_output=True, text=True, cwd=tempfile.gettempdir(),
                              env={"PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual((done.returncode, done.stdout), (0, "no gates yet\n"), done.stderr)


if __name__ == "__main__":
    unittest.main()
