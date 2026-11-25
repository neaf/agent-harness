import io, os, shutil, subprocess, sys, tempfile, time, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import watch  # noqa: E402
from github import GhError  # noqa: E402  (watch.py puts harness-common/scripts on sys.path)

HEAD = "a1b2c3d4e5f6a7b8c9d0"
OLD = "0000000000000000000000000000000000000000"


def run(name, status="COMPLETED", conclusion="SUCCESS", **extra):
    return {"name": name, "workflowName": "ci", "status": status, "conclusion": conclusion, **extra}


def snap(*rollup, reviews=(), threads=(), state="OPEN"):
    """A github.Gh.pr_snapshot answer."""
    return {"state": state, "head": HEAD, "rollup": list(rollup), "reviews": list(reviews), "threads": list(threads)}


def review(login, commit=HEAD, state="COMMENTED", is_bot=True):
    return {"login": login, "is_bot": is_bot, "state": state, "commit": commit}


def thread(resolved, is_bot=True):
    return {"id": "T", "url": "u", "resolved": resolved, "path": "a.py", "line": 1, "login": "x", "is_bot": is_bot}


class FakeGh:
    """Answers pr_snapshot from a list: a snapshot dict, or an exception to raise."""

    def __init__(self, *answers, repo="owner/repo"):
        self.answers, self.calls, self.name = list(answers), [], repo

    def pr_snapshot(self, repo, number):
        self.calls.append((repo, number))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def repo(self):
        if isinstance(self.name, Exception):
            raise self.name
        return self.name


class StopLoop(Exception):
    pass


class ChecksTest(unittest.TestCase):
    def test_running_check_is_pending(self):
        self.assertEqual(watch.checks([run("test", status="IN_PROGRESS", conclusion=None)]), (True, []))

    def test_failure_and_timeout_are_failing(self):
        rollup = [run("lint", conclusion="FAILURE"), run("e2e", conclusion="TIMED_OUT")]
        self.assertEqual(watch.checks(rollup), (False, ["e2e", "lint"]))

    def test_skipped_neutral_and_stale_are_fine(self):
        rollup = [run(name, conclusion=name.upper()) for name in ("skipped", "neutral", "stale", "action_required")]
        self.assertEqual(watch.checks(rollup), (False, []))

    def test_newest_rerun_replaces_an_older_failure(self):
        old = run("test", conclusion="FAILURE", startedAt="2026-11-20T10:00:00Z")
        new = run("test", conclusion="SUCCESS", startedAt="2026-11-20T11:00:00Z")
        self.assertEqual(watch.checks([new, old]), (False, []))

    def test_pending_rerun_hides_an_older_failure_from_the_failing_list(self):
        old = run("test", conclusion="FAILURE", startedAt="2026-11-20T10:00:00Z")
        new = run("test", status="QUEUED", conclusion=None, startedAt="2026-11-20T11:00:00Z")
        self.assertEqual(watch.checks([old, new]), (True, []))

    def test_queued_rerun_without_a_start_time_is_the_newest(self):
        old = run("test", conclusion="FAILURE", startedAt="2026-11-20T10:00:00Z")
        for started in (None, "", "0001-01-01T00:00:00Z"):
            new = run("test", status="QUEUED", conclusion=None, startedAt=started)
            self.assertEqual(watch.checks([new, old]), (True, []), started)

    def test_same_name_in_two_workflows_is_two_checks(self):
        rollup = [run("test", conclusion="FAILURE"), {**run("test"), "workflowName": "other"}]
        self.assertEqual(watch.checks(rollup), (False, ["test"]))

    def test_commit_status_contexts(self):
        rollup = [
            {"context": "legacy/a", "state": "PENDING", "createdAt": "2026-11-20T10:00:00Z"},
            {"context": "legacy/b", "state": "ERROR", "createdAt": "2026-11-20T10:00:00Z"},
            {"context": "legacy/c", "state": "SUCCESS", "createdAt": "2026-11-20T10:00:00Z"},
        ]
        self.assertEqual(watch.checks(rollup), (True, ["legacy/b"]))

    def test_FR_FW_03_a_sole_cancelled_run_is_failing(self):
        pending, failing = watch.checks([run("test", conclusion="CANCELLED")])
        self.assertFalse(pending)
        self.assertEqual(failing, ["test (cancelled)"])

    def test_cancelled_run_beside_another_run_is_superseded(self):
        cancelled = run("test", conclusion="CANCELLED", startedAt="2026-11-20T11:00:00Z")
        older = run("test", conclusion="SUCCESS", startedAt="2026-11-20T10:00:00Z")
        self.assertEqual(watch.checks([older, cancelled]), (False, []))
        self.assertEqual(watch.checks([cancelled, older]), (False, []))


class PrStateTest(unittest.TestCase):
    def test_reviewer_must_cover_the_head_commit(self):
        state = watch.pr_state(snap(run("test"), reviews=[review("claude[bot]", OLD)]), ["claude[bot]"])
        self.assertEqual(state["missing"], ["claude[bot]"])

    def test_reviewer_match_ignores_case(self):
        state = watch.pr_state(snap(run("test"), reviews=[review("Claude")]), ["claude[bot]"])
        self.assertEqual(state["missing"], [])

    def test_reviewer_match_ignores_the_bot_suffix(self):
        state = watch.pr_state(snap(run("test"), reviews=[review("claude")]), ["claude[bot]"])
        self.assertEqual(state["missing"], [])

    def test_changes_requested_counts_as_reviewed_dismissed_does_not(self):
        for review_state, missing in (("CHANGES_REQUESTED", []), ("APPROVED", []), ("DISMISSED", ["bot"]),
                                      ("PENDING", ["bot"])):
            state = watch.pr_state(snap(run("test"), reviews=[review("bot", state=review_state)]), ["bot"])
            self.assertEqual(state["missing"], missing, review_state)

    def test_no_reviewers_means_nothing_missing(self):
        self.assertEqual(watch.pr_state(snap(run("test")), [])["missing"], [])

    def test_unresolved_threads_are_counted_with_the_human_ones(self):
        threads = [thread(False), thread(True), thread(False, is_bot=False), thread(True, is_bot=False)]
        state = watch.pr_state(snap(run("test"), threads=threads), [])
        self.assertEqual((state["unresolved"], state["human"]), (2, 1))

    def test_sha_is_short(self):
        self.assertEqual(watch.pr_state(snap(), [])["sha"], HEAD[:7])

    def test_empty_rollup_is_pending_until_allowed(self):
        self.assertTrue(watch.pr_state(snap(), [])["pending"])
        self.assertFalse(watch.pr_state(snap(), [], allow_no_checks=True)["pending"])


def state(**changes):
    base = {"sha": "a1b2c3d", "pending": False, "failing": [], "missing": [], "unresolved": 0, "human": 0}
    return {**base, **changes}


class DoneTest(unittest.TestCase):
    def test_done_when_green_reviewed_and_resolved(self):
        self.assertTrue(watch.is_done(state()))

    def test_pending_is_never_done(self):
        for until in watch.DONE_LINES:
            self.assertFalse(watch.is_done(state(pending=True), until))

    def test_failing_missing_or_unresolved_is_not_done(self):
        self.assertFalse(watch.is_done(state(failing=["test"])))
        self.assertFalse(watch.is_done(state(missing=["bot"])))
        self.assertFalse(watch.is_done(state(unresolved=1)))

    def test_until_ci_ignores_reviews_and_threads(self):
        self.assertTrue(watch.is_done(state(failing=["test"], missing=["bot"], unresolved=3), "ci"))

    def test_until_bots_allows_human_threads_only(self):
        self.assertTrue(watch.is_done(state(unresolved=2, human=2), "bots"))
        self.assertFalse(watch.is_done(state(unresolved=2, human=1), "bots"))
        self.assertFalse(watch.is_done(state(unresolved=2, human=2)))
        self.assertFalse(watch.is_done(state(failing=["test"], unresolved=1, human=1), "bots"))
        self.assertFalse(watch.is_done(state(missing=["bot"]), "bots"))


class FormatTest(unittest.TestCase):
    def test_line_has_sha_ci_failing_review_and_threads(self):
        self.assertEqual(
            watch.format_pr(7, state(failing=["lint"], missing=["bot"], unresolved=2), ["bot"]),
            "#7 a1b2c3d | CI done | failing: lint | waiting for review: bot | unresolved threads: 2",
        )

    def test_no_reviewers_leaves_out_the_review_part(self):
        self.assertEqual(watch.format_pr(7, state(pending=True), []),
                         "#7 a1b2c3d | CI running | failing: none | unresolved threads: 0")

    def test_human_threads_are_named(self):
        self.assertEqual(watch.format_pr(7, state(unresolved=3, human=1), ["bot"]),
                         "#7 a1b2c3d | CI done | failing: none | reviewed | unresolved threads: 3 (human 1)")


class ReportChangesTest(unittest.TestCase):
    def test_first_round_prints_every_pr(self):
        _, lines = watch.report_changes({}, {1: state(), 2: state()}, [])
        self.assertEqual(len(lines), 2)

    def test_unchanged_state_prints_nothing(self):
        _, lines = watch.report_changes({1: state()}, {1: state()}, [])
        self.assertEqual(lines, [])

    def test_only_a_changed_pr_prints(self):
        previous = {1: state(pending=True), 2: state(pending=True)}
        _, lines = watch.report_changes(previous, {1: state(), 2: state(pending=True)}, [])
        self.assertEqual(len(lines), 1)
        self.assertIn("#1", lines[0])


PENDING = run("test", status="IN_PROGRESS", conclusion=None)
DONE = snap(run("test"), reviews=[review("bot")])


class RunPrTest(unittest.TestCase):
    def run_pr(self, gh, numbers=(7,), reviewers=("bot",), until="all", once=False, timeout=0, rounds=10):
        """run_pr with a sleep that ends the loop after `rounds` sleeps, so a watcher that never stops ends."""
        out, sleeps = [], []

        def sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) >= rounds:
                raise StopLoop()

        with redirect_stderr(io.StringIO()) as err:
            code = watch.run_pr(list(numbers), "owner/repo", list(reviewers), until, 1, timeout, False, once, gh,
                                sleep, lambda: 0, out.append)
        self.err = err.getvalue()
        return code, out, sleeps

    def test_pending_then_done_twice_prints_all_done_once(self):
        code, out, sleeps = self.run_pr(FakeGh(snap(PENDING, reviews=[review("bot")]), DONE, DONE))
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "ALL DONE")
        self.assertEqual(sum(line == "ALL DONE" for line in out), 1)
        self.assertEqual(len(sleeps), 2)
        self.assertEqual(sum("CI running" in line for line in out), 1)

    def test_FR_FW_04_one_done_round_is_not_enough(self):
        # The first poll sees one finished check; the second sees a second check registered and running.
        gh = FakeGh(DONE, snap(run("test"), PENDING | {"name": "e2e"}, reviews=[review("bot")]), DONE, DONE)
        code, out, sleeps = self.run_pr(gh)
        self.assertEqual(code, 0)
        self.assertEqual(len(sleeps), 3)
        self.assertEqual(out.count("ALL DONE"), 1)
        self.assertIn("CI running", out[1])

    def test_unchanged_pending_rounds_print_nothing_new(self):
        _, out, _ = self.run_pr(FakeGh(snap(PENDING), snap(PENDING), DONE, DONE))
        self.assertEqual(len([line for line in out if line.startswith("#7")]), 2)

    def test_failed_gh_call_skips_the_round_without_crashing(self):
        code, out, _ = self.run_pr(FakeGh(GhError("HTTP 502: bad gateway"), DONE, DONE))
        self.assertEqual(code, 0)
        self.assertIn("skipped #7 this round: HTTP 502: bad gateway", self.err)

    def test_FR_FW_07_repeated_gh_failure_prints_a_stdout_line_and_exits_4(self):
        code, out, sleeps = self.run_pr(FakeGh(*[GhError("HTTP 502: bad gateway")] * 5))
        self.assertEqual(code, 4)
        self.assertEqual(out[-1], "GH FAILING: #7 HTTP 502: bad gateway")
        self.assertEqual(len(sleeps), watch.GH_FAILING_ROUNDS - 1)

    def test_a_good_round_resets_the_failure_count(self):
        error = GhError("HTTP 502")
        code, _, sleeps = self.run_pr(FakeGh(error, error, DONE, error, error, DONE, DONE))
        self.assertEqual(code, 0)
        self.assertEqual(len(sleeps), 6)

    def test_FR_FW_08_a_merged_pr_prints_one_line_and_stops(self):
        code, out, sleeps = self.run_pr(FakeGh(*[snap(PENDING, state="MERGED")] * 5), reviewers=())
        self.assertEqual(sum("merged" in line for line in out), 1)
        self.assertEqual(out, ["#7 merged, stopped watching", "ALL DONE"])
        self.assertEqual((code, sleeps), (0, []))

    def test_a_closed_pr_leaves_the_others_watched(self):
        gh = FakeGh(snap(PENDING, state="CLOSED"), snap(PENDING), DONE, DONE)
        code, out, _ = self.run_pr(gh, numbers=(7, 8))
        self.assertEqual(code, 0)
        self.assertEqual(out[0], "#7 closed, stopped watching")
        self.assertEqual(gh.calls, [("owner/repo", 7), ("owner/repo", 8), ("owner/repo", 8), ("owner/repo", 8)])

    def test_once_reports_not_done_and_exits_1(self):
        code, out, sleeps = self.run_pr(FakeGh(snap(run("test", conclusion="FAILURE"), reviews=[review("bot")])),
                                        once=True)
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "NOT DONE")
        self.assertEqual(sleeps, [])

    def test_once_reports_all_done_from_one_round(self):
        code, out, sleeps = self.run_pr(FakeGh(DONE), once=True)
        self.assertEqual((code, out[-1], sleeps), (0, "ALL DONE", []))

    def test_timeout_exits_3(self):
        out = []
        code = watch.run_pr([7], "owner/repo", [], "all", 1, 0.5, False, False, FakeGh(snap(PENDING)),
                            lambda s: None, iter([0, 1]).__next__, out.append)
        self.assertEqual(code, 3)
        self.assertEqual(out[-1], "TIMEOUT")

    def test_until_ci_stops_when_checks_finish_even_with_missing_review(self):
        failing = snap(run("test", conclusion="FAILURE"))
        code, out, _ = self.run_pr(FakeGh(failing, failing), until="ci")
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "CI DONE")

    def test_until_bots_stops_with_human_threads_open(self):
        human = snap(run("test"), reviews=[review("bot")], threads=[thread(False, is_bot=False)])
        code, out, _ = self.run_pr(FakeGh(human, human), until="bots")
        self.assertEqual(code, 0)
        self.assertEqual(out, ["#7 a1b2c3d | CI done | failing: none | reviewed | unresolved threads: 1 (human 1)",
                               "BOTS DONE"])

    def test_until_bots_waits_for_bot_threads(self):
        bot = snap(run("test"), reviews=[review("bot")], threads=[thread(False)])
        with self.assertRaises(StopLoop):
            self.run_pr(FakeGh(*[bot] * 3), until="bots", rounds=2)


class MainTest(unittest.TestCase):
    def main(self, argv, gh):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            code = watch.main(argv, gh=gh)
        return code, out.getvalue().splitlines()

    def test_once_prints_to_stdout(self):
        code, lines = self.main(["pr", "7", "--once"], FakeGh(DONE))
        self.assertEqual((code, lines), (0, ["#7 a1b2c3d | CI done | failing: none | unresolved threads: 0",
                                             "ALL DONE"]))

    def test_unresolvable_repository_prints_gh_failing_and_exits_4(self):
        code, lines = self.main(["pr", "7"], FakeGh(repo=GhError("not a git repository")))
        self.assertEqual((code, lines), (4, ["GH FAILING: cannot resolve the repository: not a git repository"]))

    def test_interval_must_be_positive(self):
        for mode in (["pr", "7"], ["local", "--cmd", "true"]):
            for value in ("0", "-1", "nan", "x"):
                with self.assertRaises(SystemExit) as stop, redirect_stderr(io.StringIO()):
                    watch.parser().parse_args(mode + ["--interval", value])
                self.assertEqual(stop.exception.code, 2)

    def test_watch_has_no_gh_subprocess_and_no_write(self):
        source = Path(watch.__file__).read_text()
        for word in ('"gh"', "resolve_thread", "graphql"):
            self.assertNotIn(word, source)


class ResultsTest(unittest.TestCase):
    def test_first_pass_prints_pass(self):
        _, lines = watch.report_results({}, [("pytest -q", 0, "3 passed\n")])
        self.assertEqual(lines, ["PASS pytest -q"])

    def test_same_state_prints_nothing(self):
        previous, _ = watch.report_results({}, [("pytest -q", 0, "")])
        _, lines = watch.report_results(previous, [("pytest -q", 0, "")])
        self.assertEqual(lines, [])

    def test_same_failure_prints_nothing(self):
        previous, _ = watch.report_results({}, [("pytest -q", 1, "test_a failed\n")])
        _, lines = watch.report_results(previous, [("pytest -q", 1, "test_a failed\n")])
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

    def test_FR_FW_09_a_failure_with_new_output_prints_again(self):
        previous, _ = watch.report_results({}, [("pytest -q", 1, "test_a failed\n")])
        _, lines = watch.report_results(previous, [("pytest -q", 1, "test_b failed\n")])
        self.assertEqual(lines[:1], ["FAIL pytest -q (exit 1)"])
        self.assertIn("    test_b failed", lines)

    def test_a_timed_out_command_is_a_failure(self):
        _, lines = watch.report_results({}, [("sleep 9", None, "timed out after 1 s\n")])
        self.assertEqual(lines, ["FAIL sleep 9 (timed out)", "    timed out after 1 s"])


class RunShellTest(unittest.TestCase):
    def test_output_and_exit_code(self):
        self.assertEqual(watch.run_shell("echo out; echo err >&2; exit 3", 10), (3, "out\nerr\n"))

    def test_stdin_is_closed(self):
        self.assertEqual(watch.run_shell("cat", 10), (0, ""))

    def test_timeout_kills_the_command_and_its_children(self):
        began = time.monotonic()
        code, output = watch.run_shell("echo started; sleep 30 & wait", 0.5)
        self.assertLess(time.monotonic() - began, 10)
        self.assertIsNone(code)
        self.assertIn("started", output)
        self.assertTrue(output.rstrip().endswith("timed out after 0.5 s"))


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_skips_git_dependency_and_skill_state_folders(self):
        for folder in (".git", "node_modules", ".attack-plan", ".rearch", ".ai-notes"):
            (self.root / folder).mkdir()
            (self.root / folder / "x.md").write_text("x")
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

    def test_files_seen_after_a_run_do_not_trigger(self):
        trigger = watch.Trigger(0, {"a": 1})
        trigger.ran({"a": 1, "out.log": 1})
        self.assertFalse(trigger.observe({"a": 1, "out.log": 1}, 10))


class RunLocalTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.target = self.root / "a.py"
        self.target.write_text("a")

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_once_passes_and_exits_0(self):
        out = []
        code = watch.run_local(["a", "b"], [], 0, 0, True, lambda c: (0, ""), None, None, out.append)
        self.assertEqual(code, 0)
        self.assertEqual(out, ["PASS a", "PASS b", "ALL PASS"])

    def test_once_lists_failed_commands_and_exits_1(self):
        results = {"a": (0, ""), "b": (2, "boom\n"), "c": (None, "timed out after 1 s\n")}
        out = []
        code = watch.run_local(["a", "b", "c"], [], 0, 0, True, lambda c: results[c], None, None, out.append)
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "FAILED: b, c")

    def loop(self, runner, on_sleep, stop_after):
        runs = []

        def counted(command):
            runs.append(command)
            return runner(command)

        ticks = iter(range(100))

        def sleep(_):
            on_sleep(len(runs))
            if len(runs) >= stop_after:
                raise StopLoop()

        with self.assertRaises(StopLoop):
            watch.run_local(["cmd"], [str(self.root)], 0, 0, False, counted, sleep, lambda: next(ticks), [].append)
        return runs

    def test_loop_reruns_after_a_change(self):
        def on_sleep(runs):
            if runs == 1:
                self.target.write_text("changed")
                os.utime(self.target, ns=(5, 5))

        self.assertEqual(self.loop(lambda c: (0, ""), on_sleep, 2), ["cmd", "cmd"])

    def test_files_the_commands_write_do_not_rerun_them(self):
        def runner(command):
            (self.root / "out.log").write_text(str(time.monotonic_ns()))
            return 0, ""

        sleeps = []

        def on_sleep(runs):
            sleeps.append(runs)
            if len(sleeps) >= 5:
                raise StopLoop()

        self.assertEqual(self.loop(runner, on_sleep, 2), ["cmd"])

    def test_timeout_exits_3(self):
        out = []
        code = watch.run_local(["cmd"], [str(self.root)], 1, 0, False, lambda c: (0, ""), lambda s: None,
                               iter([0, 30, 31, 61]).__next__, out.append, timeout=60)
        self.assertEqual(code, 3)
        self.assertEqual(out, ["PASS cmd", "TIMEOUT"])


class CliSmokeTest(unittest.TestCase):
    def cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, "-I", str(Path(watch.__file__)), *args],
                              capture_output=True, text=True, cwd=cwd, stdin=subprocess.DEVNULL)

    def test_local_once_from_the_command_line(self):
        root = Path(tempfile.mkdtemp())
        try:
            (root / "a.txt").write_text("x")
            done = self.cli("local", "--once", "--path", str(root), "--cmd", "test -f a.txt", "--cmd", "false",
                            cwd=str(root))
            self.assertEqual(done.returncode, 1)
            self.assertIn("PASS test -f a.txt", done.stdout)
            self.assertIn("FAIL false (exit 1)", done.stdout)
            self.assertTrue(done.stdout.rstrip().endswith("FAILED: false"))
        finally:
            shutil.rmtree(root)

    def test_help_exits_0(self):
        for args in ([], ["pr"], ["local"]):
            done = self.cli(*args, "--help")
            self.assertEqual(done.returncode, 0, args)
            self.assertIn("usage", done.stdout)


if __name__ == "__main__":
    unittest.main()
