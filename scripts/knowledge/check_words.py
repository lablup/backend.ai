#!/usr/bin/env python3
"""Find words the glossary rejects in documents.

Usage:
    python3 scripts/knowledge/check_words.py [--root DIR] [--base REF] [PATH ...]

Reads the rejected words from `GLOSSARY.md`, `glossary/<topic>.md` and their
`.ko.md` pairs. With --base, checks the lines of `.md` files added since REF. With
PATH, checks those whole files.

Term variants and expressions with a qualifier in parentheses have other valid
meanings, so a match prints as "review:" and does not fail. Code spans, fenced
blocks, frontmatter, the glossary and `report.md` are not checked. Exits 1 when any
other match exists. CI runs this via knowledge-check.yml.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

KO_SUFFIX = ".ko.md"
EXPRESSION_HEADERS = {"사용하지 않는 표현": False, "Do not write": True}
TERM_HEADERS = ("사용하지 않는 어휘", "Do not write")
SKIPPED_NAMES = frozenset({"report.md", "report.ko.md", "GLOSSARY.md", "GLOSSARY.ko.md"})
SKIPPED_PARTS = frozenset({"glossary"})
HANGUL = "가-힣"
PARTICLES = "은는이가을를의에도로와과만"
QUALIFIER = re.compile(r"\s*\([^)]*\)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"`[^`]*`")
HUNK = re.compile(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@")
DIFF_FILE = re.compile(r"^\+\+\+ b/(.+)$")

SYLLABLE_BASE = 0xAC00
VOWEL_COUNT = 21
FINAL_COUNT = 28
FINAL_N = 4
FINAL_L = 8
FINAL_B = 17
FINAL_SS = 20
# Vowel index of the stem to the vowel index after adding 아/어.
CONTRACTED_VOWELS = {18: 4, 20: 6, 13: 14, 8: 9}
CONSONANT_ENDINGS = "다고지는면며기게던니시겠"
VOWEL_ENDINGS = "아어았었은을습"


@dataclass(frozen=True)
class Word:
    text: str
    replacement: str
    pattern: re.Pattern[str]
    advisory: bool


def _with_final(syllable: str, final: int) -> str:
    return chr(ord(syllable) + final)


def _split(syllable: str) -> tuple[int, int, int]:
    offset = ord(syllable) - SYLLABLE_BASE
    return (
        offset // (VOWEL_COUNT * FINAL_COUNT),
        offset // FINAL_COUNT % VOWEL_COUNT,
        offset % FINAL_COUNT,
    )


def _join(initial: int, vowel: int, final: int = 0) -> str:
    return chr(SYLLABLE_BASE + (initial * VOWEL_COUNT + vowel) * FINAL_COUNT + final)


def _verb_forms(stem: str) -> list[str]:
    """Return the regex alternatives of a verb stem's inflected forms."""
    head, last = stem[:-1], stem[-1]
    initial, vowel, final = _split(last)
    consonant = f"{stem}[{CONSONANT_ENDINGS}]"
    if final == FINAL_L:
        dropped = head + _join(initial, vowel)
        return [
            consonant,
            f"{stem}[{VOWEL_ENDINGS}]",
            f"{dropped}[는니]",
            head + _with_final(_join(initial, vowel), FINAL_N),
        ]
    if final:
        return [consonant, f"{stem}[{VOWEL_ENDINGS}]"]
    forms = [
        consonant,
        head + _with_final(last, FINAL_N),
        head + _with_final(last, FINAL_L),
        head + _with_final(last, FINAL_B),
    ]
    if last == "하":
        contracted = "해"
    elif last == "르" and head:
        prior_initial, prior_vowel, _ = _split(head[-1])
        return [*forms, head[:-1] + _join(prior_initial, prior_vowel, FINAL_L) + "[러라렀랐]"]
    else:
        contracted = _join(initial, CONTRACTED_VOWELS.get(vowel, vowel))
    return [*forms, head + contracted, head + _with_final(contracted, FINAL_SS)]


def _korean_pattern(text: str) -> re.Pattern[str]:
    clean = text.replace("~", " ").strip()
    tokens = clean.split()
    last = tokens[-1]
    prefix = r"\s+".join(re.escape(token) for token in tokens[:-1])
    if len(tokens) > 1 and "~" in text and text.index("~") > 0:
        prefix = (
            re.escape(tokens[0])
            + r"\s+.*?"
            + r"\s*".join(re.escape(token) for token in tokens[1:-1])
        )
    if last.endswith("다") and len(last) > 1:
        ending = "(?:" + "|".join(_verb_forms(last[:-1])) + ")"
    else:
        ending = re.escape(last) + f"(?:[{PARTICLES}]|으로|이다|입니다)?(?![{HANGUL}])"
    body = rf"{prefix}\s+{ending}" if prefix else ending
    boundary = "" if text.startswith("~") else f"(?<![{HANGUL}])"
    return re.compile(boundary + body)


def _english_pattern(text: str) -> re.Pattern[str]:
    words = r"\s+".join(re.escape(word) for word in text.split())
    return re.compile(rf"(?<![\w-]){words}(?:s|es|d|ed|ing)?(?![\w-])")


def _pattern(text: str) -> re.Pattern[str]:
    return _korean_pattern(text) if re.search(f"[{HANGUL}]", text) else _english_pattern(text)


def _alternatives(cell: str) -> list[str]:
    """Split a cell, carrying a shared leading word into the alternatives after it."""
    parts = [part.strip() for part in re.split(r"\s*/\s*|,\s+", cell) if part.strip()]
    if not parts:
        return []
    leading = parts[0].split()[:-1]
    return [parts[0]] + [
        " ".join([*leading, part])
        if leading and len(part.split()) == 1 and part.endswith("다")
        else part
        for part in parts[1:]
    ]


def _table_rows(path: Path) -> list[list[str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def _expressions(path: Path) -> list[Word]:
    words = []
    in_table = False
    for row in _table_rows(path):
        if row[0] in EXPRESSION_HEADERS and len(row) == 2:
            in_table = True
            continue
        if not in_table or len(row) != 2:
            in_table = False
            continue
        cell, replacement = row
        advisory = bool(QUALIFIER.search(cell))
        for text in _alternatives(QUALIFIER.sub("", cell)):
            if text.lower() not in replacement.lower():
                words.append(Word(text, replacement, _pattern(text), advisory))
    return words


def _terms(path: Path) -> list[Word]:
    rows = _table_rows(path)
    header = next((row for row in rows if any(name in row for name in TERM_HEADERS)), None)
    if header is None:
        return []
    variant_at = next(header.index(name) for name in TERM_HEADERS if name in header)
    words = []
    for row in rows:
        if row is header or len(row) != len(header):
            continue
        term = row[0]
        for text in re.split(r",\s+", row[variant_at]):
            if text and text.lower() != term.lower():
                words.append(Word(text, term, _pattern(text), True))
    return words


def load_words(root: Path) -> tuple[list[Word], list[Word]]:
    """Return the rejected words of English documents and of Korean documents."""
    english = _expressions(root / "GLOSSARY.md")
    korean = _expressions(root / "GLOSSARY.ko.md")
    for path in sorted((root / "glossary").glob("*.md")):
        (korean if path.name.endswith(KO_SUFFIX) else english).extend(_terms(path))
    return english, korean


def _is_skipped(path: str) -> bool:
    parts = Path(path).parts
    return parts[-1] in SKIPPED_NAMES or bool(SKIPPED_PARTS.intersection(parts))


def _prose_lines(text: str) -> dict[int, str]:
    """Return line number to text, without frontmatter, fenced blocks and code spans."""
    lines = text.splitlines()
    start = lines.index("---", 1) + 1 if lines and lines[0] == "---" and "---" in lines[1:] else 0
    prose = {}
    fenced = False
    for number, line in enumerate(lines[start:], start + 1):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            prose[number] = CODE_SPAN.sub(" ", line)
    return prose


def _added_lines(root: Path, base: str) -> dict[str, set[int]]:
    diff = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--unified=0",
            "--no-color",
            "--diff-filter=d",
            f"{base}...HEAD",
            "--",
            "*.md",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    added: dict[str, set[int]] = {}
    current = ""
    for line in diff.splitlines():
        if match := DIFF_FILE.match(line):
            current = match[1]
        elif match := HUNK.match(line):
            first, count = int(match[1]), int(match[2] or 1)
            added.setdefault(current, set()).update(range(first, first + count))
    return added


def check_file(
    root: Path,
    path: str,
    numbers: set[int] | None,
    english: list[Word],
    korean: list[Word],
) -> tuple[list[str], list[str]]:
    words = korean if path.endswith(KO_SUFFIX) else english
    problems: list[str] = []
    reviews: list[str] = []
    for number, line in _prose_lines((root / path).read_text(encoding="utf-8")).items():
        if numbers is not None and number not in numbers:
            continue
        for word in words:
            if word.pattern.search(line):
                message = f"{path}:{number}: {word.text} -> {word.replacement}: {line.strip()}"
                (reviews if word.advisory else problems).append(message)
    return problems, reviews


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", help="check the lines added since this git ref")
    parser.add_argument("paths", nargs="*", help="check these whole files")
    args = parser.parse_args()
    english, korean = load_words(args.root)
    targets: dict[str, set[int] | None] = {}
    if args.base:
        targets.update(_added_lines(args.root, args.base))
    targets.update(dict.fromkeys(args.paths))
    problems: list[str] = []
    reviews: list[str] = []
    for path, numbers in sorted(targets.items()):
        if not _is_skipped(path):
            file_problems, file_reviews = check_file(args.root, path, numbers, english, korean)
            problems += file_problems
            reviews += file_reviews
    for review in reviews:
        print(f"review: {review}")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
