#!/usr/bin/python3
"""Projects the harness into the global config of Claude Code and opencode.

Skills are symlinked. Agents are rendered from agents/*.md with the shared preamble
(skills/harness-common/references/preamble.md). Instructions are copied. A manifest per host
lists what this script owns, so a later run removes what is no longer planned.
Usage: install.py [--check] [--claude 0|1] [--opencode 0|1] [--yes]
Exit: 0 done or clean, 1 drift (--check), 2 needs --yes without a terminal, 3 declined, 4 invalid source.
"""
import argparse, json, os, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# -I leaves the script folder out of sys.path (topics/macOS Python.md).
sys.path.insert(0, str(ROOT / "skills" / "harness-common" / "scripts"))
import claude_code, opencode  # noqa: E402

TIERS = ("fast", "default", "strong")
AGENT_KEYS = ("name", "description", "tier", "tools")
MANIFEST = "agent-harness-manifest.json"
BACKUP = "agent-harness-backup"


class InvalidSource(Exception):
    """A missing or malformed source file. The message names the file and, for agents, the key."""


def frontmatter(text):
    """(meta, body) of a file that starts with `---` lines of `key: value`. ValueError names the problem."""
    lines = text.split("\n")
    if lines[0] != "---":
        raise ValueError("no opening --- fence")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("no closing --- fence") from None
    meta = {}
    for number, line in enumerate(lines[1:end], 2):
        key, sep, value = line.partition(": ")
        if not sep or not key.strip() or not value.strip() or key != key.strip():
            raise ValueError(f"line {number}: not a 'key: value' line: {line!r}")
        if key in meta:
            raise ValueError(f"{key}: given twice")
        meta[key] = value.strip()
    return meta, "\n".join(lines[end + 1:]).lstrip("\n")


def parse_agent(path):
    """Validated (meta, body) of one agent source. `tools` becomes a list. ValueError names the key."""
    meta, body = frontmatter(path.read_text())
    for key in AGENT_KEYS:
        if key not in meta:
            raise ValueError(f"{key}: missing")
    for key in meta:
        if key not in AGENT_KEYS:
            raise ValueError(f"{key}: unknown key (allowed: {', '.join(AGENT_KEYS)})")
    if meta["name"] != path.stem:
        raise ValueError(f"name: {meta['name']} differs from the file name {path.stem}")
    if meta["tier"] not in TIERS:
        raise ValueError(f"tier: unknown tier {meta['tier']} (allowed: {', '.join(TIERS)})")
    tools = [t.strip() for t in meta["tools"].split(",")]
    for tool in tools:
        if tool in claude_code.SPAWN_TOOLS:
            raise ValueError(f"tools: {tool} is a spawn tool; agents never spawn subagents")
        if tool not in claude_code.TOOLS:
            raise ValueError(f"tools: unknown tool {tool!r} (allowed: {', '.join(claude_code.TOOLS)})")
    if not body.strip():
        raise ValueError("body: empty")
    meta["tools"] = tools
    return meta, body


def sources():
    """(agents, instructions text, preamble text, skill folders). Raises InvalidSource with every problem."""
    errors = []
    for name in ("agents", "skills"):
        if not (ROOT / name).is_dir():
            errors.append(f"{name}/: missing folder")
    agents = []
    if (ROOT / "agents").is_dir():
        for path in sorted((ROOT / "agents").glob("*.md")):
            try:
                agents.append((path.name, *parse_agent(path)))
            except ValueError as e:
                errors.append(f"agents/{path.name}: {e}")
    texts = []
    for rel in ("instructions/global.md", "skills/harness-common/references/preamble.md"):
        if (ROOT / rel).is_file():
            texts.append((ROOT / rel).read_text())
        else:
            errors.append(f"{rel}: missing")
    if errors:
        raise InvalidSource("\n".join(errors))
    skills = sorted(d for d in (ROOT / "skills").iterdir() if d.is_dir())
    return agents, texts[0], texts[1], skills


def desired(p, adapter, agents, instructions, preamble, skills):
    """Ordered {destination: ("write", content) | ("link", source)} for one host (paths `p`)."""
    items = {}
    for filename, meta, body in agents:
        items[p["agents"] / filename] = ("write", adapter.render_agent(meta, body, preamble))
    items[p["instructions"]] = ("write", instructions)
    for d in skills:
        items[p["skills"] / d.name] = ("link", d)
    return items


def is_real_dir(path):
    return path.is_dir() and not path.is_symlink()


def points_into(link, roots):
    target = Path(os.path.normpath(link.parent / os.readlink(link)))
    return any(target == r or r in target.parents for r in roots)


def read_manifest(path):
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except ValueError:
        print(f"warning: {path} is not valid JSON, ignored", file=sys.stderr)
        return {}


def owned(base, manifest):
    """Manifest entries as absolute paths inside base. Entries that leave base are ignored."""
    out = []
    for key in ("files", "links"):
        entries = manifest.get(key)
        for rel in entries if isinstance(entries, list) else []:
            if isinstance(rel, str) and not os.path.isabs(rel):
                dest = Path(os.path.normpath(base / rel))
                if base in dest.parents:
                    out.append(dest)
    return out


def plan_host(p, items, stamp):
    """Plan entries (verb, destination, kind, payload) that bring one host (paths `p`) to `items`."""
    base = p["base"]
    plan = []
    for dest, (kind, payload) in items.items():
        if is_real_dir(dest):
            # A folder is never deleted: it moves aside (FR-INST-12, -13).
            plan.append(("backup", dest, "backup", base / BACKUP / stamp / dest.relative_to(base)))
            plan.append(("replace", dest, kind, payload))
            continue
        exists = dest.exists() or dest.is_symlink()
        if kind == "write":
            # A symlink at a file destination is replaced, never written through (FR-INST-12).
            same = exists and not dest.is_symlink() and dest.read_text() == payload
        else:
            same = dest.is_symlink() and dest.resolve() == payload.resolve()
        if not same:
            plan.append(("replace" if exists else "create", dest, kind, payload))
    manifest_path = base / MANIFEST
    manifest = read_manifest(manifest_path)
    roots = {ROOT} | ({Path(manifest["checkout"])} if isinstance(manifest.get("checkout"), str) else set())
    stale = []
    for dest in owned(base, manifest):
        if dest in items or dest in stale:
            continue
        if dest.is_symlink() and points_into(dest, roots):
            stale.append(dest)
        elif dest.is_file() and not dest.is_symlink() and dest.parent == p["agents"]:
            stale.append(dest)
    if p["skills"].is_dir():
        for dest in sorted(p["skills"].iterdir()):
            if (dest not in items and dest not in stale and dest.is_symlink() and not dest.exists()
                    and points_into(dest, {ROOT})):
                stale.append(dest)
    plan += [("remove", dest, "remove", None) for dest in stale]
    files = sorted(str(d.relative_to(base)) for d, (k, _) in items.items() if k == "write")
    links = sorted(str(d.relative_to(base)) for d, (k, _) in items.items() if k == "link")
    content = json.dumps({"checkout": str(ROOT), "files": files, "links": links}, indent=2) + "\n"
    if not (manifest_path.is_file() and not manifest_path.is_symlink() and manifest_path.read_text() == content):
        exists = manifest_path.exists() or manifest_path.is_symlink()
        plan.append(("replace" if exists else "create", manifest_path, "write", content))
    return plan


def apply(entry):
    _, dest, kind, payload = entry
    dest.parent.mkdir(parents=True, exist_ok=True)
    if kind == "backup":
        payload.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dest), str(payload))
    elif kind == "remove":
        dest.unlink()
    elif kind == "write":
        tmp = dest.with_name(f".{dest.name}.agent-harness-tmp")
        tmp.write_text(payload)
        os.replace(tmp, dest)  # replaces a symlink itself, not its target
    else:
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        dest.symlink_to(payload)


def describe(entry):
    verb, dest, kind, payload = entry
    return f"{verb:8}{dest}" + (f" -> {payload}" if kind in ("link", "backup") else "")


def main(argv=None, home=None):
    home = Path(home) if home is not None else Path.home()
    ap = argparse.ArgumentParser(description="Install the harness into Claude Code and opencode.")
    ap.add_argument("--check", action="store_true", help="report drift, write nothing")
    ap.add_argument("--claude", type=int, choices=(0, 1))
    ap.add_argument("--opencode", type=int, choices=(0, 1))
    ap.add_argument("--yes", action="store_true", help="replace, move aside or remove existing items without asking")
    a = ap.parse_args(argv)
    try:
        agents, instructions, preamble, skills = sources()
    except InvalidSource as e:
        for line in str(e).splitlines():
            print(f"install.py: {line}", file=sys.stderr)
        return 4
    stamp = time.strftime("%Y%m%d-%H%M%S")
    plan = []
    for adapter, flag in ((claude_code, a.claude), (opencode, a.opencode)):
        p = adapter.paths(home)
        use = flag if flag is not None else int(p["base"].exists() or bool(shutil.which(adapter.BINARY)))
        if use:
            plan += plan_host(p, desired(p, adapter, agents, instructions, preamble, skills), stamp)
    for entry in plan:
        print(describe(entry))
    if a.check:
        print(f"{len(plan)} change(s) needed")
        return 1 if plan else 0
    existing = [e for e in plan if e[0] != "create"]
    if existing and not a.yes:
        if not sys.stdin.isatty():
            print(f"{len(existing)} existing item(s) would be replaced, moved aside or removed. "
                  "Rerun with --yes to confirm.", file=sys.stderr)
            return 2
        try:
            answer = input(f"Replace, move aside or remove {len(existing)} existing item(s)? [y/N] ")
        except EOFError:
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            print("Nothing changed.")
            return 3
    for entry in plan:
        apply(entry)
    print(f"{len(plan)} change(s) applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
