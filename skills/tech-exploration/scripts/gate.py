#!/usr/bin/python3
"""Records where each section of a tech exploration stands.

Usage:
  gate.py open <work folder> <stage> <section> [--file F] [--heading H]
  gate.py grilled <work folder> <section> --rounds N --open-findings N
  gate.py approve <work folder> <section> --by NAME
  gate.py skip <work folder> <section>
  gate.py reopen <work folder> <section> --reason TEXT
  gate.py status <work folder>
  gate.py verify <work folder>
"""
import hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

STAGES = ["intake", "sources", "product", "product-review", "technical", "milestones", "audit", "publish"]
PASSED = ("approved", "not reviewed")
REVIEWABLE = ("stale", "not reviewed")
DRAFT_STAGES = {
    "technical-solution.md": "technical",
    "design-proposal.md": "technical",
    "alternatives.md": "technical",
}
HEADING = re.compile(r"(#+)\s+(.*)")


class Refused(Exception):
    pass


class Gate:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.path = self.folder / "gates.json"
        self.gates = json.loads(self.path.read_text())["gates"] if self.path.exists() else []

    def open(self, stage, gate_id, file=None, heading=None):
        if stage not in STAGES:
            raise Refused(f"unknown stage {stage}, use one of: {', '.join(STAGES)}")
        existing = self.find(gate_id)
        if existing and existing["status"] not in REVIEWABLE:
            raise Refused(f"{gate_id} is {existing['status']}: reopen it first")
        blocking = self.blockers(stage, gate_id)
        if blocking:
            raise Refused(f"{gate_id} comes after sections in progress, approve or skip them first: {', '.join(blocking)}")
        gate = existing or {"id": gate_id}
        gate.update(stage=stage, file=file, heading=heading, status="drafting")
        if not existing:
            self.gates.append(gate)
        self.save()
        return f"opened {gate_id} ({stage})"

    def grilled(self, gate_id, rounds, open_findings):
        gate = self.fetch(gate_id)
        if gate["status"] != "drafting":
            raise Refused(f"{gate_id} is {gate['status']}, not drafting")
        if rounds < 1:
            raise Refused(f"{gate_id} needs at least one challenge round")
        if open_findings > 0:
            raise Refused(f"{gate_id} still has {open_findings} open findings: settle them or ask the author")
        gate.update(status="grilled", rounds=rounds)
        self.save()
        return f"{gate_id} grilled in {rounds} round(s)"

    def approve(self, gate_id, by):
        gate = self.fetch(gate_id)
        if gate["status"] != "grilled":
            raise Refused(f"{gate_id} is {gate['status']}: it must be grilled before approval")
        if not (by or "").strip():
            raise Refused("approval needs --by with the name of the person who approved")
        digest = self.section_hash(gate)
        if gate.get("heading") and digest is None:
            raise Refused(f"{gate_id}: section \"{gate['heading']}\" not found in {gate['file']}")
        gate.update(status="approved", approved_by=by,
                    approved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), hash=digest)
        self.save()
        return f"{gate_id} approved by {by}"

    def skip(self, gate_id):
        gate = self.fetch(gate_id)
        if gate["status"] == "approved":
            raise Refused(f"{gate_id} is approved")
        gate["status"] = "not reviewed"
        self.save()
        return f"{gate_id} not reviewed, moving on"

    def reopen(self, gate_id, reason):
        gate = self.fetch(gate_id)
        if not (reason or "").strip():
            raise Refused("reopen needs --reason")
        index = self.gates.index(gate)
        gate.update(status="drafting", reopened_because=reason)
        stale = [later for later in self.gates[index + 1:] if later["status"] == "approved"]
        for later in stale:
            later["status"] = "stale"
        self.save()
        return "\n".join([f"reopened {gate_id}"] + [f"{later['id']} is now stale" for later in stale])

    def status(self):
        if not self.gates:
            return "no gates yet"
        lines = []
        for gate in self.gates:
            by = f" by {gate['approved_by']}" if gate.get("approved_by") and gate["status"] == "approved" else ""
            changed = ", CHANGED SINCE APPROVAL" if self.changed_since_approval(gate) else ""
            lines.append(f"{gate['stage']} / {gate['id']}: {gate['status']}{by}{changed}")
        return "\n".join(lines)

    def problems(self):
        found = [f"{g['id']} changed after its approval: reopen it" for g in self.gates if self.changed_since_approval(g)]
        for name, stage in DRAFT_STAGES.items():
            if (self.folder / "draft" / name).exists() and not any(g["stage"] == stage for g in self.gates):
                found.append(f"draft/{name} exists before the {stage} stage was opened")
        found += [f"{g['id']} is stale: re-review it" for g in self.gates if g["status"] == "stale"]
        return found

    def blockers(self, stage, except_id):
        limit = STAGES.index(stage)
        return [g["id"] for g in self.gates
                if STAGES.index(g["stage"]) <= limit and g["id"] != except_id and g["status"] not in PASSED]

    def find(self, gate_id):
        return next((g for g in self.gates if g["id"] == gate_id), None)

    def fetch(self, gate_id):
        gate = self.find(gate_id)
        if gate is None:
            raise Refused(f"no gate {gate_id}")
        return gate

    def changed_since_approval(self, gate):
        return gate["status"] == "approved" and bool(gate.get("hash")) and self.section_hash(gate) != gate["hash"]

    def section_hash(self, gate):
        if not gate.get("file"):
            return None
        path = self.folder / gate["file"]
        if not path.exists():
            return None
        text = path.read_text()
        if gate.get("heading"):
            text = section(text, gate["heading"])
        return hashlib.sha256(text.strip().encode()).hexdigest() if text is not None else None

    def save(self):
        self.path.write_text(json.dumps({"gates": self.gates}, indent=2) + "\n")


def section(text, heading):
    lines = text.splitlines(keepends=True)
    start = level = None
    for index, line in enumerate(lines):
        match = HEADING.fullmatch(line.rstrip("\n"))
        if not match:
            continue
        if start is not None:
            if len(match.group(1)) <= level:
                return "".join(lines[start:index])
        elif match.group(2).strip().lower() == heading.strip().lower():
            start, level = index, len(match.group(1))
    return "".join(lines[start:]) if start is not None else None


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    command, folder, rest = argv[0], argv[1], argv[2:]
    options, positional = {}, []
    while rest:
        arg = rest.pop(0)
        if arg.startswith("--"):
            options[arg[2:]] = rest.pop(0) if rest else ""
        else:
            positional.append(arg)
    gate = Gate(folder)
    try:
        if command == "open":
            print(gate.open(positional[0], positional[1], file=options.get("file"), heading=options.get("heading")))
        elif command == "grilled":
            print(gate.grilled(positional[0], int(options.get("rounds", 0)), int(options.get("open-findings", 0))))
        elif command == "approve":
            print(gate.approve(positional[0], options.get("by")))
        elif command == "skip":
            print(gate.skip(positional[0]))
        elif command == "reopen":
            print(gate.reopen(positional[0], options.get("reason")))
        elif command == "status":
            print(gate.status())
        elif command == "verify":
            found = gate.problems()
            print("\n".join(found) if found else "OK")
            return 1 if found else 0
        else:
            sys.exit(__doc__)
    except (Refused, IndexError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
