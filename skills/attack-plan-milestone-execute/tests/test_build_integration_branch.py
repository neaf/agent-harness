"""build_integration_branch.py against throwaway repositories: a bare remote and a clone, no user config."""
import io, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from build_integration_branch import BuildIntegrationBranch, main  # noqa: E402
from git import Git  # noqa: E402  (build_integration_branch put harness-common/scripts on the path)

# No global or system git config: the user's signing, hooks or aliases never reach a test repository.
# No automatic gc or maintenance either: a background run races the folder's removal in tearDown.
ISOLATED = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "gc.auto", "GIT_CONFIG_VALUE_0": "0",
            "GIT_CONFIG_KEY_1": "maintenance.auto", "GIT_CONFIG_VALUE_1": "false"}


class BuildIntegrationBranchTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, ISOLATED)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tmp = Path(tempfile.mkdtemp())
        self.remote = self.tmp / "remote.git"
        self.clone = self.tmp / "clone"
        self.out = io.StringIO()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "master", str(self.remote)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.clone)], check=True, capture_output=True)
        self.sh("config", "user.email", "spec@example.com")
        self.sh("config", "user.name", "Spec")
        self.sh("checkout", "-q", "-b", "master")
        (self.clone / "base.txt").write_text("base\n")
        self.sh("add", "base.txt")
        self.sh("commit", "-q", "-m", "Base")
        self.sh("push", "-q", "origin", "master")
        self.commit_on("backend", "backend.txt", "backend\n")
        self.commit_on("frontend", "frontend.txt", "frontend\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", "-C", str(cwd or self.clone), *args], capture_output=True, text=True)

    def sh(self, *args, cwd=None):
        done = self.git(*args, cwd=cwd)
        if done.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {done.stdout}{done.stderr}")
        return done.stdout

    def commit_on(self, branch, file, content, base="master"):
        self.sh("checkout", "-q", "-B", branch, f"origin/{base}")
        (self.clone / file).write_text(content)
        self.sh("add", file)
        self.sh("commit", "-q", "-m", f"Add {file}")
        self.sh("push", "-q", "origin", f"{branch}:{branch}")

    def build(self, repo=None, **options):
        return BuildIntegrationBranch(target="qa", repo=str(repo or self.clone), out=self.out, **options).run()

    def remote_sha(self, ref="qa"):
        return self.sh("rev-parse", ref, cwd=self.remote).strip()

    def remote_file(self, ref, file):
        return self.sh("show", f"{ref}:{file}", cwd=self.remote)

    def last_event(self):
        lines = [line for line in self.out.getvalue().splitlines() if line.startswith("INTEGRATION_BRANCH_EVENT ")]
        return json.loads(lines[-1].split(" ", 1)[1])

    def test_merges_every_head_onto_master_and_pushes_a_new_integration_branch(self):
        self.assertTrue(self.build(heads=["backend", "frontend"], push=True))

        self.assertEqual(self.remote_file("qa", "backend.txt"), "backend\n")
        self.assertEqual(self.remote_file("qa", "frontend.txt"), "frontend\n")
        self.assertEqual(len(self.sh("log", "--format=%P", "-1", "qa", cwd=self.remote).split()), 2)
        self.assertEqual(self.last_event()["status"], "pushed")
        self.assertEqual(self.last_event()["target"], "qa")

    def test_builds_without_pushing_by_default(self):
        self.assertTrue(self.build(heads=["backend"]))

        self.assertEqual(self.last_event()["status"], "built")
        self.assertNotEqual(self.git("rev-parse", "--verify", "-q", "qa", cwd=self.remote).returncode, 0)

    def test_updates_an_existing_integration_branch_with_a_fast_forward(self):
        self.build(heads=["backend", "frontend"], push=True)
        first = self.sh("rev-parse", "qa", cwd=self.remote).strip()
        self.sh("checkout", "-q", "backend")
        (self.clone / "backend.txt").write_text("backend v2\n")
        self.sh("commit", "-q", "-am", "Update backend")
        self.sh("push", "-q", "origin", "backend")

        self.assertTrue(self.build(heads=["backend"], push=True))

        self.assertEqual(self.remote_file("qa", "backend.txt"), "backend v2\n")
        self.assertEqual(self.git("merge-base", "--is-ancestor", first, "qa", cwd=self.remote).returncode, 0)

    def test_FR_APE_08_stops_on_a_conflict_and_pushes_nothing(self):
        self.commit_on("conflicting", "backend.txt", "other\n")

        self.assertFalse(self.build(heads=["backend", "conflicting"], push=True))

        self.assertEqual(self.last_event()["status"], "conflict")
        self.assertEqual(self.last_event()["error"], "CONFLICT merging conflicting")
        self.assertEqual(self.last_event()["head"], "conflicting")
        self.assertEqual(self.last_event()["files"], ["backend.txt"])
        self.assertIn("backend.txt", self.out.getvalue())
        self.assertNotEqual(self.git("rev-parse", "--verify", "-q", "qa", cwd=self.remote).returncode, 0)

    def test_refuses_to_start_from_a_target_that_does_not_exist(self):
        self.assertFalse(self.build(heads=["backend"], base="target"))

        self.assertIn("does not exist", self.last_event()["error"])

    def test_starts_from_a_named_base_branch_when_given(self):
        self.assertTrue(self.build(heads=["backend"], base="master", push=True))

        self.assertEqual(self.remote_file("qa", "backend.txt"), "backend\n")

    # FR-APE-08 fixes (Phase 9).

    def test_FR_APE_08_merging_a_head_already_in_the_target_adds_no_commit(self):
        self.assertTrue(self.build(heads=["backend"], push=True))
        first = self.remote_sha()

        self.assertTrue(self.build(heads=["backend"], push=True))

        self.assertEqual(self.remote_sha(), first)
        self.assertEqual(self.last_event(), {"status": "unchanged", "target": "qa", "sha": first})
        self.assertIn("skipped backend: already in", self.out.getvalue())

    def test_FR_APE_08_only_new_heads_add_a_commit(self):
        self.build(heads=["backend"], push=True)
        first = self.remote_sha()

        self.assertTrue(self.build(heads=["backend", "frontend"], push=True))

        self.assertEqual(self.sh("rev-parse", "qa~1", cwd=self.remote).strip(), first)
        self.assertEqual(self.last_event()["status"], "pushed")

    def test_FR_APE_08_a_head_already_in_the_default_branch_is_skipped(self):
        self.sh("push", "-q", "origin", "origin/backend:refs/heads/master")

        self.assertTrue(self.build(heads=["backend"]))

        self.assertEqual(self.last_event()["sha"], self.remote_sha("master"))
        self.assertEqual(self.last_event()["status"], "built")

    def test_FR_APE_08_a_git_failure_that_is_no_conflict_is_not_reported_as_one(self):
        self.sh("checkout", "-q", "--orphan", "unrelated")
        self.sh("rm", "-q", "-rf", ".")
        (self.clone / "other.txt").write_text("other\n")
        self.sh("add", "other.txt")
        self.sh("commit", "-q", "-m", "Unrelated root")
        self.sh("push", "-q", "origin", "unrelated")

        self.assertFalse(self.build(heads=["unrelated"]))

        self.assertEqual(self.last_event()["status"], "failed")
        self.assertNotIn("CONFLICT", self.last_event()["error"])
        self.assertIn("unrelated histories", self.last_event()["error"])

    def test_FR_APE_08_an_old_git_stops_before_any_fetch(self):
        calls = []

        def runner(args, cwd):
            calls.append(args)
            return 0, "git version 2.37.1 (Apple Git-137.1)\n", ""

        run = BuildIntegrationBranch(target="qa", heads=["backend"], out=self.out, git=Git(".", runner))
        self.assertFalse(run.run())

        self.assertEqual(calls, [["--version"]])
        self.assertEqual(self.last_event()["error"], "needs git 2.38 or later, found 2.37.1")

    def test_FR_APE_08_a_failed_target_lookup_is_not_read_as_absent(self):
        self.sh("remote", "set-url", "origin", str(self.tmp / "gone.git"))

        self.assertFalse(self.build(heads=["backend"], default="master"))

        self.assertEqual(self.last_event()["status"], "failed")
        self.assertIn("git ls-remote", self.last_event()["error"])
        self.assertNotIn("does not exist", self.last_event()["error"])

    def test_FR_APE_08_a_single_branch_clone_fetches_every_head(self):
        single = self.tmp / "single"
        subprocess.run(["git", "clone", "-q", "--single-branch", "-b", "master", str(self.remote), str(single)],
                       check=True, capture_output=True)
        self.sh("config", "user.email", "spec@example.com", cwd=single)
        self.sh("config", "user.name", "Spec", cwd=single)
        self.build(heads=["backend"], push=True)
        self.sh("checkout", "-q", "frontend")
        (self.clone / "frontend.txt").write_text("frontend v2\n")
        self.sh("commit", "-q", "-am", "Update frontend")
        self.sh("push", "-q", "origin", "frontend")

        self.assertTrue(self.build(repo=single, heads=["frontend"], push=True))

        self.assertEqual(self.remote_file("qa", "frontend.txt"), "frontend v2\n")
        self.assertEqual(self.remote_file("qa", "backend.txt"), "backend\n")

    def test_FR_APE_08_a_missing_identity_is_named(self):
        self.sh("config", "--unset", "user.email")
        self.sh("config", "--unset", "user.name")
        with mock.patch.dict(os.environ, {"GIT_AUTHOR_NAME": "", "GIT_AUTHOR_EMAIL": "", "EMAIL": "",
                                          "GIT_COMMITTER_NAME": "", "GIT_COMMITTER_EMAIL": ""}):
            for key in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
                del os.environ[key]
            ok = self.build(heads=["backend"])

        self.assertFalse(ok)
        self.assertEqual(self.last_event()["error"], "no git identity: set user.name and user.email (git config)")

    def test_cli_exit_codes(self):
        with mock.patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(main(["--target", "qa", "--heads", "backend", "--repo", str(self.clone)]), 0)
            self.assertEqual(main(["--target", "qa", "--heads", "backend", "--from", "target",
                                   "--repo", str(self.clone)]), 1)
        self.assertIn('"status": "built"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
