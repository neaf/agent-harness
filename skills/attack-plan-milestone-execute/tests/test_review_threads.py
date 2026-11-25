"""review_threads.py: list with bot or human, resolve refuses human threads (Q17). gh is a fake, never GitHub."""
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
        self.resolved, self.repo_calls = [], 0

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

    def resolve_thread(self, thread_id):
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
    def test_Q17_resolves_bot_threads_only(self):
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
    if "resolveReviewThread" in query:
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

    def test_help_and_bad_usage(self):
        code, lines = self.cli("--help")
        self.assertEqual(code, 0)
        self.assertEqual(self.cli("resolve")[0], 2)
        self.assertFalse(self.log.exists())


class SkillTextTest(unittest.TestCase):
    """Phase 9 exit: the skill holds no raw thread mutation and no reference to parts nobody writes."""

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

if __name__ == "__main__":
    unittest.main()
