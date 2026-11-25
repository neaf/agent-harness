import io, re, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_draft import TASK_HEADINGS, CheckDraft, check_tasks, main  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
FIXTURE = SKILL.parents[1] / "tests" / "fixtures" / "markdown" / "fenced-headings.md"

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
        text = plan().replace("# 5. Risks\n1. **Query cost**\n", "```sh\n# 5. Risks\n```\n")
        self.assertEqual(self.messages(self.run_check(text), "FAIL"), ["no risks section"])
        fixture = FIXTURE.read_text().replace("# Product solution", "# 1. Product solution")
        text = plan().replace("# 1. Product solution\n" + PRODUCT, fixture)
        self.assertEqual(self.messages(self.run_check(text), "FAIL"), [])

    def test_FR_APC_11_B7_an_estimated_rows_column_is_not_an_estimate(self):
        table = "| Table | Estimated rows |\n|---|---|\n| tasks | 10 estimate |\n"
        self.assertEqual(self.run_check(plan(technical=table)), [("PASS", "all", "no blocking issue")])

    def test_FR_APC_11_B7_an_estimate_header_fails_in_the_technical_solution_too(self):
        for table in ("| Milestone | Tasks | **Effort** |\n|---|---|---|\n",
                      "<table>\n<tr><td>Milestone</td><td>Estimate</td></tr>\n<tr><td>M1</td><td>x</td></tr>\n</table>\n"):
            with self.subTest(table=table):
                results = self.run_check(plan(), technical_solution=f"# Overview\n{table}")
                self.assertIn(("FAIL", "technical-solution.md", "a task table has an estimate column"), results)
        (self.folder / "technical-solution.md").unlink()
        rows = "| Milestone | Tasks |\n|---|---|\n| M1 | Estimate the load |\n"
        self.assertEqual(self.messages(self.run_check(plan(technical=rows)), "FAIL"), [])

    def test_FR_APC_11_B8_template_banned_labels_warn(self):
        warnings = self.messages(self.run_check(plan(technical="1. Add it for P1, which risk 2 covers.\n")), "WARN")
        self.assertEqual(warnings, ['line 14: inline cross-reference "risk 2"', 'line 14: inline cross-reference "P1"'])
        warnings = self.messages(self.run_check(plan(product="Proposed: managers see every task.\n")), "WARN")
        self.assertEqual(warnings, ['line 4: "Proposed": write the rule as decided, or as an open question'])

    def test_FR_APC_11_B9_a_product_page_named_milestones_is_not_the_section(self):
        product = PRODUCT + "## Milestones overview\nThe page lists the milestones of a client.\n"
        text = plan(product=product).replace("# 4. Milestones and verification\n- M1: the week widget.\n",
                                             "# 4. Milestones and verification\n")
        failures = self.messages(self.run_check(text, "product"), "FAIL")
        self.assertEqual(sorted(failures), ["the technical section has content before the product solution is approved"])
        unnumbered = text.replace("# 0. ", "# ").replace("# 1. ", "# ").replace("# 2. ", "# ") \
            .replace("# 3. ", "# ").replace("# 4. ", "# ").replace("# 5. ", "# ")
        failures = self.messages(self.run_check(unnumbered, "product"), "FAIL")
        self.assertEqual(sorted(failures), ["the technical section has content before the product solution is approved"])

    def test_FR_APC_11_L6_prose_words_are_not_code_terms(self):
        product = "A first-class view. Managers query the list by client and see the schema of the week.\n"
        self.assertEqual(self.messages(self.run_check(plan(product=product)), "WARN"), [])


def task(title="[WK M1-1] Add the widget", skip=(), extra="", empty=()):
    parts = [f"### {title}\n"]
    for heading, _ in TASK_HEADINGS:
        if heading in skip:
            continue
        parts.append(f"#### {heading}\n" + ("" if heading in empty else "None, for the test.\n"))
    return "".join(parts) + extra


class TasksTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.path = self.folder / "technical-solution.md"

    def tearDown(self):
        shutil.rmtree(self.folder)

    def check(self, text, milestone=None):
        self.path.write_text("# 6. Task detail\n## M1 tasks\n" + text)
        return [(level, message) for level, _, message in check_tasks(self.path, milestone)]

    def test_a_full_block_passes(self):
        self.assertEqual(self.check(task() + task("[WK M1-2] Add the endpoint")), [("PASS", "2 task block(s)")])

    def test_names_missing_empty_and_unknown_parts(self):
        results = self.check(task(skip=("Files", "QA"), empty=("Base",), extra="#### Notes\nx\n"))
        self.assertIn(("FAIL", "M1-1: no Files, QA"), results)
        self.assertIn(("FAIL", 'M1-1: Base is empty (write "None" and why)'), results)
        self.assertTrue(any(level == "WARN" and 'heading "Notes"' in m for level, m in results), results)

    def test_the_tracker_ticket_is_optional(self):
        self.assertEqual(self.check(task(skip=("Tracker ticket",))), [("PASS", "1 task block(s)")])

    def test_parts_must_keep_the_schema_order(self):
        text = task().replace("#### Base\n", "#### Tmp\n").replace("#### QA\n", "#### Base\n").replace("#### Tmp\n", "#### QA\n")
        self.assertIn(("FAIL", "M1-1: headings out of the schema order"), self.check(text))

    def test_numbering_and_project_code(self):
        results = self.check(task() + task("[WK M1-3] Add the endpoint") + task("[SHOP M2-1] Other"))
        self.assertIn(("FAIL", "M1 tasks are not numbered 1 to 2 in order: M1-1, M1-3"), results)
        self.assertIn(("FAIL", "task titles use more than one project code: SHOP, WK"), results)

    def test_milestone_filter_and_no_block(self):
        text = task() + task("[WK M2-1] Next milestone")
        self.assertEqual(self.check(text, 2), [("PASS", "1 task block(s)")])
        self.assertEqual(self.check(text, 3)[0][0], "FAIL")
        self.assertIn("no task block", self.check("Just prose.\n")[0][1])

    def test_a_fenced_task_is_not_a_task(self):
        self.assertIn("no task block", self.check("```markdown\n" + task() + "```\n")[0][1])

    def test_the_example_in_executable_plan_passes_and_follows_the_schema(self):
        doc = (SKILL / "references" / "executable-plan.md").read_text()
        example = re.search(r"## Task block example\n\n```markdown\n(.*?)\n```", doc, re.DOTALL).group(1)
        self.path.write_text(example + "\n")
        self.assertEqual([r[0] for r in check_tasks(self.path)], ["PASS"])
        listed = re.search(r"these headings, in this order: (.*?)\.\n", doc).group(1).split(", ")
        self.assertEqual(listed, [h for h, _ in TASK_HEADINGS])


class CommandLineTest(unittest.TestCase):
    def run_main(self, *args):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_bad_command_lines_name_the_problem(self):
        missing = str(Path(tempfile.gettempdir()) / "no-such-draft-folder")
        for args, text in (((), "give one draft folder, got 0"), ((missing,), "no draft folder"),
                           (("--tasks",), "--tasks needs a file"), (("--tasks", missing), "no file"),
                           ((".", "--strict"), "unknown option --strict"),
                           (("--tasks", __file__, "--milestone", "x"), "--milestone needs a milestone number")):
            with self.subTest(args=args):
                code, out, err = self.run_main(*args)
                self.assertEqual((code, out), (1, ""))
                self.assertIn(text, err)
                self.assertEqual(len(err.splitlines()), 1)

    def test_help_exits_0(self):
        code, out, _ = self.run_main("--help")
        self.assertEqual(code, 0)
        self.assertIn("check_draft.py --tasks <file>", out)

    def test_tasks_from_the_command_line(self):
        folder = Path(tempfile.mkdtemp())
        try:
            (folder / "t.md").write_text(task())
            script = SKILL / "scripts" / "check_draft.py"
            done = subprocess.run(["/usr/bin/python3", "-I", str(script), "--tasks", str(folder / "t.md"), "--milestone", "M1"],
                                  capture_output=True, text=True, cwd=tempfile.gettempdir(),
                                  env={"PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual((done.returncode, done.stdout), (0, f"PASS {folder / 't.md'}: 1 task block(s)\n"), done.stderr)
        finally:
            shutil.rmtree(folder)


if __name__ == "__main__":
    unittest.main()
