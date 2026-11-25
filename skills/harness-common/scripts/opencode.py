"""opencode adapter: install paths and agent rendering.

Facts: skills/harness-common/topics/opencode.md.
"""
import json
from pathlib import Path

BINARY = "opencode"
# Claude Code tool name -> opencode permission action (opencode.md "Permissions").
ACTIONS = {
    "Read": "read", "Glob": "glob", "Grep": "grep", "Edit": "edit", "Write": "edit",
    "Bash": "shell", "WebFetch": "webfetch", "WebSearch": "websearch", "Skill": "skill",
}
SPAWN_ACTION = "subagent"
# opencode only: Code Mode cannot reach the filesystem (opencode.md "`execute` (Code Mode)").
SANDBOX_LINE = ("Use the file, search and shell tools directly. "
                "The `execute` sandbox supports no `import`, `require` or filesystem access.")


def paths(home):
    base = Path(home) / ".config" / "opencode"
    return {"base": base, "agents": base / "agents", "skills": base / "skills", "instructions": base / "AGENTS.md"}


def permissions(tools):
    """Deny rules for every mapped action the agent's `tools` do not cover, then the spawn deny.

    Only denies: allowed actions keep the defaults and the user's global rules (opencode.md "Permissions").
    """
    allowed = set()
    for tool in tools:
        if tool not in ACTIONS:
            raise ValueError(f"no opencode action for tool {tool}")
        allowed.add(ACTIONS[tool])
    denied = sorted(set(ACTIONS.values()) - allowed) + [SPAWN_ACTION]
    return [{"action": action, "resource": "*", "effect": "deny"} for action in denied]


def render_agent(meta, body, preamble):
    """V2 frontmatter `description`, `mode: subagent`, `permissions`. Never `tools` or `permission`.

    A file with `permissions` is read as V2 and its V1 keys are dropped (opencode.md "Quirk: V1 and V2
    frontmatter"). No `model` line: a subagent without one runs on the session model (FR-AGT-02).
    """
    head = [f"description: {json.dumps(meta['description'])}", "mode: subagent", "permissions:"]
    head += [f'  - {{action: {r["action"]}, resource: "{r["resource"]}", effect: {r["effect"]}}}'
             for r in permissions(meta["tools"])]
    return ("---\n" + "\n".join(head) + "\n---\n\n" + preamble.strip() + "\n\n" + SANDBOX_LINE + "\n\n" + body)
