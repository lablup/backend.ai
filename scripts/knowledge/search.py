#!/usr/bin/env python3
"""Search KNOWLEDGE.md documents by their frontmatter.

Usage:
    python3 scripts/knowledge/search.py [TERM ...] [--root DIR]

Without terms, lists every KNOWLEDGE.md. With terms, prints the documents
whose name, type, keywords, description, or path contain every term
(case-insensitive substring match). Read the description to decide whether
to open the file; do not open every match.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from frontmatter import (
    KnowledgeDocument,
    ParseError,
    build_document,
    iter_knowledge_files,
    load,
)


def matches(terms: list[str], relative_path: str, document: KnowledgeDocument) -> bool:
    haystack = " ".join((
        relative_path,
        document.name,
        document.type,
        " ".join(document.keywords),
        document.description,
    )).lower()
    return all(term.lower() in haystack for term in terms)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="*", help="terms that must all match")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="repository root to search under (default: current directory)",
    )
    args = parser.parse_args()

    for path in iter_knowledge_files(args.root):
        relative_path = str(path.relative_to(args.root))
        try:
            raw, _ = load(path)
        except ParseError as exc:
            print(f"{relative_path}: skipped, {exc}", file=sys.stderr)
            continue
        document, problems = build_document(raw)
        if document is None:
            print(f"{relative_path}: skipped, {problems[0]}", file=sys.stderr)
            continue
        if args.terms and not matches(args.terms, relative_path, document):
            continue
        print(relative_path)
        print(f"  {document.name} ({document.type}, {document.status})")
        print(f"  {document.description}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
