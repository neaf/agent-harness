#!/usr/bin/python3
"""Checks the drafts of an attack plan against the writing rules.

Usage: check_draft.py <draft folder> [--product]
Prints PASS, WARN or FAIL lines. Exits 1 on a FAIL.
"""
import re, sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "summary": r"\bsummary\b",
    "product": r"\bproduct solution\b",
    "questions": r"\bopen questions\b",
    "technical": r"\btechnical solution\b",
    "milestones": r"\bmilestones\b",
    "risks": r"\brisks\b",
}
PRODUCT_STAGE_SECTIONS = ("summary", "product", "questions")
LATER_SECTIONS = ("technical", "milestones")
EFFORT_PATTERNS = [
    r"\b(engineer|dev|developer|man|person)[- ]?(days?|weeks?|months?)\b",
    r"\bstory[- ]points?\b",
    r"\bt-shirt siz",
]
CROSS_REFERENCE_PATTERNS = [
    r"\bsee (section |§ ?)?\d+(\.\d+)*\b",
    r"§ ?\d",
    r"\bas (mentioned|described|said) above\b",
    r"\bsee (risk|question) \d+\b",
]
PRODUCT_CODE_TERMS = r"\b(controller|endpoint|serializer|migration|query|orm|sql|class|schema)\b"
HEADING = re.compile(r"(#+)\s+(.*)")
QUESTION_START = re.compile(r"(?=^\s*[-*]?\s*\*\*Q\d+\.)", re.MULTILINE)
QUESTION_TITLE = re.compile(r"\s*[-*]?\s*\*\*Q(\d+)\.\s*(.+?)\*\*")
QUESTION_PARTS = ("Context", "Question", "Recommendation")
MAIN_FILES = ("attack-plan.md", "technical-solution.md", "evidence.md")


class CheckDraft:
    def __init__(self, folder, stage="full"):
        self.folder = Path(folder)
        self.stage = stage
        self.results = []

    def run(self):
        plan_path = self.folder / "attack-plan.md"
        if not plan_path.exists():
            self.add("FAIL", "attack-plan.md", "missing")
            return self.results
        plan = plan_path.read_text()
        self.check_sections(plan)
        if self.stage == "product":
            self.check_product_stage(plan)
        self.check_product_section(plan)
        self.check_questions(plan)
        if re.search(r"<td>\s*estimat|\|\s*estimat", plan.lower()):
            self.add("FAIL", "attack-plan.md", "a task table has an estimate column")
        for name in MAIN_FILES:
            path = self.folder / name
            if path.exists():
                self.check_text(name, path.read_text())
        if not any(level == "FAIL" for level, _, _ in self.results):
            self.add("PASS", "all", "no blocking issue")
        return self.results

    def check_sections(self, plan):
        keys = PRODUCT_STAGE_SECTIONS if self.stage == "product" else REQUIRED_SECTIONS
        for key in keys:
            if section_index(plan, REQUIRED_SECTIONS[key]) is None:
                self.add("FAIL", "attack-plan.md", f"no {key} section")
        product, questions, technical = (section_index(plan, REQUIRED_SECTIONS[k])
                                         for k in ("product", "questions", "technical"))
        if None not in (product, questions, technical) and not product < questions < technical:
            self.add("FAIL", "attack-plan.md",
                     "Open questions must sit after Product solution and before Technical solution")

    def check_product_stage(self, plan):
        if (self.folder / "technical-solution.md").exists():
            self.add("FAIL", "technical-solution.md", "exists before the product solution is approved")
        for key in LATER_SECTIONS:
            text = section_text(plan, REQUIRED_SECTIONS[key])
            if text and text.strip():
                self.add("FAIL", "attack-plan.md", f"the {key} section has content before the product solution is approved")

    def check_product_section(self, plan):
        text = section_text(plan, REQUIRED_SECTIONS["product"])
        if not text:
            return
        if re.search(r"`[^`]+`", text):
            self.add("WARN", "attack-plan.md", "inline code in the product solution")
        for term in dict.fromkeys(re.findall(PRODUCT_CODE_TERMS, text.lower())):
            self.add("WARN", "attack-plan.md", f"code term \"{term}\" in the product solution")

    def check_questions(self, plan):
        text = section_text(plan, REQUIRED_SECTIONS["questions"])
        if not text:
            return
        blocks = [b for b in QUESTION_START.split(text) if QUESTION_TITLE.match(b)]
        numbers = [int(QUESTION_TITLE.match(b).group(1)) for b in blocks]
        if numbers != list(range(1, len(numbers) + 1)):
            self.add("FAIL", "attack-plan.md",
                     f"questions are not numbered 1 to {len(numbers)} in order: {', '.join(map(str, numbers))}")
        for block in blocks:
            number, title = QUESTION_TITLE.match(block).groups()
            if title.strip().endswith("."):
                self.add("WARN", "attack-plan.md", f"Q{number} title ends with a period")
            missing = [part for part in QUESTION_PARTS if f"**{part}" not in block]
            if missing:
                self.add("FAIL", "attack-plan.md", f"Q{number} has no {', '.join(missing)}")

    def check_text(self, name, text):
        for line, number in prose_lines(text):
            lowered = line.lower()
            for pattern in EFFORT_PATTERNS:
                match = re.search(pattern, lowered)
                if match:
                    self.add("FAIL", name, f"line {number}: effort estimate \"{match.group(0)}\"")
            for pattern in CROSS_REFERENCE_PATTERNS:
                match = re.search(pattern, lowered)
                if match:
                    self.add("WARN", name, f"line {number}: inline cross-reference \"{match.group(0)}\"")
            if re.search(r"\bOption [A-D]\b", line):
                self.add("FAIL", name, f"line {number}: \"Option A/B\" belongs in the alternatives")
            if line.count("`") % 2:
                self.add("FAIL", name, f"line {number}: odd number of backticks")
        if any("decision log" in title for _, title, _ in headings(text)):
            self.add("FAIL", name, "a decision log section")

    def add(self, level, file, message):
        self.results.append((level, file, message))


def prose_lines(text):
    in_fence = False
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line, number


def headings(text):
    found = []
    for line, number in prose_lines(text):
        match = HEADING.fullmatch(line.rstrip("\n"))
        if match:
            found.append((len(match.group(1)), match.group(2).strip().lower(), number))
    return found


def section_index(plan, pattern):
    return next((i for i, (_, title, _) in enumerate(headings(plan)) if re.search(pattern, title)), None)


def section_text(plan, pattern):
    found = headings(plan)
    index = section_index(plan, pattern)
    if index is None:
        return None
    level, _, start = found[index]
    finish = next((number for lvl, _, number in found[index + 1:] if lvl <= level), None)
    lines = plan.splitlines(keepends=True)
    return "".join(lines[start:(finish - 1) if finish else len(lines)])


def main(argv):
    folder = next((arg for arg in argv if not arg.startswith("--")), None)
    if not folder or not Path(folder).is_dir():
        sys.exit(__doc__)
    results = CheckDraft(folder, "product" if "--product" in argv else "full").run()
    for level, file, message in results:
        print(f"{level} {file}: {message}")
    return 1 if any(level == "FAIL" for level, _, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
