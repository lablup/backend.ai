#!/usr/bin/env python3
"""Validate the length limits of BEP documents.

Usage:
    python3 scripts/knowledge/check_bep_length.py [--root DIR] [PATH ...]

Checks `proposals/BEP-<number>-*.md`, `.ko.md` and the sub-documents in
`proposals/BEP-<number>/` from BEP-1080 on, or the given paths. The limits follow `proposals/BEP-0000-template.md`. Prints one
"path:line: problem" line per violation and exits 1 when any exist. CI runs this
via knowledge-check.yml.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

FIRST_CHECKED_NUMBER = 1080
BEP_FILE = re.compile(r"^BEP-(\d{4})-.+\.md$")
BEP_DIR = re.compile(r"^BEP-(\d{4})$")
KO_SUFFIX = ".ko.md"

MAX_LINES = 300
MAX_ITEMS = 7
MAX_DESIGN_SUBSECTIONS = 4
MAX_DESIGN_TABLES = 2
MAX_TABLE_ROWS = 7
MAX_DESIGN_SENTENCES = 3
MAX_ITEM_CHARS = {"ko": 80, "en": 120}

GOALS = {"목표", "Goals"}
COUNTED_LISTS = {
    "목표가 아닌 것",
    "Non-goals",
    "영향",
    "Impact",
    "구현 순서",
    "Implementation Order",
}
DESIGN = {"설계", "Design"}
REJECTED_PREFIXES = ("기각한 대안:", "Rejected:")

FENCE = re.compile(r"^\s*(```|~~~)")
LIST_ITEM = re.compile(r"^(\s*)(?:[-*]|\d+\.) (.*)$")
TABLE_ROW = re.compile(r"^\s*\|")
TABLE_DIVIDER = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
IMAGE = re.compile(r"^\s*!\[")
SENTENCE_END = re.compile(r"[^\d\s.]\.(?:\s|$)")
ABBREVIATION = re.compile(r"\b(?:e\.g|i\.e|etc|vs|cf)\.", re.IGNORECASE)


@dataclass
class Section:
    title: str
    line: int
    body: list[tuple[int, str]] = field(default_factory=list)


def _content_lines(path: Path) -> list[tuple[int, str]]:
    """Lines outside frontmatter, code fences and HTML comments, with 1-based numbers."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = 0
    if lines and lines[0] == "---" and "---" in lines[1:]:
        start = lines.index("---", 1) + 1
    result = []
    fenced = False
    commented = False
    for number, line in enumerate(lines[start:], start=start + 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if commented or line.lstrip().startswith("<!--"):
            commented = "-->" not in line
            continue
        result.append((number, line))
    return result


def _sections(lines: list[tuple[int, str]], level: str) -> list[Section]:
    sections: list[Section] = []
    for number, line in lines:
        if line.startswith(level + " "):
            sections.append(Section(line[len(level) + 1 :].strip(), number))
        elif sections:
            sections[-1].body.append((number, line))
    return sections


def _tables(body: list[tuple[int, str]]) -> list[tuple[int, int]]:
    """(first line, row count without the header) of each table."""
    tables: list[tuple[int, int]] = []
    in_table = False
    for number, line in body:
        if TABLE_ROW.match(line):
            if not in_table:
                tables.append((number, 0))
                in_table = True
            elif not TABLE_DIVIDER.match(line):
                first, rows = tables[-1]
                tables[-1] = (first, rows + 1)
        else:
            in_table = False
    return tables


def _top_items(body: list[tuple[int, str]]) -> int:
    return sum(1 for _, line in body if (m := LIST_ITEM.match(line)) and not m[1])


def check_file(path: Path, display: str) -> list[str]:
    lang = "ko" if path.name.endswith(KO_SUFFIX) else "en"
    lines = _content_lines(path)
    problems = []
    if len(lines) > MAX_LINES:
        problems.append(f"{display}:1: {len(lines)} lines, limit {MAX_LINES}")
    for number, line in lines:
        if not (m := LIST_ITEM.match(line)):
            continue
        if m[1]:
            problems.append(f"{display}:{number}: nested list item, keep lists one level")
        if len(m[2]) > MAX_ITEM_CHARS[lang]:
            problems.append(
                f"{display}:{number}: list item of {len(m[2])} chars, limit {MAX_ITEM_CHARS[lang]}"
            )
    for section in _sections(lines, "##"):
        if section.title in GOALS:
            for first, rows in _tables(section.body):
                if rows > MAX_ITEMS:
                    problems.append(f"{display}:{first}: {rows} goal rows, limit {MAX_ITEMS}")
        elif section.title in COUNTED_LISTS:
            if (count := _top_items(section.body)) > MAX_ITEMS:
                problems.append(
                    f"{display}:{section.line}: {count} items in '{section.title}', "
                    f"limit {MAX_ITEMS}"
                )
        elif section.title in DESIGN:
            problems += _check_design(section, display)
    return problems


def _check_design(section: Section, display: str) -> list[str]:
    problems = []
    subsections = _sections(section.body, "###")
    if len(subsections) > MAX_DESIGN_SUBSECTIONS:
        problems.append(
            f"{display}:{section.line}: {len(subsections)} design subsections, "
            f"limit {MAX_DESIGN_SUBSECTIONS}"
        )
    first_sub = subsections[0].line if subsections else None
    lead = [(n, line) for n, line in section.body if first_sub is None or n < first_sub]
    for unit in [Section(section.title, section.line, lead), *subsections]:
        problems += _check_design_unit(unit, display)
    return problems


def _check_design_unit(unit: Section, display: str) -> list[str]:
    """Table and sentence limits of a design subsection, or of the text before the first one."""
    problems = []
    tables = _tables(unit.body)
    if len(tables) > MAX_DESIGN_TABLES:
        problems.append(f"{display}:{unit.line}: {len(tables)} tables, limit {MAX_DESIGN_TABLES}")
    for first, rows in tables:
        if rows > MAX_TABLE_ROWS:
            problems.append(f"{display}:{first}: {rows} table rows, limit {MAX_TABLE_ROWS}")
    sentences = 0
    for _, line in unit.body:
        text = line.strip()
        if not text or TABLE_ROW.match(line) or IMAGE.match(line):
            continue
        if text.startswith(REJECTED_PREFIXES):
            continue
        count = len(SENTENCE_END.findall(ABBREVIATION.sub("", line)))
        sentences += max(count, 1) if LIST_ITEM.match(line) else count
    if sentences > MAX_DESIGN_SENTENCES:
        problems.append(
            f"{display}:{unit.line}: {sentences} sentences in '{unit.title}', "
            f"limit {MAX_DESIGN_SENTENCES}"
        )
    return problems


def _default_paths(root: Path) -> list[Path]:
    paths = []
    for path in sorted((root / "proposals").glob("BEP-*")):
        if path.is_file() and (m := BEP_FILE.match(path.name)):
            if int(m[1]) >= FIRST_CHECKED_NUMBER:
                paths.append(path)
        elif path.is_dir() and (m := BEP_DIR.match(path.name)):
            if int(m[1]) >= FIRST_CHECKED_NUMBER:
                paths += sorted(path.glob("*.md"))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("paths", nargs="*", type=Path, help="check these files instead")
    args = parser.parse_args()
    paths = args.paths or _default_paths(args.root)
    problems = []
    for path in paths:
        display = str(path.relative_to(args.root)) if path.is_relative_to(args.root) else str(path)
        problems += check_file(path, display)
    for problem in problems:
        sys.stdout.write(problem + "\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
