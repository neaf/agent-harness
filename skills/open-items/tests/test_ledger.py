"""Pins the version 1 ledger grammar and the reply's block (references/format.md), on invented ledgers."""
import io, re, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
import ledger  # noqa: E402

SCRIPT = SKILL / "scripts" / "ledger.py"
FORMAT = (SKILL / "references" / "format.md").read_text(encoding="utf-8")
EXAMPLE, SUBAGENT_EXAMPLE = re.findall(r"```markdown\n(.*?)```", FORMAT, re.S)

HEAD = "# Open items: demo\n\n" + ledger.COMMENT + "\n\n"


def doc(waiting="", checks="", closed=""):
    return HEAD + f"## Waiting on you\n\n{waiting}\n## Claude will check\n\n{checks}\n## Closed\n\n{closed}"


def problems(text):
    return [message for _, message in ledger.parse(text).problems]


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = ledger.main([str(a) for a in args])
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class Grammar(unittest.TestCase):
    def test_FR_OI_03_the_format_example_fits(self):
        led = ledger.parse(EXAMPLE)
        self.assertEqual(led.problems, [])
        self.assertEqual([ledger.label(i) for i in led.items], ["Y1", "Y2", "Y4", "Y5", "A1"])
        self.assertEqual(led.items[0]["fields"]["recommended"], "Look first")
        self.assertEqual([i["box"] for i in led.closed], ["x", "-", ">"])

    def test_FR_OI_03_the_subagent_items_fit(self):
        led = ledger.parse(doc(SUBAGENT_EXAMPLE))
        self.assertEqual(led.problems, [])
        self.assertEqual(led.items[0]["fields"]["raised by"], "Rebase #820 on main")
        self.assertEqual(led.items[1]["kind"], "review")

    def test_init_writes_an_empty_ledger_that_fits(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "checkout-m2" / "open-items.md"
            self.assertEqual(run("init", path)[0], 0)
            self.assertEqual(run("check", path)[:2], (0, "ok: 0 open, 0 closed\n"))
            self.assertEqual(path.read_text().splitlines()[0], "# Open items: checkout-m2")
            self.assertEqual(run("init", path)[0], 2)

    def test_each_break_is_named(self):
        item = "- [ ] Y1 · decision · Ship it?\n  - from: Claude, \"S\", 2026-11-26 14:02\n"
        cases = {
            "first line": "# Notes\n" + doc()[len("# Open items: demo\n"):],
            "unknown section 'Later'": doc() + "## Later\n",
            "Y items go under": doc(checks=item),
            "kind 'question'": doc(item.replace("decision", "question")),
            "unknown field 'owner'": doc(item + "  - owner: you\n"),
            "out of order": doc(item + "  - state: due\n"),
            "state 'blocked'": doc(item.replace("  - from", "  - state: blocked\n  - from")),
            "used twice": doc(item + item),
            "fits no shape": doc(item + "and this wraps onto a second line\n"),
            "no 'from' field": doc("- [ ] Y1 · decision · Ship it?\n"),
            "a dropped line says why": doc(closed="- [-] Y2 · dropped 2026-11-26 15:10\n"),
            "want 'answered|done|went ahead": doc(closed="- [x] Y2 · closed 2026-11-26 15:10\n"),
            "no '## Closed' section": doc().split("## Closed")[0],
        }
        for want, text in cases.items():
            with self.subTest(want):
                self.assertTrue(any(want in p for p in problems(text)), problems(text))

    def test_FR_OI_04_check_prints_one_line_and_details_behind_v(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad = Path(d) / "good.md", Path(d) / "bad.md"
            good.write_text(EXAMPLE)
            bad.write_text(doc("- [ ] Y1 · decision · Ship it?\nwraps\n"))
            self.assertEqual(run("check", good)[:2], (0, "ok: 5 open (Y1 Y2 Y4 Y5 A1), 3 closed\n"))
            code, out, _ = run("check", bad)
            self.assertEqual((code, out.count("\n")), (1, 1))
            code, out, _ = run("check", bad, "-v")
            self.assertEqual(out.splitlines()[1:], ["line 8: a line that fits no shape (an item's text never wraps)",
                                                   "line 7: Y1 has no 'from' field"])
            self.assertEqual(run("check", Path(d) / "missing.md")[0], 2)


class Ids(unittest.TestCase):
    def test_FR_OI_02_next_counts_past_closed_ids(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "open-items.md"
            path.write_text(EXAMPLE)
            self.assertEqual(run("next", path, "Y")[1], "Y8\n")
            self.assertEqual(run("next", path, "A")[1], "A2\n")
            self.assertEqual(run("next", Path(d) / "none.md", "Y")[1], "Y1\n")

    def test_FR_OI_02_prune_keeps_the_newest_and_the_highest_id(self):
        closed = "".join(f"- [x] Y{n} · done 2026-11-{10 + n:02d} 10:00 · ok\n" for n in range(1, 6))
        closed = "- [-] Y9 · dropped 2026-11-01 09:00 · gone\n" + closed
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "open-items.md"
            path.write_text(doc(closed=closed))
            self.assertEqual(run("prune", path, "--keep", "2")[1], "pruned 3 closed lines, 3 kept\n")
            led = ledger.parse(path.read_text())
            self.assertEqual(led.problems, [])
            self.assertEqual(sorted(ledger.label(i) for i in led.closed), ["Y4", "Y5", "Y9"])
            self.assertEqual(run("next", path, "Y")[1], "Y10\n")
            self.assertEqual(run("prune", path, "--keep", "2")[1], "nothing to prune: 3 closed\n")


class Block(unittest.TestCase):
    def block(self, text, since="", show=()):
        return "\n".join(ledger.block(ledger.parse(text), since, set(show)))

    def test_FR_OI_05_the_example_block(self):
        self.assertEqual(self.block(EXAMPLE, "2026-11-26 14:02"), """**Waiting on you** (4)
- **Y1** decision: Run `bin/schema-lint --fix` now, or look at the 14 warnings first? (I'd look first) (new)
- **Y2** your task: Answer the 2 review threads from Mira on #812. (new)
- **Y4** default: Mark #812 to #815 ready in this order: #812, #814, #813, #815. (goes ahead when CI is green on all four, unless you object) (new)
- **Y5** decision: Can I remove the worktrees ~/dev/shop-wt-cart and ~/dev/shop-wt-tax? (new)

**Claude will check** (1)
- **A1** after the M2 stack merges: Re-check #820, which GitHub shows as conflicting. (new)

Closed this turn: Y3 (answered "Run it"; done: 14 entries added to the todo file); Y6 (dropped: #818 was closed); Y7 (superseded by Y5).""")

    def test_FR_OI_05_a_later_turn_lists_every_Y_and_hides_quiet_A_items(self):
        self.assertEqual(self.block(EXAMPLE, "2026-11-26 16:00"), """**Waiting on you** (4)
- **Y1** decision: Run `bin/schema-lint --fix` now, or look at the 14 warnings first? (I'd look first)
- **Y2** your task: Answer the 2 review threads from Mira on #812.
- **Y4** default: Mark #812 to #815 ready in this order: #812, #814, #813, #815. (goes ahead when CI is green on all four, unless you object)
- **Y5** decision: Can I remove the worktrees ~/dev/shop-wt-cart and ~/dev/shop-wt-tax?""")
        self.assertIn("**Claude will check** (1)\n- **A1**", self.block(EXAMPLE, "2026-11-26 16:00", ["A1"]))
        due = EXAMPLE.replace("  - trigger: after", "  - state: due\n  - trigger: after")
        self.assertIn("- **A1** due, after the M2 stack merges:", self.block(due))

    def test_FR_OI_07_subagent_items_in_the_block(self):
        answered = ("- [ ] Y5 · decision · Keep main's rates, or this branch's?\n  - state: answered\n"
                    "  - subagent: Rebase #820 on main\n  - answer: \"Main's\"\n  - from: Claude, \"S\", 2026-11-26 16:41\n")
        out = self.block(doc(answered + SUBAGENT_EXAMPLE), "2026-11-26 16:58").splitlines()
        self.assertEqual(out[1:], [
            "- **Y5** decision: Keep main's rates, or this branch's? (answered \"Main's\"; with Rebase #820 on main)",
            "- **Y7** decision, from Rebase #820 on main: The 2027 reduced rate is 12% on main and 15% in the #820 fixture: which is right?",
            "- **Y8** review: Receipt email copy (new)"])

    def test_FR_OI_05_the_skill_shows_the_block_the_script_prints(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        shown = re.search(r"--show A1`:\n\n```markdown\n(.*?)```", text, re.S).group(1)
        self.assertEqual(shown, self.block(EXAMPLE, "2026-11-26 15:10", ["A1"]) + "\n")

    def test_nothing_open(self):
        self.assertEqual(self.block(doc()), "Nothing waits on you.")

    def test_FR_OI_05_block_refuses_a_broken_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "open-items.md"
            path.write_text(doc("- [ ] Y1 · decision · x\n"))
            self.assertEqual(run("block", path)[:2], (1, f"FAIL: 1 problem in {path}\n"))
            self.assertEqual(run("block", path, "--since", "today")[0], 2)


class Script(unittest.TestCase):
    def test_NFR_01_runs_isolated_on_the_system_python(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "open-items.md"
            path.write_text(EXAMPLE)
            done = subprocess.run(["/usr/bin/python3", "-I", str(SCRIPT), "check", str(path)],
                                  capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual((done.returncode, done.stdout), (0, "ok: 5 open (Y1 Y2 Y4 Y5 A1), 3 closed\n"))


if __name__ == "__main__":
    unittest.main()
