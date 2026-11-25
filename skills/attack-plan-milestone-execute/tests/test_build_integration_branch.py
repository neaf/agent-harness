import io, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_integration_branch import BuildIntegrationBranch  # noqa: E402


class BuildIntegrationBranchTest(unittest.TestCase):
    def setUp(self):
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

    def build(self, **options):
        return BuildIntegrationBranch(target="qa", repo=str(self.clone), out=self.out, **options).run()

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

    def test_stops_on_a_conflict_and_pushes_nothing(self):
        self.commit_on("conflicting", "backend.txt", "other\n")

        self.assertFalse(self.build(heads=["backend", "conflicting"], push=True))

        self.assertEqual(self.last_event()["status"], "failed")
        self.assertEqual(self.last_event()["error"], "CONFLICT merging conflicting")
        self.assertIn("backend.txt", self.out.getvalue())
        self.assertNotEqual(self.git("rev-parse", "--verify", "-q", "qa", cwd=self.remote).returncode, 0)

    def test_refuses_to_start_from_a_target_that_does_not_exist(self):
        self.assertFalse(self.build(heads=["backend"], base="target"))

        self.assertIn("does not exist", self.last_event()["error"])

    def test_starts_from_a_named_base_branch_when_given(self):
        self.assertTrue(self.build(heads=["backend"], base="master", push=True))

        self.assertEqual(self.remote_file("qa", "backend.txt"), "backend\n")

    # Known defects (FR-APE-08). Phase 9 fixes each and removes its marker.

    @unittest.expectedFailure
    def test_FR_APE_08_merging_a_head_already_in_the_target_adds_no_commit(self):
        self.assertTrue(self.build(heads=["backend"], push=True))
        first = self.sh("rev-parse", "qa", cwd=self.remote).strip()

        self.assertTrue(self.build(heads=["backend"], push=True))

        self.assertEqual(self.sh("rev-parse", "qa", cwd=self.remote).strip(), first)

    @unittest.expectedFailure
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


if __name__ == "__main__":
    unittest.main()
