#!/usr/bin/python3
"""Prints one line per state change of GitHub pull requests or of local checks.

Usage:
  watch.py pr <number> [<number> ...] [--repo OWNER/NAME] [--reviewer LOGIN ...]
            [--interval SECONDS] [--until all|ci] [--timeout MINUTES]
            [--allow-no-checks] [--once]
  watch.py local --cmd COMMAND [--cmd COMMAND ...] [--path PATH ...]
            [--interval SECONDS] [--debounce SECONDS] [--once]

The last line says why it stopped: ALL DONE, CI DONE, NOT DONE (pr --once),
TIMEOUT (pr, exit 3), ALL PASS or FAILED (local --once).
"""
import argparse, json, os, re, subprocess, sys, time

SKIP_DIRS = {
    ".git", ".ai-notes", ".venv", "venv", "node_modules", "__pycache__", ".tox", ".mypy_cache",
    ".pytest_cache", ".gradle", ".idea", ".next", ".dart_tool", "build", "dist", "target",
    "coverage", "DerivedData", "Pods",
}
FAILING_CONCLUSIONS = {"FAILURE", "TIMED_OUT", "STARTUP_FAILURE"}
FAILING_STATES = {"FAILURE", "ERROR"}
PENDING_STATES = {"PENDING", "EXPECTED"}
THREADS_QUERY = (
    "query($owner: String!, $name: String!, $number: Int!) { repository(owner: $owner, name: $name) {"
    " pullRequest(number: $number) { reviewThreads(first: 100) { nodes { isResolved } } } } }"
)
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
TAIL_LINES = 15
LABEL_WIDTH = 70


class GhError(Exception):
    pass


def first_line(text):
    lines = (text or "").strip().splitlines()
    return lines[0] if lines else ""


def is_check_run(item):
    return "status" in item or "conclusion" in item


def item_name(item):
    return item.get("name") or item.get("context")


def latest_checks(rollup):
    """One entry per check: its newest run. Cancelled runs are superseded duplicates and are dropped."""
    newest = {}
    for item in rollup:
        if item.get("conclusion") == "CANCELLED":
            continue
        key = (item.get("workflowName"), item_name(item))
        stamp = item.get("startedAt") or item.get("createdAt") or ""
        if key not in newest or stamp >= newest[key][0]:
            newest[key] = (stamp, item)
    return [item for _, item in newest.values()]


def checks(rollup):
    """Returns (pending, failing): whether a check still runs, and the sorted names of the failing ones."""
    pending, failing = False, set()
    for item in latest_checks(rollup):
        if is_check_run(item):
            if item.get("status") != "COMPLETED":
                pending = True
            elif item.get("conclusion") in FAILING_CONCLUSIONS:
                failing.add(item_name(item))
        elif item.get("state") in PENDING_STATES:
            pending = True
        elif item.get("state") in FAILING_STATES:
            failing.add(item_name(item))
    return pending, sorted(failing)


def normalize_login(login):
    login = (login or "").lower()
    return login[: -len("[bot]")] if login.endswith("[bot]") else login


def pr_state(view, reviews, threads, reviewers, allow_no_checks=False):
    head = view["headRefOid"]
    rollup = view.get("statusCheckRollup") or []
    pending, failing = checks(rollup)
    pending = pending or (not rollup and not allow_no_checks)
    reviewed = {
        normalize_login((review.get("user") or {}).get("login"))
        for review in reviews if review.get("commit_id") == head
    }
    return {
        "sha": head[:7],
        "pending": pending,
        "failing": failing,
        "missing": [login for login in reviewers if normalize_login(login) not in reviewed],
        "unresolved": sum(1 for thread in threads if not thread["isResolved"]),
    }


def is_done(state, until="all"):
    if state["pending"]:
        return False
    if until == "ci":
        return True
    return not (state["failing"] or state["missing"] or state["unresolved"])


def format_pr(number, state, reviewers):
    parts = [
        f"#{number} {state['sha']}",
        "CI running" if state["pending"] else "CI done",
        "failing: " + (", ".join(state["failing"]) or "none"),
    ]
    if reviewers:
        if state["missing"]:
            parts.append("waiting for review: " + ", ".join(state["missing"]))
        else:
            parts.append("reviewed")
    parts.append(f"unresolved threads: {state['unresolved']}")
    return " | ".join(parts)


def report_changes(previous, current, reviewers):
    lines = [format_pr(number, state, reviewers) for number, state in current.items() if previous.get(number) != state]
    return {**previous, **current}, lines


def run_gh(args):
    try:
        done = subprocess.run(args, capture_output=True, text=True)
    except OSError as error:
        return 1, "", str(error)
    return done.returncode, done.stdout, done.stderr


def gh(runner, args):
    code, out, err = runner(["gh", *args])
    if code:
        raise GhError(first_line(err) or f"gh exited with {code}")
    return out


def resolve_repo(runner):
    return gh(runner, ["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]).strip()


def fetch_pr(runner, repo, number, reviewers, allow_no_checks=False):
    owner, name = repo.split("/", 1)
    view = json.loads(gh(runner, ["pr", "view", str(number), "-R", repo, "--json", "headRefOid,statusCheckRollup"]))
    reviews = json.loads(gh(runner, ["api", f"repos/{repo}/pulls/{number}/reviews?per_page=100"]))
    graph = json.loads(gh(runner, [
        "api", "graphql", "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"number={number}",
        "-f", f"query={THREADS_QUERY}",
    ]))
    threads = graph["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    return pr_state(view, reviews, threads, reviewers, allow_no_checks)


def run_pr(numbers, repo, reviewers, until, interval, timeout, allow_no_checks, once, runner, sleep, clock, emit):
    previous, started = {}, clock()
    while True:
        current = {}
        for number in numbers:
            try:
                current[number] = fetch_pr(runner, repo, number, reviewers, allow_no_checks)
            except (GhError, ValueError, KeyError, TypeError) as error:
                print(f"skipped #{number} this round: {error}", file=sys.stderr)
        previous, lines = report_changes(previous, current, reviewers)
        for line in lines:
            emit(line)
        if len(current) == len(numbers) and all(is_done(current[number], until) for number in numbers):
            emit("CI DONE" if until == "ci" else "ALL DONE")
            return 0
        if once:
            emit("NOT DONE")
            return 1
        if timeout and clock() - started >= timeout:
            emit("TIMEOUT")
            return 3
        sleep(interval)


def run_shell(command):
    done = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
    )
    return done.returncode, done.stdout


def run_commands(commands, runner):
    return [(command, *runner(command)) for command in commands]


def label(command):
    return command if len(command) <= LABEL_WIDTH else command[: LABEL_WIDTH - 3] + "..."


def tail(output, lines=TAIL_LINES):
    return ANSI.sub("", output).rstrip().splitlines()[-lines:]


def report_results(previous, results):
    """results: (command, exit code, output) per command. previous: command -> passed. Lines only on change."""
    lines = []
    for command, code, output in results:
        passed = code == 0
        if previous.get(command) != passed:
            if passed:
                lines.append(f"PASS {label(command)}")
            else:
                lines.append(f"FAIL {label(command)} (exit {code})")
                lines.extend("    " + line for line in tail(output))
    return {**previous, **{command: code == 0 for command, code, _ in results}}, lines


def walk_files(root):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def snapshot(roots):
    files = {}
    for root in roots:
        for path in walk_files(root):
            try:
                stat = os.stat(path)
            except OSError:
                continue
            files[path] = (stat.st_mtime_ns, stat.st_size)
    return files


class Trigger:
    """Says when a run is due: files changed since the last run, and quiet for `delay` seconds."""

    def __init__(self, delay, initial):
        self.delay, self.ran_on, self.seen, self.changed_at = delay, initial, initial, None

    def observe(self, current, now):
        if current != self.seen:
            self.seen, self.changed_at = current, now
        if self.changed_at is not None and now - self.changed_at >= self.delay and self.seen != self.ran_on:
            self.ran_on, self.changed_at = self.seen, None
            return True
        return False


def run_local(commands, roots, interval, debounce, once, runner, sleep, clock, emit):
    if once:
        results = run_commands(commands, runner)
        _, lines = report_results({}, results)
        for line in lines:
            emit(line)
        failed = [label(command) for command, code, _ in results if code]
        emit("ALL PASS" if not failed else "FAILED: " + ", ".join(failed))
        return 1 if failed else 0
    trigger = Trigger(debounce, snapshot(roots))
    previous, lines = report_results({}, run_commands(commands, runner))
    for line in lines:
        emit(line)
    while True:
        sleep(interval)
        if trigger.observe(snapshot(roots), clock()):
            previous, lines = report_results(previous, run_commands(commands, runner))
            for line in lines:
                emit(line)


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = ap.add_subparsers(dest="mode", required=True)
    pr = modes.add_parser("pr", help="watch GitHub pull requests")
    pr.add_argument("numbers", nargs="+", type=int)
    pr.add_argument("--repo", help="OWNER/NAME; default: the repository of the current folder")
    pr.add_argument("--reviewer", action="append", default=[], dest="reviewers",
                    help="login whose review must cover the head commit (repeatable)")
    pr.add_argument("--interval", type=float, default=120, help="seconds between polls")
    pr.add_argument("--until", choices=("all", "ci"), default="all", help="ci: stop when CI is done")
    pr.add_argument("--timeout", type=float, default=0, help="minutes before TIMEOUT; 0 means no limit")
    pr.add_argument("--allow-no-checks", action="store_true", help="a PR with no checks at all counts as done")
    pr.add_argument("--once", action="store_true", help="one round, then exit")
    local = modes.add_parser("local", help="rerun commands when files change")
    local.add_argument("--cmd", action="append", required=True, dest="commands", help="shell command (repeatable)")
    local.add_argument("--path", action="append", dest="paths", help="folder or file to watch (default: .)")
    local.add_argument("--interval", type=float, default=2, help="seconds between scans")
    local.add_argument("--debounce", type=float, default=1, help="quiet seconds before a rerun")
    local.add_argument("--once", action="store_true", help="run once, then exit with the combined status")
    return ap


def emit(line):
    print(line, flush=True)


def main(argv=None):
    args = parser().parse_args(argv)
    if args.mode == "pr":
        try:
            repo = args.repo or resolve_repo(run_gh)
        except GhError as error:
            sys.exit(f"cannot resolve the repository: {error}")
        return run_pr(args.numbers, repo, args.reviewers, args.until, args.interval, args.timeout * 60,
                      args.allow_no_checks, args.once, run_gh, time.sleep, time.monotonic, emit)
    roots = [os.path.abspath(path) for path in args.paths or ["."]]
    return run_local(args.commands, roots, args.interval, args.debounce, args.once, run_shell,
                     time.sleep, time.monotonic, emit)


if __name__ == "__main__":
    sys.exit(main())
