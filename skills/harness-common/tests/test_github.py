"""github.py: the gh runner, the paginated pull request snapshot and thread resolve, against a fake runner."""
import json, sys, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import github  # noqa: E402
from github import Gh, GhError  # noqa: E402

HEAD = "a1b2c3d4e5f6a7b8c9d0"


class Fake:
    """runner(args) -> stdout from a list; an exception in the list is raised."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def __call__(self, args):
        self.calls.append(args)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, str) else json.dumps(answer)

    def variables(self, call):
        """GraphQL variables of one call: {name: (flag, value)}."""
        args = self.calls[call]
        pairs = zip(args[2::2], args[3::2])
        return {kv.split("=", 1)[0]: (flag, kv.split("=", 1)[1]) for flag, kv in pairs if not kv.startswith("query=")}

    def query(self, call):
        return next(a for a in self.calls[call] if a.startswith("query="))[len("query="):]


def page(nodes, cursor=None):
    return {"pageInfo": {"hasNextPage": cursor is not None, "endCursor": cursor}, "nodes": nodes}


def check_run(name, status="COMPLETED", conclusion="SUCCESS", started="2026-11-20T10:00:00Z", workflow="ci"):
    suite = {"workflowRun": {"workflow": {"name": workflow}}} if workflow else {"workflowRun": None}
    return {"__typename": "CheckRun", "name": name, "status": status, "conclusion": conclusion,
            "startedAt": started, "checkSuite": suite}


def context(name, state="SUCCESS"):
    return {"__typename": "StatusContext", "context": name, "state": state, "createdAt": "2026-11-20T10:00:00Z"}


def review(login, kind="Bot", state="COMMENTED", commit=HEAD):
    return {"state": state, "author": {"__typename": kind, "login": login}, "commit": {"oid": commit}}


def thread(tid, resolved=False, kind="Bot", login="bot"):
    author = {"__typename": kind, "login": login} if kind else None
    return {"id": tid, "isResolved": resolved, "path": "a.py", "line": 3,
            "comments": {"nodes": [{"url": f"https://x/{tid}", "author": author}]}}


def answer(checks=None, reviews=None, threads=None, state="OPEN", head=HEAD, rollup=True):
    """One GraphQL answer holding the given connections (pass a page() or leave out)."""
    pr = {"state": state, "headRefOid": head}
    if checks is not None:
        pr["commits"] = {"nodes": [{"commit": {"oid": head, "statusCheckRollup": {"contexts": checks}
                                               if rollup else None}}]}
    if reviews is not None:
        pr["reviews"] = reviews
    if threads is not None:
        pr["reviewThreads"] = threads
    return {"data": {"repository": {"pullRequest": pr}}}


class SnapshotTest(unittest.TestCase):
    def test_one_call_reads_state_head_rollup_reviews_and_threads(self):
        fake = Fake(answer(page([check_run("test"), context("legacy")]), page([review("claude")]),
                           page([thread("T1"), thread("T2", True, "User", "ann")])))
        snap = Gh(fake).pr_snapshot("owner/repo", 7)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0][:2], ["api", "graphql"])
        self.assertEqual(fake.variables(0), {"owner": ("-f", "owner"), "name": ("-f", "repo"), "number": ("-F", "7")})
        self.assertEqual((snap["state"], snap["head"]), ("OPEN", HEAD))
        self.assertEqual(snap["rollup"], [
            {"name": "test", "workflowName": "ci", "status": "COMPLETED", "conclusion": "SUCCESS",
             "startedAt": "2026-11-20T10:00:00Z"},
            {"context": "legacy", "state": "SUCCESS", "createdAt": "2026-11-20T10:00:00Z"},
        ])
        self.assertEqual(snap["reviews"], [{"login": "claude", "is_bot": True, "state": "COMMENTED", "commit": HEAD}])
        self.assertEqual(snap["threads"], [
            {"id": "T1", "url": "https://x/T1", "resolved": False, "path": "a.py", "line": 3, "login": "bot",
             "is_bot": True},
            {"id": "T2", "url": "https://x/T2", "resolved": True, "path": "a.py", "line": 3, "login": "ann",
             "is_bot": False},
        ])

    def test_every_page_is_read_and_only_unfinished_connections_are_asked_again(self):
        fake = Fake(
            answer(page([check_run("a")], "c1"), page([review("bot")]), page([thread("T1")], "t1")),
            answer(page([check_run("b")]), threads=page([thread("T2")], "t2")),
            answer(threads=page([thread("T3")])),
        )
        snap = Gh(fake).pr_snapshot("owner/repo", 7)
        self.assertEqual(len(fake.calls), 3)
        self.assertEqual([i["name"] for i in snap["rollup"]], ["a", "b"])
        self.assertEqual([t["id"] for t in snap["threads"]], ["T1", "T2", "T3"])
        self.assertEqual(len(snap["reviews"]), 1)
        self.assertEqual(fake.variables(1)["checks"], ("-f", "c1"))
        self.assertEqual(fake.variables(1)["threads"], ("-f", "t1"))
        self.assertNotIn("reviews", fake.variables(1))
        self.assertNotIn("reviews(", fake.query(1))
        self.assertEqual(set(fake.variables(2)) - {"owner", "name", "number"}, {"threads"})
        self.assertNotIn("commits(", fake.query(2))

    def test_connections_ask_for_100_items(self):
        query = github.snapshot_query(list(github.PARTS))
        self.assertEqual(query.count("first: 100"), 3)
        self.assertIn("pageInfo { hasNextPage endCursor }", query)

    def test_no_rollup_yet_is_an_empty_list(self):
        snap = Gh(Fake(answer(page([]), page([]), page([]), rollup=False))).pr_snapshot("o/r", 1)
        self.assertEqual(snap["rollup"], [])

    def test_merged_state_and_null_reviews(self):
        fake = Fake(answer(page([]), None, page([]), state="MERGED"))
        fake.answers[0]["data"]["repository"]["pullRequest"]["reviews"] = None
        snap = Gh(fake).pr_snapshot("o/r", 1)
        self.assertEqual((snap["state"], snap["reviews"]), ("MERGED", []))

    def test_a_check_run_outside_actions_has_no_workflow(self):
        snap = Gh(Fake(answer(page([check_run("ext", workflow=None)]), page([]), page([])))).pr_snapshot("o/r", 1)
        self.assertIsNone(snap["rollup"][0]["workflowName"])

    def test_deleted_author_is_ghost_and_not_a_bot(self):
        snap = Gh(Fake(answer(page([]), page([]), page([thread("T1", kind=None)])))).pr_snapshot("o/r", 1)
        self.assertEqual((snap["threads"][0]["login"], snap["threads"][0]["is_bot"]), ("ghost", False))

    def test_head_moving_between_pages_raises(self):
        fake = Fake(answer(page([check_run("a")], "c1"), page([]), page([])),
                    answer(page([check_run("b")]), head="f" * 20))
        with self.assertRaisesRegex(GhError, "head moved"):
            Gh(fake).pr_snapshot("o/r", 1)

    def test_missing_pull_request_raises(self):
        with self.assertRaisesRegex(GhError, "no pull request #9 in o/r"):
            Gh(Fake({"data": {"repository": {"pullRequest": None}}})).pr_snapshot("o/r", 9)

    def test_graphql_errors_raise_with_the_first_message(self):
        fake = Fake({"errors": [{"message": "Could not resolve to a PullRequest\nmore"}], "data": None})
        with self.assertRaisesRegex(GhError, "^GraphQL: Could not resolve to a PullRequest$"):
            Gh(fake).pr_snapshot("o/r", 9)

    def test_unexpected_shape_and_non_json_raise(self):
        with self.assertRaisesRegex(GhError, "unexpected GraphQL answer"):
            Gh(Fake({"data": {"repository": {"pullRequest": {"state": "OPEN"}}}})).pr_snapshot("o/r", 1)
        with self.assertRaisesRegex(GhError, "no JSON"):
            Gh(Fake("<html>")).pr_snapshot("o/r", 1)

    def test_runner_error_passes_through(self):
        with self.assertRaisesRegex(GhError, "HTTP 502"):
            Gh(Fake(GhError("HTTP 502"))).pr_snapshot("o/r", 1)


class RepoAndResolveTest(unittest.TestCase):
    def test_repo(self):
        fake = Fake("owner/name\n")
        self.assertEqual(Gh(fake).repo(), "owner/name")
        self.assertEqual(fake.calls[0][:2], ["repo", "view"])

    def test_repo_without_a_slash_raises(self):
        with self.assertRaisesRegex(GhError, "not OWNER/NAME"):
            Gh(Fake("\n")).repo()

    def test_resolve_thread(self):
        fake = Fake({"data": {"resolveReviewThread": {"thread": {"id": "T1", "isResolved": True}}}})
        self.assertTrue(Gh(fake).resolve_thread("T1"))
        self.assertIn("resolveReviewThread", fake.query(0))
        self.assertEqual(fake.variables(0), {"id": ("-f", "T1")})


class RunTest(unittest.TestCase):
    def test_missing_gh(self):
        with mock.patch.object(github.shutil, "which", return_value=None):
            with self.assertRaisesRegex(GhError, "gh not found on PATH"):
                github.run(["repo", "view"])

    def test_failure_names_the_first_stderr_line(self):
        done = mock.Mock(returncode=1, stdout="", stderr="HTTP 401: Bad credentials\nhint\n")
        with mock.patch.object(github.shutil, "which", return_value="/bin/gh"), \
                mock.patch.object(github.subprocess, "run", return_value=done) as call:
            with self.assertRaisesRegex(GhError, "^HTTP 401: Bad credentials$"):
                github.run(["api", "graphql"])
        self.assertEqual(call.call_args[0][0], ["gh", "api", "graphql"])
        self.assertIs(call.call_args[1]["stdin"], github.subprocess.DEVNULL)

    def test_timeout(self):
        with mock.patch.object(github.shutil, "which", return_value="/bin/gh"), \
                mock.patch.object(github.subprocess, "run",
                                  side_effect=github.subprocess.TimeoutExpired("gh", 60)):
            with self.assertRaisesRegex(GhError, "gh api timed out after 60 s"):
                github.run(["api", "graphql"])

    def test_stdout_on_success(self):
        done = mock.Mock(returncode=0, stdout="{}", stderr="")
        with mock.patch.object(github.shutil, "which", return_value="/bin/gh"), \
                mock.patch.object(github.subprocess, "run", return_value=done):
            self.assertEqual(github.run(["api"]), "{}")


if __name__ == "__main__":
    unittest.main()
