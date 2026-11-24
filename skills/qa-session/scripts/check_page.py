#!/usr/bin/python3
"""Checks a QA session page against the rules a script can decide.

Usage: check_page.py <page.md> [-v]
Prints one summary line. -v lists every finding with its line number.
Exits 1 on a FAIL. Facts (is a value right, does a control exist) are the verifier's job, not this script's.
"""
import argparse, re, sys
from pathlib import Path

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
INTERNAL_ID = re.compile(r"\b(?:R|D|Q|S|DEC|ADR)[- ]?\d{1,3}\b")
PLACEHOLDER = re.compile(r"<(?!/?(?:br|b|i|em|strong|code|sub|sup|u|kbd|details|summary)\b)[A-Za-z][A-Za-z _-]{0,40}>")
UNFINISHED = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b")
BARE_TODAY = re.compile(r"\btoday\b", re.IGNORECASE)
SCENARIO = re.compile(r"^### (\d+)\. \S")
CHECK = re.compile(r"^\s*- \[([ xX])\] \S")
AS_LINE = re.compile(r"^As \S")
HEADING = re.compile(r"^#{1,6} (.+)$")
FINDING_ROW = re.compile(r"^\|\s*\d+\s*\|")


def scan(lines):
    findings = []
    scenarios = []
    current = None
    headings = []
    ticked = 0
    checks = 0
    finding_rows = 0
    in_findings = False

    for number, line in enumerate(lines, 1):
        heading = HEADING.match(line)
        if heading:
            title = heading.group(1).strip()
            headings.append(title.lower())
            in_findings = title.lower().startswith("findings")
            if line.startswith("### "):
                match = SCENARIO.match(line)
                if match:
                    current = {"line": number, "number": int(match.group(1)), "as": False, "checks": 0, "closed": False}
                    scenarios.append(current)
                else:
                    current = None
            else:
                current = None
        if EMOJI.search(line):
            findings.append((number, "FAIL", "emoji"))
        for match in INTERNAL_ID.finditer(line):
            findings.append((number, "FAIL", f"internal id '{match.group(0)}': name the case instead"))
        if PLACEHOLDER.search(line):
            findings.append((number, "FAIL", "placeholder: put the value in the page before the session"))
        if UNFINISHED.search(line):
            findings.append((number, "FAIL", "unfinished marker"))
        if BARE_TODAY.search(line):
            findings.append((number, "WARN", "bare 'today': say 'on production' or 'in this test environment'"))
        if "(cont.)" in line:
            findings.append((number, "WARN", "patched label '(cont.)': rewrite the block"))
        if in_findings and FINDING_ROW.match(line):
            finding_rows += 1

        check = CHECK.match(line)
        if check:
            checks += 1
            if check.group(1).lower() == "x":
                ticked += 1
            if current is not None:
                if not current["as"]:
                    findings.append((number, "FAIL", "check before the 'As <user>:' line of its scenario"))
                    current["as"] = True
                current["checks"] += 1
        elif current is not None and AS_LINE.match(line) and not current["as"]:
            current["as"] = True

    numbers = [s["number"] for s in scenarios]
    if numbers != list(range(1, len(numbers) + 1)):
        findings.append((0, "FAIL", f"scenario numbers are {numbers}, expected 1 to {len(numbers)} in order"))
    for scenario in scenarios:
        if scenario["checks"] == 0:
            findings.append((scenario["line"], "WARN", "scenario without checkboxes"))
    if not any("known limits" in h for h in headings):
        findings.append((0, "WARN", "no 'Known limits, not bugs' section"))
    if not any(h.startswith("findings") for h in headings):
        findings.append((0, "FAIL", "no Findings section"))
    if not any(h.startswith("product question") for h in headings):
        findings.append((0, "WARN", "no product questions section (write 'none' if there are none)"))

    return findings, {"scenarios": len(scenarios), "checks": checks, "ticked": ticked, "finding_rows": finding_rows}


def main():
    parser = argparse.ArgumentParser(description="Check a QA session page.")
    parser.add_argument("page", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    lines = args.page.read_text(encoding="utf-8").splitlines()
    findings, counts = scan(lines)
    fails = sum(1 for _, level, _ in findings if level == "FAIL")
    warns = sum(1 for _, level, _ in findings if level == "WARN")
    print(
        f"qa page: {counts['scenarios']} scenarios, {counts['checks']} checks, "
        f"{counts['ticked']} ticked, {counts['finding_rows']} findings, {fails} FAIL, {warns} WARN"
    )
    if args.verbose:
        for number, level, message in findings:
            where = f"line {number}" if number else "page"
            print(f"{level} {where}: {message}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
