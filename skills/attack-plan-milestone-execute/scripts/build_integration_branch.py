#!/usr/bin/python3
"""Builds an integration branch from the heads of several branches, without a checkout.

Usage:
  build_integration_branch.py --target BRANCH --heads A,B,C [--from BASE] [--default BRANCH]
      [--message TEXT] [--push] [--repo PATH] [--remote NAME]

The first run starts from the default branch. Later runs merge the heads on top of the
existing target (--from target), so the push stays a fast-forward. A conflict stops the run
and pushes nothing. The last line of output is INTEGRATION_BRANCH_EVENT with a JSON payload.
Needs git 2.38 or later (merge-tree --write-tree).
"""
import argparse, json, subprocess, sys


class Failure(Exception):
    pass


class BuildIntegrationBranch:
    def __init__(self, target, heads, base=None, default=None, message=None, push=False,
                 repo=".", remote="origin", out=sys.stdout):
        self.target = target
        self.heads = heads
        self.base = base
        self.default = default
        self.message = message
        self.push = push
        self.repo = repo
        self.remote = remote
        self.out = out
        self.target_exists = False

    def run(self):
        try:
            self.fetch()
            current = self.base_commit()
            self.say(f"base {self.base_name()} {short(current)}")
            for head in self.heads:
                current = self.merge(current, head)
            self.publish(current)
            self.event(status="pushed" if self.push else "built", target=self.target, sha=current)
            return True
        except Failure as error:
            self.say(str(error))
            self.event(status="failed", target=self.target, error=str(error).splitlines()[0].strip())
            return False

    def fetch(self):
        if self.default is None:
            self.default = self.detect_default()
        branches = [self.default, *self.heads]
        if self.base not in (None, "target", self.default):
            branches.append(self.base)
        self.git_or_fail("fetch", "-q", self.remote, *dict.fromkeys(branches))
        self.target_exists = self.git("fetch", "-q", self.remote, self.target)[1] == 0

    def detect_default(self):
        output, code = self.git("ls-remote", "--symref", self.remote, "HEAD")
        for line in output.splitlines():
            if code == 0 and line.startswith("ref: refs/heads/"):
                return line[len("ref: refs/heads/"):].split()[0]
        raise Failure(f"cannot read the default branch of {self.remote}: pass --default")

    def base_name(self):
        return self.base or ("target" if self.target_exists else self.default)

    def base_commit(self):
        name = self.base_name()
        if name == "target":
            if not self.target_exists:
                raise Failure(f"{self.target} does not exist on {self.remote}: use --from {self.default}")
            return self.rev(f"{self.remote}/{self.target}")
        return self.rev(f"{self.remote}/{name}")

    def merge(self, current, head):
        other = self.rev(f"{self.remote}/{head}")
        output, code = self.git("merge-tree", "--write-tree", "--name-only", current, other)
        if code != 0:
            raise Failure(f"CONFLICT merging {head}\n{output}")
        tree = output.splitlines()[0].strip()
        commit = self.git_or_fail("commit-tree", tree, "-p", current, "-p", other,
                                  "-m", self.merge_message(head)).strip()
        self.say(f"merged {head} -> {short(commit)}")
        return commit

    def merge_message(self, head):
        return ": ".join(part for part in (self.message, f"Merge {head}") if part)

    def publish(self, commit):
        if not self.push:
            self.say(f"built {short(commit)}, not pushed (pass --push to update {self.target})")
            return
        self.git_or_fail("push", "-q", self.remote, f"{commit}:refs/heads/{self.target}")
        self.say(f"pushed {self.target} at {short(commit)}")

    def rev(self, ref):
        return self.git_or_fail("rev-parse", ref).strip()

    def git(self, *args):
        done = subprocess.run(["git", "-C", self.repo, *args], capture_output=True, text=True)
        return done.stdout + done.stderr, done.returncode

    def git_or_fail(self, *args):
        output, code = self.git(*args)
        if code != 0:
            raise Failure(f"git {args[0]} failed: {output}")
        return output

    def say(self, line):
        print(line, file=self.out)

    def event(self, **payload):
        self.say(f"INTEGRATION_BRANCH_EVENT {json.dumps(payload)}")


def short(sha):
    return sha[:12]


def split_list(value):
    return [item for item in value.split(",") if item]


def main(argv):
    parser = argparse.ArgumentParser(description="Build or update an integration branch from branch heads, without a checkout.")
    parser.add_argument("--target", required=True, help="integration branch to build or update")
    parser.add_argument("--heads", required=True, type=split_list, help="comma-separated branches to merge, in order")
    parser.add_argument("--from", dest="base", help="default branch name, or target to merge on top of the integration branch (default: target when it exists, else the default branch)")
    parser.add_argument("--default", help="default branch of the remote (default: read from the remote)")
    parser.add_argument("--message", help="prefix for the merge commit messages")
    parser.add_argument("--push", action="store_true", help="push the result (plain push, never forced)")
    parser.add_argument("--repo", default=".", help="repository path (default: current folder)")
    parser.add_argument("--remote", default="origin", help="remote name (default: origin)")
    options = parser.parse_args(argv)
    if not options.heads:
        parser.error("--heads needs at least one branch")
    run = BuildIntegrationBranch(target=options.target, heads=options.heads, base=options.base,
                                 default=options.default, message=options.message, push=options.push,
                                 repo=options.repo, remote=options.remote)
    return 0 if run.run() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
