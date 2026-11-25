"""review_threads.py: list with bot or human; resolve and reply refuse human threads. gh is a fake, never GitHub."""
import io, json, os, shutil, subprocess, sys, tempfile, textwrap, unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "review_threads.py"
sys.path.insert(0, str(SCRIPT.parent))
import review_threads  # noqa: E402
from github import GhError  # noqa: E402  (review_threads put harness-common/scripts on the path)


def thread(tid, is_bot=True, resolved=False, login="rabbit", body="Guard the nil case.\nDetails", line=7):
    return {"id": tid, "url": f"https://github.com/o/r/pull/1#{tid}", "resolved": resolved, "path": "app/a.rb",
            "line": line, "login": login, "is_bot": is_bot, "body": body}


class FakeGh:
    def __init__(self, snapshots=None, threads=None, resolve_answer=True):
        self.snapshots, self.threads, self.resolve_answer = snapshots or {}, threads or {}, resolve_answer
        self.resolved, self.replies, self.repo_calls = [], [], 0
        self.reply_error = self.resolve_error = None

    def repo(self):
        self.repo_calls += 1
        return "o/r"

    def pr_snapshot(self, repo, number):
        answer = self.snapshots[number]
        if isinstance(answer, Exception):
            raise answer
        return {"threads": answer}

    def thread(self, thread_id):
        if thread_id not in self.threads:
            raise GhError(f"no review thread {thread_id}")
        return self.threads[thread_id]

    def reply_to_thread(self, thread_id, body):
        if self.reply_error:
            raise self.reply_error
        self.replies.append((thread_id, body))
        return f"https://github.com/o/r/pull/1#reply-{thread_id}"

    def resolve_thread(self, thread_id):
        if self.resolve_error:
            raise self.resolve_error
        self.resolved.append(thread_id)
        return self.resolve_answer


def run(argv, gh):
    with mock.patch("sys.stdout", io.StringIO()) as out:
        code = review_threads.main(argv, gh=gh)
    return code, out.getvalue().splitlines()


class ListTest(unittest.TestCase):
    def test_lists_unresolved_threads_with_bot_or_human(self):
        gh = FakeGh({1: [thread("T1"), thread("T2", is_bot=False, login="ann", line=None), thread("T3", resolved=True)],
                     2: []})
        code, lines = run(["list", "--pr", "1", "2"], gh)
        self.assertEqual(code, 0)
        self.assertEqual(lines, [
            "#1 T1 bot rabbit app/a.rb:7 https://github.com/o/r/pull/1#T1 | Guard the nil case.",
            "#1 T2 human ann app/a.rb https://github.com/o/r/pull/1#T2 | Guard the nil case.",
            "2 unresolved: 1 bot, 1 human",
        ])
        self.assertEqual(gh.repo_calls, 1)

    def test_repo_flag_skips_the_lookup_and_long_text_is_cut(self):
        gh = FakeGh({1: [thread("T1", body="\n\n" + "x" * 300)]})
        code, lines = run(["list", "--pr", "1", "--repo", "o/r"], gh)
        self.assertEqual(gh.repo_calls, 0)
        self.assertTrue(lines[0].endswith("| " + "x" * 97 + "..."))

    def test_a_pr_that_cannot_be_read_fails_and_the_rest_is_listed(self):
        gh = FakeGh({1: GhError("HTTP 502"), 2: [thread("T1")]})
        code, lines = run(["list", "--pr", "1", "2"], gh)
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "FAIL #1: HTTP 502")
        self.assertEqual(lines[-1], "1 unresolved: 1 bot, 0 human")


class ResolveTest(unittest.TestCase):
    def test_resolves_bot_threads_only(self):
        gh = FakeGh(threads={"T1": thread("T1"), "T2": thread("T2", is_bot=False, login="ann"),
                             "T3": thread("T3", resolved=True)})
        code, lines = run(["resolve", "--thread", "T1", "T2", "T3"], gh)
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["RESOLVED T1", "REFUSED: T2 human thread (ann), the user resolves it",
                                 "RESOLVED T3 (already)"])
        self.assertEqual(gh.resolved, ["T1"])

    def test_all_bot_threads_resolved_exits_0(self):
        code, lines = run(["resolve", "--thread", "T1"], FakeGh(threads={"T1": thread("T1")}))
        self.assertEqual((code, lines), (0, ["RESOLVED T1"]))

    def test_unknown_thread_and_unresolved_answer_fail(self):
        gh = FakeGh(threads={"T1": thread("T1")}, resolve_answer=False)
        code, lines = run(["resolve", "--thread", "T9", "T1"], gh)
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["FAIL T9: no review thread T9", "FAIL T1: GitHub did not mark it resolved"])

    def test_a_deleted_author_counts_as_human(self):
        gh = FakeGh(threads={"T1": thread("T1", is_bot=False, login="ghost")})
        self.assertEqual(run(["resolve", "--thread", "T1"], gh)[1], ["REFUSED: T1 human thread (ghost), the user resolves it"])
        self.assertEqual(gh.resolved, [])


class ReplyTest(unittest.TestCase):
    """FR-APE-15: a bot REPLY thread gets its reply posted, then resolved; a human thread is never written to."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.body = self.tmp / "reply.md"
        self.body.write_text("No change needed: the guard is at app/a.rb:3.\n")

    def reply(self, gh, tid="T1"):
        return run(["reply", "--thread", tid, "--body-file", str(self.body)], gh)

    def test_posts_the_reply_then_resolves(self):
        gh = FakeGh(threads={"T1": thread("T1")})
        code, lines = self.reply(gh)
        self.assertEqual((code, lines), (0, ["REPLIED T1 https://github.com/o/r/pull/1#reply-T1", "RESOLVED T1"]))
        self.assertEqual(gh.replies, [("T1", "No change needed: the guard is at app/a.rb:3.")])
        self.assertEqual(gh.resolved, ["T1"])

    def test_human_and_deleted_author_threads_are_refused_and_untouched(self):
        for login in ("ann", "ghost"):
            gh = FakeGh(threads={"T2": thread("T2", is_bot=False, login=login)})
            code, lines = self.reply(gh, "T2")
            self.assertEqual((code, lines), (1, [f"REFUSED: T2 human thread ({login}), the user replies"]))
            self.assertEqual((gh.replies, gh.resolved), ([], []))

    def test_a_resolved_thread_gets_no_reply(self):
        gh = FakeGh(threads={"T1": thread("T1", resolved=True)})
        self.assertEqual(self.reply(gh), (1, ["REFUSED: T1 already resolved, no reply posted"]))
        self.assertEqual((gh.replies, gh.resolved), ([], []))

    def test_a_failed_post_resolves_nothing(self):
        gh = FakeGh(threads={"T1": thread("T1")})
        gh.reply_error = GhError("HTTP 502")
        self.assertEqual(self.reply(gh), (1, ["FAIL T1: HTTP 502"]))
        self.assertEqual(gh.resolved, [])

    def test_a_failed_resolve_after_the_reply_says_so(self):
        gh = FakeGh(threads={"T1": thread("T1")}, resolve_answer=False)
        code, lines = self.reply(gh)
        self.assertEqual(code, 1)
        self.assertEqual(lines[1], "FAIL T1: replied, not resolved: GitHub did not mark it resolved")
        gh = FakeGh(threads={"T1": thread("T1")})
        gh.resolve_error = GhError("HTTP 403")
        self.assertEqual(self.reply(gh)[1][1], "FAIL T1: replied, not resolved: HTTP 403")

    def test_empty_or_missing_body_is_a_usage_error(self):
        self.body.write_text("  \n")
        gh = FakeGh(threads={"T1": thread("T1")})
        for path in (str(self.body), str(self.tmp / "missing.md")):
            with mock.patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as stop:
                run(["reply", "--thread", "T1", "--body-file", path], gh)
            self.assertEqual(stop.exception.code, 2)
        self.assertEqual(gh.replies, [])

    def test_body_from_stdin(self):
        gh = FakeGh(threads={"T1": thread("T1")})
        with mock.patch("sys.stdin", io.StringIO("From stdin.\n")):
            code, _ = run(["reply", "--thread", "T1", "--body-file", "-"], gh)
        self.assertEqual((code, gh.replies), (0, [("T1", "From stdin.")]))


FAKE_GH = textwrap.dedent('''\
    #!/usr/bin/python3
    import json, os, sys
    args = sys.argv[1:]
    with open(os.environ["FAKE_GH_LOG"], "a") as log:
        log.write(json.dumps(args) + "\\n")
    query = next((a[6:] for a in args if a.startswith("query=")), "")
    def author(kind, login):
        return {"__typename": kind, "login": login}
    def node(tid, kind, login):
        return {"id": tid, "isResolved": False, "path": "a.rb", "line": 3,
                "comments": {"nodes": [{"url": "u/" + tid, "body": "Fix it", "author": author(kind, login)}]}}
    if "addPullRequestReviewThreadReply" in query:
        print(json.dumps({"data": {"addPullRequestReviewThreadReply": {"comment": {"url": "u/reply"}}}}))
    elif "resolveReviewThread" in query:
        print(json.dumps({"data": {"resolveReviewThread": {"thread": {"id": "T1", "isResolved": True}}}}))
    elif "node(id" in query:
        tid = next(a[3:] for a in args if a.startswith("id="))
        kind, login = ("Bot", "rabbit") if tid == "T1" else ("User", "ann")
        print(json.dumps({"data": {"node": dict(node(tid, kind, login), __typename="PullRequestReviewThread",
                                                pullRequest={"number": 5})}}))
    else:
        empty = {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []}
        threads = dict(empty, nodes=[node("T1", "Bot", "rabbit"), node("T2", "User", "ann")])
        pr = {"state": "OPEN", "headRefOid": "abc", "reviews": empty, "reviewThreads": threads,
              "commits": {"nodes": [{"commit": {"oid": "abc", "statusCheckRollup": None}}]}}
        print(json.dumps({"data": {"repository": {"pullRequest": pr}}}))
''')


class CliTest(unittest.TestCase):
    """The script as a process, with a fake `gh` first on PATH."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        fake = self.tmp / "gh"
        fake.write_text(FAKE_GH)
        fake.chmod(0o755)
        self.log = self.tmp / "calls.log"
        self.env = dict(os.environ, PATH=f"{self.tmp}:/usr/bin:/bin", FAKE_GH_LOG=str(self.log),
                        PYTHONDONTWRITEBYTECODE="1")

    def cli(self, *args):
        done = subprocess.run(["/usr/bin/python3", "-I", str(SCRIPT), *args], capture_output=True, text=True,
                              env=self.env, cwd=self.tmp)
        return done.returncode, done.stdout.splitlines()

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_list_then_resolve_end_to_end(self):
        code, lines = self.cli("list", "--pr", "5", "--repo", "o/r")
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["#5 T1 bot rabbit a.rb:3 u/T1 | Fix it", "#5 T2 human ann a.rb:3 u/T2 | Fix it",
                                 "2 unresolved: 1 bot, 1 human"])

        code, lines = self.cli("resolve", "--thread", "T1", "T2")
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["RESOLVED T1", "REFUSED: T2 human thread (ann), the user resolves it"])
        mutations = [c for c in self.calls() if any("resolveReviewThread" in a for a in c)]
        self.assertEqual(len(mutations), 1)
        self.assertIn("id=T1", mutations[0])

    def test_reply_end_to_end_bot_only(self):
        body = self.tmp / "reply.md"
        body.write_text("No change needed: a.rb:3")
        code, lines = self.cli("reply", "--thread", "T1", "--body-file", str(body))
        self.assertEqual((code, lines), (0, ["REPLIED T1 u/reply", "RESOLVED T1"]))
        code, lines = self.cli("reply", "--thread", "T2", "--body-file", str(body))
        self.assertEqual((code, lines), (1, ["REFUSED: T2 human thread (ann), the user replies"]))
        writes = [c for c in self.calls() if any("mutation" in a for a in c)]
        self.assertEqual(len(writes), 2)
        self.assertIn("body=No change needed: a.rb:3", writes[0])
        self.assertTrue(all("id=T1" in c for c in writes))

    def test_help_and_bad_usage(self):
        code, lines = self.cli("--help")
        self.assertEqual(code, 0)
        self.assertEqual(self.cli("resolve")[0], 2)
        self.assertEqual(self.cli("reply", "--thread", "T1")[0], 2)
        self.assertFalse(self.log.exists())


class SkillTextTest(unittest.TestCase):
    """The skill holds no raw thread mutation and no reference to parts nobody writes."""

    def texts(self):
        skill = SCRIPT.parent.parent
        return {path.name: path.read_text() for path in [skill / "SKILL.md", *sorted((skill / "resources").glob("*.md"))]}

    def test_no_raw_graphql(self):
        for name, text in self.texts().items():
            self.assertNotIn("resolveReviewThread", text, name)
            self.assertNotIn("gh api graphql", text, name)

    def test_FR_APE_01_no_milestone_spec_no_surprises_section_no_findings_table(self):
        for name, text in self.texts().items():
            for phrase in ("milestone spec", "Surprises", "findings table"):
                self.assertNotIn(phrase, text, f"{name}: {phrase}")

    def test_FR_APE_06_the_watcher_is_armed_until_bots(self):
        self.assertIn("--until bots", self.texts()["SKILL.md"])
        self.assertIn("BOTS DONE", self.texts()["SKILL.md"])

    def test_FR_APE_15_bot_replies_are_posted_by_the_script(self):
        texts = self.texts()
        self.assertIn("review_threads.py reply", texts["SKILL.md"])
        self.assertIn("review_threads.py reply", texts["review-pass.md"])
        for name, text in texts.items():
            self.assertNotIn("waits for the user", text, name)


if __name__ == "__main__":
    unittest.main()
