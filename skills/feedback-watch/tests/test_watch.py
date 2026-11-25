import io, json, os, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import watch  # noqa: E402

HEAD = "a1b2c3d4e5f6a7b8c9d0"
OLD = "0000000000000000000000000000000000000000"


def run(name, status="COMPLETED", conclusion="SUCCESS", **extra):
    return {"name": name, "workflowName": "ci", "status": status, "conclusion": conclusion, **extra}


def view(*rollup):
    return {"headRefOid": HEAD, "statusCheckRollup": list(rollup)}


def review(login, commit=HEAD):
    return {"user": {"login": login}, "commit_id": commit}


def thread(resolved):
    return {"isResolved": resolved}


class Scripted:
    """A runner that answers gh calls from a list of (code, stdout, stderr) per call."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        return self.answers.pop(0)


def ok(payload):
    return 0, json.dumps(payload), ""


def pr_answers(rollup, reviews=(), threads=()):
    return [
        ok(view(*rollup)),
        ok(list(reviews)),
        ok({"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": list(threads)}}}}}),
    ]


class ChecksTest(unittest.TestCase):
    def test_running_check_is_pending(self):
        self.assertEqual(watch.checks([run("test", status="IN_PROGRESS", conclusion=None)]), (True, []))

    def test_failure_and_timeout_are_failing(self):
        rollup = [run("lint", conclusion="FAILURE"), run("e2e", conclusion="TIMED_OUT")]
        self.assertEqual(watch.checks(rollup), (False, ["e2e", "lint"]))

    def test_cancelled_run_is_ignored(self):
        # Characterizes the defect FR-FW-03 (Q24). Phase 6 replaces it with the marked test below.
        self.assertEqual(watch.checks([run("test", conclusion="CANCELLED")]), (False, []))

    def test_newest_rerun_replaces_an_older_failure(self):
        old = run("test", conclusion="FAILURE", startedAt="2026-11-20T10:00:00Z")
        new = run("test", conclusion="SUCCESS", startedAt="2026-11-20T11:00:00Z")
        self.assertEqual(watch.checks([new, old]), (False, []))

    def test_pending_rerun_hides_an_older_failure_from_the_failing_list(self):
        old = run("test", conclusion="FAILURE", startedAt="2026-11-20T10:00:00Z")
        new = run("test", status="QUEUED", conclusion=None, startedAt="2026-11-20T11:00:00Z")
        self.assertEqual(watch.checks([old, new]), (True, []))

    def test_same_name_in_two_workflows_is_two_checks(self):
        rollup = [run("test", conclusion="FAILURE"), {**run("test"), "workflowName": "other"}]
        self.assertEqual(watch.checks(rollup), (False, ["test"]))

    def test_commit_status_contexts(self):
        rollup = [
            {"context": "legacy/a", "state": "PENDING"},
            {"context": "legacy/b", "state": "ERROR"},
            {"context": "legacy/c", "state": "SUCCESS"},
        ]
        self.assertEqual(watch.checks(rollup), (True, ["legacy/b"]))

    @unittest.expectedFailure
    def test_FR_FW_03_a_sole_cancelled_run_is_failing(self):
        pending, failing = watch.checks([run("test", conclusion="CANCELLED")])
        self.assertFalse(pending)
        self.assertTrue(any("test" in name for name in failing))


class PrStateTest(unittest.TestCase):
    def test_reviewer_must_cover_the_head_commit(self):
        state = watch.pr_state(view(run("test")), [review("claude[bot]", OLD)], [], ["claude[bot]"])
        self.assertEqual(state["missing"], ["claude[bot]"])

    def test_reviewer_match_ignores_case(self):
        state = watch.pr_state(view(run("test")), [review("Claude[bot]")], [], ["claude[bot]"])
        self.assertEqual(state["missing"], [])

    def test_reviewer_match_ignores_the_bot_suffix(self):
        state = watch.pr_state(view(run("test")), [review("claude[bot]")], [], ["claude"])
        self.assertEqual(state["missing"], [])

    def test_no_reviewers_means_nothing_missing(self):
        self.assertEqual(watch.pr_state(view(run("test")), [], [], [])["missing"], [])

    def test_unresolved_threads_are_counted(self):
        state = watch.pr_state(view(run("test")), [], [thread(False), thread(True), thread(False)], [])
        self.assertEqual(state["unresolved"], 2)

    def test_sha_is_short(self):
        self.assertEqual(watch.pr_state(view(), [], [], [])["sha"], HEAD[:7])

    def test_empty_rollup_is_pending_until_allowed(self):
        self.assertTrue(watch.pr_state(view(), [], [], [])["pending"])
        self.assertFalse(watch.pr_state(view(), [], [], [], allow_no_checks=True)["pending"])


class DoneTest(unittest.TestCase):
    def state(self, **changes):
        base = {"sha": "a1b2c3d", "pending": False, "failing": [], "missing": [], "unresolved": 0}
        return {**base, **changes}

    def test_done_when_green_reviewed_and_resolved(self):
        self.assertTrue(watch.is_done(self.state()))

    def test_pending_is_never_done(self):
        self.assertFalse(watch.is_done(self.state(pending=True), "ci"))

    def test_failing_missing_or_unresolved_is_not_done(self):
        self.assertFalse(watch.is_done(self.state(failing=["test"])))
        self.assertFalse(watch.is_done(self.state(missing=["bot"])))
        self.assertFalse(watch.is_done(self.state(unresolved=1)))

    def test_until_ci_ignores_reviews_and_threads(self):
        self.assertTrue(watch.is_done(self.state(failing=["test"], missing=["bot"], unresolved=3), "ci"))


class FormatTest(unittest.TestCase):
    def test_line_has_sha_ci_failing_review_and_threads(self):
        state = {"sha": "a1b2c3d", "pending": False, "failing": ["lint"], "missing": ["bot"], "unresolved": 2}
        self.assertEqual(
            watch.format_pr(7, state, ["bot"]),
            "#7 a1b2c3d | CI done | failing: lint | waiting for review: bot | unresolved threads: 2",
        )

    def test_no_reviewers_leaves_out_the_review_part(self):
        state = {"sha": "a1b2c3d", "pending": True, "failing": [], "missing": [], "unresolved": 0}
        self.assertEqual(watch.format_pr(7, state, []), "#7 a1b2c3d | CI running | failing: none | unresolved threads: 0")


class ReportChangesTest(unittest.TestCase):
    def state(self, pending=True):
        return {"sha": "a1b2c3d", "pending": pending, "failing": [], "missing": [], "unresolved": 0}

    def test_first_round_prints_every_pr(self):
        _, lines = watch.report_changes({}, {1: self.state(), 2: self.state()}, [])
        self.assertEqual(len(lines), 2)

    def test_unchanged_state_prints_nothing(self):
        previous = {1: self.state()}
        _, lines = watch.report_changes(previous, {1: self.state()}, [])
        self.assertEqual(lines, [])

    def test_only_a_changed_pr_prints(self):
        previous = {1: self.state(), 2: self.state()}
        _, lines = watch.report_changes(previous, {1: self.state(pending=False), 2: self.state()}, [])
        self.assertEqual(len(lines), 1)
        self.assertIn("#1", lines[0])


class RunPrTest(unittest.TestCase):
    def run_pr(self, runner, until="all", once=False, timeout=0):
        out = []
        sleeps = []
        code = watch.run_pr([7], "owner/repo", ["bot"], until, 1, timeout, False, once, runner,
                            sleeps.append, lambda: 0, out.append)
        return code, out, sleeps

    def test_pending_then_done_prints_all_done_once(self):
        pending = run("test", status="IN_PROGRESS", conclusion=None)
        runner = Scripted(
            *pr_answers([pending], [review("bot")]),
            *pr_answers([run("test")], [review("bot")]),
        )
        code, out, sleeps = self.run_pr(runner)
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "ALL DONE")
        self.assertEqual(sum(line == "ALL DONE" for line in out), 1)
        self.assertEqual(len(sleeps), 1)
        self.assertEqual(sum("CI running" in line for line in out), 1)

    def test_unchanged_pending_rounds_print_nothing_new(self):
        pending = run("test", status="IN_PROGRESS", conclusion=None)
        runner = Scripted(*pr_answers([pending]), *pr_answers([pending]), *pr_answers([run("test")], [review("bot")]))
        _, out, _ = self.run_pr(runner)
        self.assertEqual(len([line for line in out if line.startswith("#7")]), 2)

    def test_failed_gh_call_skips_the_round_without_crashing(self):
        runner = Scripted(
            (1, "", "HTTP 502: bad gateway\nmore"),
            *pr_answers([run("test")], [review("bot")]),
        )
        with redirect_stderr(io.StringIO()) as err:
            code, out, _ = self.run_pr(runner)
        self.assertEqual(code, 0)
        self.assertIn("skipped #7 this round: HTTP 502: bad gateway", err.getvalue())

    def test_once_reports_not_done_and_exits_1(self):
        runner = Scripted(*pr_answers([run("test", conclusion="FAILURE")], [review("bot")]))
        code, out, sleeps = self.run_pr(runner, once=True)
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "NOT DONE")
        self.assertEqual(sleeps, [])

    def test_timeout_exits_3(self):
        pending = run("test", status="IN_PROGRESS", conclusion=None)
        runner = Scripted(*pr_answers([pending]))
        out = []
        code = watch.run_pr([7], "owner/repo", [], "all", 1, 0.5, False, False, runner,
                            lambda s: None, iter([0, 1]).__next__, out.append)
        self.assertEqual(code, 3)
        self.assertEqual(out[-1], "TIMEOUT")

    def test_until_ci_stops_when_checks_finish_even_with_missing_review(self):
        runner = Scripted(*pr_answers([run("test", conclusion="FAILURE")]))
        code, out, _ = self.run_pr(runner, until="ci", once=True)
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "CI DONE")

    # Known defects. Phase 6 fixes each and removes its marker.

    def run_until_stopped(self, runner, rounds=5):
        """run_pr with a sleep that ends the loop after `rounds` sleeps, so a watcher that never stops ends."""
        out, sleeps = [], []

        def sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) >= rounds:
                raise StopLoop()

        with redirect_stderr(io.StringIO()):
            code = watch.run_pr([7], "owner/repo", [], "all", 1, 0, False, False, runner, sleep, lambda: 0, out.append)
        return code, out

    @unittest.expectedFailure
    def test_FR_FW_08_a_merged_pr_prints_one_line_and_stops(self):
        pending = run("test", status="IN_PROGRESS", conclusion=None)
        merged = [ok({**view(pending), "state": "MERGED"}), *pr_answers([pending])[1:]]
        _, out = self.run_until_stopped(Scripted(*merged * 5))
        self.assertEqual(sum("merged" in line for line in out), 1)

    @unittest.expectedFailure
    def test_FR_FW_07_repeated_gh_failure_prints_a_stdout_line_and_exits_4(self):
        code, out = self.run_until_stopped(Scripted(*[(1, "", "HTTP 502: bad gateway")] * 5))
        self.assertEqual(code, 4)
        self.assertTrue(out[-1].startswith("GH FAILING"))


class FetchPrTest(unittest.TestCase):
    def test_calls_gh_for_view_reviews_and_threads(self):
        runner = Scripted(*pr_answers([run("test")], [review("bot")], [thread(True)]))
        state = watch.fetch_pr(runner, "owner/repo", 7, ["bot"])
        self.assertFalse(state["pending"])
        self.assertEqual(runner.calls[0][:6], ["gh", "pr", "view", "7", "-R", "owner/repo"])
        self.assertEqual(runner.calls[1][-1], "repos/owner/repo/pulls/7/reviews?per_page=100")
        self.assertIn("number=7", runner.calls[2])
        self.assertIn("name=repo", runner.calls[2])

    def test_gh_error_raises_for_the_caller_to_skip(self):
        runner = Scripted((1, "", "Could not resolve to a PullRequest\n"))
        with self.assertRaisesRegex(watch.GhError, "Could not resolve"):
            watch.fetch_pr(runner, "owner/repo", 99, [])


class ResultsTest(unittest.TestCase):
    def test_first_pass_prints_pass(self):
        _, lines = watch.report_results({}, [("pytest -q", 0, "3 passed\n")])
        self.assertEqual(lines, ["PASS pytest -q"])

    def test_same_state_prints_nothing(self):
        previous, _ = watch.report_results({}, [("pytest -q", 0, "")])
        _, lines = watch.report_results(previous, [("pytest -q", 0, "")])
        self.assertEqual(lines, [])

    def test_failure_prints_the_tail_of_the_output(self):
        output = "\n".join(f"line {n}" for n in range(1, 31)) + "\n"
        _, lines = watch.report_results({}, [("pytest -q", 1, output)])
        self.assertEqual(lines[0], "FAIL pytest -q (exit 1)")
        self.assertEqual(len(lines), 1 + watch.TAIL_LINES)
        self.assertEqual(lines[-1], "    line 30")

    def test_recovery_prints_pass(self):
        previous, _ = watch.report_results({}, [("ruff check .", 1, "E501")])
        _, lines = watch.report_results(previous, [("ruff check .", 0, "")])
        self.assertEqual(lines, ["PASS ruff check ."])

    def test_ansi_codes_are_stripped_from_the_tail(self):
        self.assertEqual(watch.tail("\x1b[31mFAILED\x1b[0m test_x\n"), ["FAILED test_x"])

    def test_long_commands_are_shortened_in_the_label(self):
        self.assertEqual(len(watch.label("x" * 200)), watch.LABEL_WIDTH)

    @unittest.expectedFailure
    def test_FR_FW_09_a_failure_with_new_output_prints_again(self):
        previous, _ = watch.report_results({}, [("pytest -q", 1, "test_a failed\n")])
        _, lines = watch.report_results(previous, [("pytest -q", 1, "test_b failed\n")])
        self.assertEqual(lines[:1], ["FAIL pytest -q (exit 1)"])
        self.assertIn("    test_b failed", lines)


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_skips_git_and_dependency_folders(self):
        for folder in (".git", "node_modules"):
            (self.root / folder).mkdir()
            (self.root / folder / "x.js").write_text("x")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("a")
        names = [os.path.relpath(p, self.root) for p in watch.snapshot([str(self.root)])]
        self.assertEqual(names, [os.path.join("src", "a.py")])

    def test_a_changed_file_changes_the_snapshot(self):
        path = self.root / "a.py"
        path.write_text("a")
        before = watch.snapshot([str(self.root)])
        os.utime(path, ns=(1, 1))
        self.assertNotEqual(before, watch.snapshot([str(self.root)]))

    def test_a_single_file_path_is_watched(self):
        path = self.root / "a.py"
        path.write_text("a")
        self.assertEqual(list(watch.snapshot([str(path)])), [str(path)])


class TriggerTest(unittest.TestCase):
    def test_runs_once_after_the_quiet_period(self):
        trigger = watch.Trigger(1, {"a": 1})
        self.assertFalse(trigger.observe({"a": 2}, 10))
        self.assertTrue(trigger.observe({"a": 2}, 11))
        self.assertFalse(trigger.observe({"a": 2}, 12))

    def test_keeps_waiting_while_files_keep_changing(self):
        trigger = watch.Trigger(1, {"a": 1})
        self.assertFalse(trigger.observe({"a": 2}, 10))
        self.assertFalse(trigger.observe({"a": 3}, 10.5))
        self.assertFalse(trigger.observe({"a": 3}, 11))
        self.assertTrue(trigger.observe({"a": 3}, 11.5))

    def test_change_reverted_before_the_run_does_not_run(self):
        trigger = watch.Trigger(1, {"a": 1})
        trigger.observe({"a": 2}, 10)
        self.assertFalse(trigger.observe({"a": 1}, 11))

    def test_zero_delay_runs_on_the_same_tick(self):
        trigger = watch.Trigger(0, {"a": 1})
        self.assertTrue(trigger.observe({"a": 2}, 10))


class RunLocalTest(unittest.TestCase):
    def test_once_passes_and_exits_0(self):
        out = []
        code = watch.run_local(["a", "b"], [], 0, 0, True, lambda c: (0, ""), None, None, out.append)
        self.assertEqual(code, 0)
        self.assertEqual(out, ["PASS a", "PASS b", "ALL PASS"])

    def test_once_lists_failed_commands_and_exits_1(self):
        results = {"a": (0, ""), "b": (2, "boom\n")}
        out = []
        code = watch.run_local(["a", "b"], [], 0, 0, True, lambda c: results[c], None, None, out.append)
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "FAILED: b")

    def test_loop_reruns_after_a_change(self):
        root = Path(tempfile.mkdtemp())
        try:
            target = root / "a.py"
            target.write_text("a")
            runs = []

            def runner(command):
                runs.append(command)
                return 0, ""

            ticks = iter(range(100))

            def sleep(_):
                if len(runs) == 1:
                    target.write_text("changed")
                    os.utime(target, ns=(5, 5))
                if len(runs) >= 2:
                    raise StopLoop()

            out = []
            with self.assertRaises(StopLoop):
                watch.run_local(["cmd"], [str(root)], 0, 0, False, runner, sleep, lambda: next(ticks), out.append)
            self.assertEqual(runs, ["cmd", "cmd"])
        finally:
            shutil.rmtree(root)


class StopLoop(Exception):
    pass


class CliSmokeTest(unittest.TestCase):
    def test_local_once_from_the_command_line(self):
        root = Path(tempfile.mkdtemp())
        try:
            (root / "a.txt").write_text("x")
            done = subprocess.run(
                [sys.executable, "-I", str(Path(watch.__file__)), "local", "--once", "--path", str(root),
                 "--cmd", "test -f a.txt", "--cmd", "false"],
                capture_output=True, text=True, cwd=str(root),
            )
            self.assertEqual(done.returncode, 1)
            self.assertIn("PASS test -f a.txt", done.stdout)
            self.assertIn("FAIL false (exit 1)", done.stdout)
            self.assertTrue(done.stdout.rstrip().endswith("FAILED: false"))
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
