"""Rules over the whole repository: no model names, ignored caches, well-formed skills, agents and Spawns tables."""
import codecs, re, subprocess, sys, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"
sys.path.insert(0, str(REPO))
import install  # noqa: E402  (one frontmatter parser: install.py's)

# Model names, families and id prefixes, ROT13-encoded so this file holds none (FR-AGT-08).
WORDS = ["fbaarg", "bchf", "unvxh", "qrrcfrrx", "trzvav", "yynzn", "zvfgeny", "djra", "xvzv"]
PREFIXES = ["tcg", "pynhqr"]  # followed by a version number
MODEL_NAME = re.compile(
    r"\b(?:" + "|".join(codecs.decode(w, "rot13") for w in WORDS) + r")\b"
    + r"|\b(?:" + "|".join(codecs.decode(p, "rot13") for p in PREFIXES) + r")-?\d",
    re.IGNORECASE,
)
# Run state records the model mapping the user confirmed (FR-AGT-07), so it is not scanned.
RUN_STATE = (".rearch/", ".attack-plan/", ".ai-notes/")


def tracked_files():
    """Tracked files plus untracked ones git does not ignore, so a new file is checked before its commit."""
    done = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                          capture_output=True, text=True)
    if done.returncode:
        raise unittest.SkipTest("not a git checkout")
    return [name for name in done.stdout.split("\0") if name and (REPO / name).is_file()]


def frontmatter(text):
    return install.frontmatter(text)[0]


def check_agent(path):
    return install.parse_agent(path)[0]


SPAWNS_HEADER = ["Spawn", "Tier", "Used for"]


def spawns_problems(text, agents):
    """Problems in the `Spawns` tables of one SKILL.md (harness-common/references/model-tiers.md "Spawns table").

    A table follows a heading named `Spawns`. Its Spawn cell names an agent or `general` (the first
    backticked word, else the cell), and its Tier cell is the agent's tier. `agents` maps name to tier.
    """
    problems, fenced, section, header = [], False, False, None
    for number, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if s.startswith("#"):
            section, header = s.lstrip("#").strip() == "Spawns", None
            continue
        if not section or not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
            if cells != SPAWNS_HEADER:
                problems.append(f"line {number}: header {cells}, want {SPAWNS_HEADER}")
            continue
        if all(set(c) <= set(":- ") for c in cells) or header != SPAWNS_HEADER:
            continue
        span = re.search(r"`([^`]+)`", cells[0])
        spawn = span.group(1) if span else cells[0]
        tier = cells[1].strip("` ") if len(cells) > 1 else ""
        if tier not in install.TIERS:
            problems.append(f"line {number}: {spawn}: unknown tier {tier!r}")
        elif spawn != "general" and spawn not in agents:
            problems.append(f"line {number}: {spawn}: no such agent in agents/")
        elif spawn != "general" and agents[spawn] != tier:
            problems.append(f"line {number}: {spawn}: tier {tier}, agents/{spawn}.md says {agents[spawn]}")
    return problems


def has_spawns_table(text):
    """True when a heading named `Spawns` is followed by a table with the Spawns header, outside fences."""
    fenced, section = False, False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fenced = not fenced
        elif not fenced and s.startswith("#"):
            section = s.lstrip("#").strip() == "Spawns"
        elif not fenced and section and s.startswith("|"):
            if [c.strip() for c in s.strip("|").split("|")] == SPAWNS_HEADER:
                return True
    return False


def spawns(text, agents):
    """True when a SKILL.md delegates: it names an agent from agents/, the host's general-purpose
    subagent, or links the tier gate (model-tiers.md)."""
    names = "|".join(re.escape(a) for a in agents)
    return bool(re.search(r"\b(?:" + names + r")\b|general-purpose|model-tiers\.md", text))


class ModelNameTest(unittest.TestCase):
    def setUp(self):
        self.files = [f for f in tracked_files() if not f.startswith(RUN_STATE)]
        self.hits = {}
        for name in self.files:
            text = (REPO / name).read_bytes().decode("utf-8", errors="ignore")
            found = sorted({m.group(0) for m in MODEL_NAME.finditer(text)})
            if found:
                self.hits[name] = found

    def test_no_model_name_in_any_tracked_file(self):
        self.assertEqual(self.hits, {})

    def test_every_skill_folder_is_scanned(self):
        scanned = {name.split("/")[1] for name in self.files if name.startswith("skills/") and name.count("/") >= 2}
        folders = {d.name for d in (REPO / "skills").iterdir() if d.is_dir()}
        self.assertEqual(sorted(folders - scanned), [])
        self.assertIn("skills/storyboard/references/skeleton.html", self.files)
        self.assertIn("docs/requirements.md", self.files)

    def test_the_pattern_finds_names_and_ids(self):
        for text in (codecs.decode("zbqry: bchf", "rot13"), codecs.decode("qrrcfrrx/qrrcfrrx-synfu", "rot13"),
                     codecs.decode("pynhqr-3-5", "rot13"), codecs.decode("TCG-4b", "rot13")):
            self.assertRegex(text, MODEL_NAME)
        for text in ("Claude Code", "opencode", "magnum-opusculum", "ollama"):
            self.assertNotRegex(text, MODEL_NAME)


class RepoRulesTest(unittest.TestCase):
    def test_bytecode_caches_are_ignored(self):
        for path in ("skills/feedback-watch/scripts/__pycache__/watch.cpython-39.pyc", "tests/stray.pyc"):
            done = subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", path])
            self.assertEqual(done.returncode, 0, path)

    def test_every_skill_has_a_skill_md_named_after_its_folder(self):
        for folder in sorted(d for d in (REPO / "skills").iterdir() if d.is_dir()):
            with self.subTest(skill=folder.name):
                meta = frontmatter((folder / "SKILL.md").read_text())
                self.assertEqual(meta.get("name"), folder.name)
                self.assertTrue(meta.get("description"))

    def test_every_agent_parses(self):
        agents = sorted((REPO / "agents").glob("*.md"))
        self.assertTrue(agents)
        for path in agents:
            with self.subTest(agent=path.name):
                check_agent(path)

    def test_the_agent_check_rejects_the_bad_fixtures(self):
        for name, reason in (("bad-fence.md", "opening"), ("bad-tier.md", "tier")):
            with self.subTest(fixture=name), self.assertRaisesRegex(ValueError, reason):
                check_agent(FIXTURES / "agents" / name)


class SpawnsTableTest(unittest.TestCase):
    AGENTS = {"critic": "strong", "reader": "fast"}

    def test_every_skill_that_spawns_has_a_spawns_table(self):
        agents = [p.stem for p in (REPO / "agents").glob("*.md")]
        need = set()
        for path in sorted((REPO / "skills").glob("*/SKILL.md")):
            # harness-common defines the convention; it never spawns.
            if (path.parent / "references" / "model-tiers.md").exists():
                continue
            text = path.read_text()
            if spawns(text, agents):
                need.add(path.parent.name)
                with self.subTest(skill=path.parent.name):
                    self.assertTrue(has_spawns_table(text), "no Spawns table")
        for name in ("attack-plan-create", "attack-plan-milestone-execute", "qa-session", "rearchitect", "storyboard"):
            self.assertIn(name, need)

    def test_the_spawn_checks_read_text(self):
        table = "## Spawns\n\n| Spawn | Tier | Used for |\n|---|---|---|\n| `general` | strong | x |\n"
        self.assertTrue(has_spawns_table(table))
        self.assertFalse(has_spawns_table("```\n" + table + "```\n"))
        self.assertFalse(has_spawns_table("## Other\n\n| Spawn | Tier | Used for |\n"))
        self.assertTrue(spawns("Spawn `critic` per section.", ["critic"]))
        self.assertTrue(spawns("run the gate in [model-tiers.md](x)", []))
        self.assertFalse(spawns("Subagents read the notes. A critical path.", ["critic"]))

    def test_every_spawns_table_names_real_agents_with_their_tier(self):
        agents = {p.stem: check_agent(p)["tier"] for p in (REPO / "agents").glob("*.md")}
        for path in sorted((REPO / "skills").glob("*/SKILL.md")):
            with self.subTest(skill=path.parent.name):
                self.assertEqual(spawns_problems(path.read_text(), agents), [])

    def test_the_check_accepts_a_good_table(self):
        text = ("## Spawns\n\n| Spawn | Tier | Used for |\n|---|---|---|\n"
                "| `critic` | `strong` | attacks |\n| `general` | default | builds |\n| reader | fast | reads |\n")
        self.assertEqual(spawns_problems(text, self.AGENTS), [])

    def test_the_check_finds_bad_rows(self):
        text = ("## Spawns\n\n| Spawn | Tier | Used for |\n|---|---|---|\n"
                "| `critic` | fast | x |\n| `ghost` | fast | x |\n| `general` | quick | x |\n"
                "\n## Other\n\n| `ghost` | fast | ignored |\n"
                "\n## Spawns\n\n| Agent | Tier |\n|---|---|\n")
        problems = spawns_problems(text, self.AGENTS)
        self.assertEqual(len(problems), 4, problems)
        for part in ("critic: tier fast", "ghost: no such agent", "unknown tier 'quick'", "header"):
            self.assertTrue(any(part in p for p in problems), part)

    def test_a_fenced_table_is_not_checked(self):
        text = "## Spawns\n\n```\n| Spawn | Tier | Used for |\n|---|---|---|\n| `ghost` | fast | x |\n```\n"
        self.assertEqual(spawns_problems(text, self.AGENTS), [])


if __name__ == "__main__":
    unittest.main()
