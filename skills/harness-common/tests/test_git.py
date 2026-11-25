"""git.py: the runner, version gate, remote branches and merges, in throwaway repositories and with a fake runner."""
import os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import git  # noqa: E402
from git import Conflict, Git, GitError  # noqa: E402

ISOLATED = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "gc.auto", "GIT_CONFIG_VALUE_0": "0",
            "GIT_CONFIG_KEY_1": "maintenance.auto", "GIT_CONFIG_VALUE_1": "false"}


class Fake:
    """runner(args, cwd) -> (code, stdout, stderr) from a list of answers."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def __call__(self, args, cwd):
        self.calls.append(args)
        return self.answers.pop(0)


class FakeRunnerTest(unittest.TestCase):
    def test_version_reads_apple_and_plain_builds(self):
        self.assertEqual(Git(".", Fake((0, "git version 2.39.5 (Apple Git-154)\n", ""))).version(), (2, 39, 5))
        self.assertEqual(Git(".", Fake((0, "git version 2.38\n", ""))).version(), (2, 38, 0))

    def test_require_names_both_versions(self):
        with self.assertRaisesRegex(GitError, "^needs git 2.38 or later, found 2.37.1$"):
            Git(".", Fake((0, "git version 2.37.1\n", ""))).require(2, 38)
        Git(".", Fake((0, "git version 2.38.0\n", ""))).require(2, 38)

    def test_a_failure_names_the_command_and_the_cause_line(self):
        fake = Fake((128, "", "fatal: refusing to merge unrelated histories\n"))
        with self.assertRaisesRegex(GitError, "^git merge-tree: refusing to merge unrelated histories$"):
            Git(".", fake).merge_tree("a", "b")

    def test_a_rejected_push_names_the_rejection(self):
        err = "To /tmp/remote.git\n ! [rejected]        abc -> qa (non-fast-forward)\nerror: failed to push\n"
        with self.assertRaisesRegex(GitError, r"^git push: ! \[rejected\]"):
            Git(".", Fake((1, "", err))).push("origin", "abc", "qa")

    def test_conflict_carries_files_and_messages_and_is_no_git_error(self):
        out = "4b825dc\nbackend.txt\nfront.txt\n\nAuto-merging backend.txt\nCONFLICT (content): backend.txt\n"
        with self.assertRaises(Conflict) as caught:
            Git(".", Fake((1, out, ""))).merge_tree("a", "b")
        self.assertEqual(caught.exception.files, ["backend.txt", "front.txt"])
        self.assertEqual(caught.exception.messages[1], "CONFLICT (content): backend.txt")
        self.assertFalse(issubclass(Conflict, GitError))

    def test_a_conflict_without_conflicted_files(self):
        with self.assertRaises(Conflict) as caught:
            Git(".", Fake((1, "4b825dc\n\nCONFLICT (rename/rename): a renamed to b and c\n", ""))).merge_tree("a", "b")
        self.assertEqual(caught.exception.files, [])
        self.assertEqual(str(caught.exception), "a conflict with no conflicted file")

    def test_fetch_uses_one_explicit_refspec_per_branch(self):
        fake = Fake((0, "", ""))
        Git(".", fake).fetch("origin", "master", "a", "master")
        self.assertEqual(fake.calls[0], ["fetch", "-q", "origin", "+refs/heads/master:refs/remotes/origin/master",
                                         "+refs/heads/a:refs/remotes/origin/a"])

    def test_remote_has_raises_instead_of_answering_no(self):
        with self.assertRaisesRegex(GitError, "^git ls-remote: Could not read from remote repository.$"):
            Git(".", Fake((128, "", "fatal: Could not read from remote repository.\n"))).remote_has("origin", "qa")

    def test_require_identity(self):
        with self.assertRaisesRegex(GitError, "no git identity"):
            Git(".", Fake((0, "A <a@b> 1 +0000\n", ""), (128, "", "fatal: no email\n"))).require_identity()

    def test_runner_never_prompts(self):
        done = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(git.subprocess, "run", return_value=done) as call:
            self.assertEqual(git.run(["status"], cwd="/x"), (0, "ok", ""))
        self.assertEqual(call.call_args[0][0], ["git", "-C", "/x", "status"])
        self.assertIs(call.call_args[1]["stdin"], git.subprocess.DEVNULL)
        self.assertEqual(call.call_args[1]["env"]["GIT_TERMINAL_PROMPT"], "0")

    def test_runner_timeout(self):
        with mock.patch.object(git.subprocess, "run", side_effect=git.subprocess.TimeoutExpired("git", 300)):
            with self.assertRaisesRegex(GitError, "^git fetch timed out after 300 s$"):
                git.run(["fetch"])


class RepositoryTest(unittest.TestCase):
    """A bare remote and a clone under mktemp -d, no global or system config."""

    def setUp(self):
        patcher = mock.patch.dict(os.environ, ISOLATED)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.remote, self.clone = self.tmp / "remote.git", self.tmp / "clone"
        self.sh("init", "-q", "--bare", "-b", "main", str(self.remote), cwd=self.tmp)
        self.sh("clone", "-q", str(self.remote), str(self.clone), cwd=self.tmp)
        self.sh("config", "user.email", "spec@example.com")
        self.sh("config", "user.name", "Spec")
        self.sh("checkout", "-q", "-b", "main")
        self.base = self.commit("base.txt", "base\n")
        self.sh("push", "-q", "origin", "main")
        self.git = Git(self.clone)

    def sh(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.clone, check=True, capture_output=True,
                              text=True).stdout.strip()

    def commit(self, name, text, branch=None):
        if branch:
            self.sh("checkout", "-q", "-B", branch, "main")
        (self.clone / name).write_text(text)
        self.sh("add", name)
        self.sh("commit", "-q", "-m", f"Add {name}")
        return self.sh("rev-parse", "HEAD")

    def test_version_of_the_real_git(self):
        self.assertGreaterEqual(self.git.version(), (2, 38, 0))

    def test_remote_branches_and_default(self):
        self.assertTrue(self.git.remote_has("origin", "main"))
        self.assertFalse(self.git.remote_has("origin", "qa"))
        self.assertEqual(self.git.default_branch("origin"), "main")

    def test_fetch_creates_the_tracking_ref_in_a_single_branch_clone(self):
        self.commit("a.txt", "a\n", branch="a")
        self.sh("push", "-q", "origin", "a")
        single = self.tmp / "single"
        self.sh("clone", "-q", "--single-branch", "-b", "main", str(self.remote), str(single), cwd=self.tmp)
        self.sh("fetch", "-q", "origin", "a", cwd=single)
        with self.assertRaises(GitError):
            Git(single).rev("origin/a")  # the quirk in git.md

        Git(single).fetch("origin", "a")

        self.assertEqual(Git(single).rev("origin/a"), self.sh("rev-parse", "a"))

    def test_merge_tree_commit_tree_and_ancestry(self):
        a = self.commit("a.txt", "a\n", branch="a")
        b = self.commit("b.txt", "b\n", branch="b")
        tree = self.git.merge_tree(a, b)
        merged = self.git.commit_tree(tree, [a, b], "Merge b")

        self.assertEqual(self.git.tree_of(merged), tree)
        self.assertTrue(self.git.is_ancestor(a, merged))
        self.assertTrue(self.git.is_ancestor(merged, merged))
        self.assertFalse(self.git.is_ancestor(merged, a))
        self.assertEqual(self.sh("show", f"{merged}:b.txt"), "b")

    def test_real_conflict(self):
        a = self.commit("base.txt", "a\n", branch="a")
        b = self.commit("base.txt", "b\n", branch="b")
        with self.assertRaises(Conflict) as caught:
            self.git.merge_tree(a, b)
        self.assertEqual(caught.exception.files, ["base.txt"])
        self.assertTrue(any("CONFLICT" in line for line in caught.exception.messages))

    def test_missing_ref_is_named(self):
        with self.assertRaisesRegex(GitError, "^no commit origin/nope$"):
            self.git.rev("origin/nope")

    def test_identity_from_repo_config(self):
        self.git.require_identity()

    def test_push_is_never_forced(self):
        other = self.commit("x.txt", "x\n", branch="x")
        self.git.push("origin", other, "qa")
        with self.assertRaisesRegex(GitError, r"rejected"):
            self.git.push("origin", self.base, "qa")
        self.assertEqual(self.sh("rev-parse", "qa", cwd=self.remote), other)


if __name__ == "__main__":
    unittest.main()
