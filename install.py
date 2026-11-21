#!/usr/bin/python3
"""Projects the harness into the global config of Claude Code and opencode.

Skills are symlinked. Agents are generated from agents/*.md with the model
tier mapped through targets/models.json. Instructions are copied.
Usage: install.py [--check] [--claude 0|1] [--opencode 0|1]
"""
import argparse, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
CLAUDE = HOME / ".claude"
OPENCODE = HOME / ".config" / "opencode"


def parse(path):
    text = path.read_text()
    _, head, body = text.split("---\n", 2)
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
    return meta, body.lstrip("\n")


def render_claude(meta, body, models):
    model = models["claude"][meta["tier"]]
    return (f"---\nname: {meta['name']}\ndescription: {meta['description']}\n"
            f"model: {model}\ntools: {meta['tools']}\n---\n\n{body}")


def render_opencode(meta, body, models):
    model = models["opencode"][meta["tier"]]
    lines = [f"description: {meta['description']}", "mode: subagent"]
    if model:
        lines.append(f"model: {model}")
    return "---\n" + "\n".join(lines) + "\n---\n\n" + body


def targets(models):
    """Yields (destination, content) for generated files and (destination, source) for links."""
    files, links = {}, {}
    for f in sorted((ROOT / "agents").glob("*.md")):
        meta, body = parse(f)
        files[CLAUDE / "agents" / f.name] = render_claude(meta, body, models)
        files[OPENCODE / "agents" / f.name] = render_opencode(meta, body, models)
    glob = (ROOT / "instructions" / "global.md").read_text()
    files[CLAUDE / "CLAUDE.md"] = glob
    files[OPENCODE / "AGENTS.md"] = glob
    for d in sorted((ROOT / "skills").iterdir()):
        if d.is_dir():
            links[CLAUDE / "skills" / d.name] = d
            links[OPENCODE / "skills" / d.name] = d
    return files, links


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report drift, write nothing")
    ap.add_argument("--claude", type=int, choices=(0, 1))
    ap.add_argument("--opencode", type=int, choices=(0, 1))
    ap.add_argument("--yes", action="store_true", help="replace existing files and folders without asking")
    a = ap.parse_args()
    use = {
        CLAUDE: a.claude if a.claude is not None else int(CLAUDE.exists() or bool(shutil.which("claude"))),
        OPENCODE: a.opencode if a.opencode is not None else int(OPENCODE.exists() or bool(shutil.which("opencode"))),
    }
    models = json.loads((ROOT / "targets" / "models.json").read_text())
    files, links = targets(models)
    plan = []
    for dest, content in files.items():
        base = CLAUDE if CLAUDE in dest.parents else OPENCODE
        if use[base] and not (dest.exists() and dest.read_text() == content):
            plan.append(("write", dest, content))
    for dest, src in links.items():
        base = CLAUDE if CLAUDE in dest.parents else OPENCODE
        if use[base] and not (dest.is_symlink() and dest.resolve() == src.resolve()):
            plan.append(("link", dest, src))
    replaced = [dest for _, dest, _ in plan if dest.exists() or dest.is_symlink()]
    for kind, dest, payload in plan:
        verb = "replace" if dest in replaced else "create"
        print(f"{verb:8}{dest}" + (f" -> {payload}" if kind == "link" else ""))
    if a.check:
        print(f"{len(plan)} change(s) needed")
        return 1 if plan else 0
    if replaced and not a.yes:
        if not sys.stdin.isatty():
            print(f"{len(replaced)} existing item(s) would be replaced. Rerun with --yes to confirm.", file=sys.stderr)
            return 2
        try:
            answer = input(f"Replace {len(replaced)} existing item(s)? [y/N] ")
        except EOFError:
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            print("Nothing changed.")
            return 1
    for kind, dest, payload in plan:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        elif kind == "link" and (dest.exists() or dest.is_symlink()):
            dest.unlink()
        if kind == "write":
            dest.write_text(payload)
        else:
            dest.symlink_to(payload)
    print(f"{len(plan)} change(s) applied")
    return 0


sys.exit(main())
