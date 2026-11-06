#!/usr/bin/env bash
# Installs the rearchitect skill and its three subagents for Claude Code and opencode.
# Override models: AUDIT_MODEL_OC=... ARCH_MODEL_OC=... ./install.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
audit_cc="${AUDIT_MODEL_CC:-sonnet}"
arch_cc="${ARCH_MODEL_CC:-opus}"
audit_oc="${AUDIT_MODEL_OC:-deepseek/deepseek-flash}"
arch_oc="${ARCH_MODEL_OC:-deepseek/deepseek-v4-pro}"
phase_cc="${PHASE_MODEL_CC:-inherit}"
phase_oc="${PHASE_MODEL_OC:-}" # empty: use the main session model

audit_desc="Audits one aspect of a project for the rearchitect skill: reads every assigned file, writes findings to .rearch/audit/."
phase_desc="Executes one phase of a rearchitect plan in a clean context: implements, verifies, leaves changes uncommitted."
arch_desc="Consolidates rearchitect audits into requirements, then designs the new architecture and phase plan in .rearch/."

# Each tool is set up only when its command or config dir exists.
# Force with WITH_CLAUDE=1 / WITH_OPENCODE=1, skip with =0.
detect() { command -v "$1" >/dev/null 2>&1 || [ -d "$2" ] && echo 1 || echo 0; }
WITH_CLAUDE="${WITH_CLAUDE:-$(detect claude ~/.claude)}"
WITH_OPENCODE="${WITH_OPENCODE:-$(detect opencode ~/.config/opencode)}"
if [ "$WITH_CLAUDE" != 1 ] && [ "$WITH_OPENCODE" != 1 ]; then
  echo "Neither Claude Code nor opencode found. Set WITH_CLAUDE=1 or WITH_OPENCODE=1 to force." >&2
  exit 1
fi

if [ "$WITH_CLAUDE" = 1 ]; then
  # Claude Code skill and agents (opencode also reads ~/.claude/skills)
  mkdir -p ~/.claude/skills ~/.claude/agents
  ln -sfn "$here" ~/.claude/skills/rearchitect
  write_cc() { # name desc model tools body
    { printf -- '---\nname: %s\ndescription: %s\nmodel: %s\ntools: %s\n---\n\n' "$1" "$2" "$3" "$4"; cat "$5"; } > ~/.claude/agents/"$1".md
  }
  write_cc rearch-auditor "$audit_desc" "$audit_cc" "Read, Grep, Glob, Bash, Write" "$here/agents/auditor.body.md"
  write_cc rearch-architect "$arch_desc" "$arch_cc" "Read, Grep, Glob, Bash, Write, Edit" "$here/agents/architect.body.md"
  write_cc rearch-phase "$phase_desc" "$phase_cc" "Read, Grep, Glob, Bash, Write, Edit" "$here/agents/phase.body.md"
  echo "Claude Code: installed (models $audit_cc / $arch_cc / $phase_cc)."
else
  echo "Claude Code: not found, skipped."
fi

if [ "$WITH_OPENCODE" != 1 ]; then
  echo "opencode: not found, skipped."
  exit 0
fi

# opencode skill and agents
mkdir -p ~/.config/opencode/skills ~/.config/opencode/agents
ln -sfn "$here" ~/.config/opencode/skills/rearchitect
write_oc() { # name desc model body
  { printf -- '---\ndescription: %s\nmode: subagent\n' "$2"
    [ -n "$3" ] && printf -- 'model: %s\n' "$3"
    printf -- '---\n\n'; cat "$4"; } > ~/.config/opencode/agents/"$1".md
}
write_oc rearch-auditor "$audit_desc" "$audit_oc" "$here/agents/auditor.body.md"
write_oc rearch-architect "$arch_desc" "$arch_oc" "$here/agents/architect.body.md"
write_oc rearch-phase "$phase_desc" "$phase_oc" "$here/agents/phase.body.md"

echo "opencode: installed (models $audit_oc / $arch_oc / ${phase_oc:-main session model})."
