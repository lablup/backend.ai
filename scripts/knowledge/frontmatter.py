"""Frontmatter schema and parser for KNOWLEDGE.md files.

The schema is the `KnowledgeDocument` dataclass: `build_document` turns parsed
frontmatter into a typed document while collecting every schema violation.
Environment-dependent checks (path existence, cross-file name uniqueness, body
links) live in `check.py`.

The parser accepts only the YAML subset the schema uses — scalars, inline
lists, block lists (of scalars or flat mappings), and one level of nested
mapping. Anything else is a parse error on purpose: the schema is fixed, so an
unparseable file is a nonconforming file. Stdlib only.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATUS_VALUES = frozenset({"draft", "stable", "deprecated"})
DEFAULT_STATUS = "stable"

SKIP_DIR_PREFIXES = (".",)
SKIP_DIR_NAMES = frozenset({"node_modules", "dist", "build"})


@dataclass(frozen=True)
class Signature:
    """An actor and the date they acted — the shape of generated/verified.

    `by` follows the actor convention: `<producer>/<version>` for agents,
    `human:<id>` for people. `at` is an ISO date (YYYY-MM-DD).
    """

    by: str
    at: str


@dataclass(frozen=True)
class KnowledgeDocument:
    """A KNOWLEDGE.md frontmatter, validated against the schema."""

    name: str
    type: str
    description: str
    scope: str
    generated: Signature
    keywords: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    verified: tuple[Signature, ...] = ()
    status: str = DEFAULT_STATUS


def build_document(
    raw: Mapping[str, object],
) -> tuple[KnowledgeDocument | None, list[str]]:
    """Validate raw frontmatter against the schema.

    Returns the typed document (None when a required field is unusable) and
    every schema violation found — the document may build even with recorded
    problems, so callers report the problems regardless.
    """
    problems: list[str] = []

    name = _required_str(raw, "name", problems)
    if name and not NAME_PATTERN.match(name):
        problems.append(f"name {name!r} is not kebab-case")
    doc_type = _required_str(raw, "type", problems)
    description = _required_str(raw, "description", problems)
    scope = _required_str(raw, "scope", problems)
    generated = _signature(raw.get("generated"), "generated", problems)

    raw_status = raw.get("status", DEFAULT_STATUS)
    status = raw_status if isinstance(raw_status, str) else ""
    if status not in STATUS_VALUES:
        problems.append(f"status {raw_status!r} is not one of {sorted(STATUS_VALUES)}")
        status = DEFAULT_STATUS

    keywords = _str_tuple(raw, "keywords", problems)
    sources = _str_tuple(raw, "sources", problems)
    verified = _verified_tuple(raw.get("verified"), problems)

    if generated and verified:
        latest = max(entry.at for entry in verified)
        if latest < generated.at:
            problems.append(
                f"verified ({latest}) is older than generated ({generated.at}) — "
                "a meaningful change must clear 'verified'"
            )

    if not (name and doc_type and description and scope and generated):
        return None, problems
    document = KnowledgeDocument(
        name=name,
        type=doc_type,
        description=description,
        scope=scope,
        generated=generated,
        keywords=keywords,
        sources=sources,
        verified=verified,
        status=status,
    )
    return document, problems


def _required_str(raw: Mapping[str, object], key: str, problems: list[str]) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        problems.append(f"missing or empty required field '{key}'")
        return ""
    return value.strip()


def _str_tuple(
    raw: Mapping[str, object], key: str, problems: list[str]
) -> tuple[str, ...]:
    value = raw.get(key)
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        problems.append(f"'{key}' must be a list of strings")
        return ()
    return tuple(value)


def _signature(value: object, key: str, problems: list[str]) -> Signature | None:
    if not isinstance(value, dict) or not value.get("by") or not value.get("at"):
        problems.append(f"missing '{key}' with 'by' and 'at'")
        return None
    at = str(value["at"])
    if not DATE_PATTERN.match(at):
        problems.append(f"{key}.at must be YYYY-MM-DD, got {at!r}")
        return None
    return Signature(by=str(value["by"]), at=at)


def _verified_tuple(value: object, problems: list[str]) -> tuple[Signature, ...]:
    if value is None:
        return ()
    entries = value if isinstance(value, list) else [value]
    signatures: list[Signature] = []
    for entry in entries:
        signature = _signature(entry, "verified", problems)
        if signature is None:
            return ()
        signatures.append(signature)
    return tuple(signatures)


class ParseError(Exception):
    def __init__(self, line_no: int, message: str) -> None:
        super().__init__(f"frontmatter line {line_no}: {message}")
        self.line_no = line_no


def iter_knowledge_files(root: Path) -> Iterator[Path]:
    """Yield every KNOWLEDGE.md under root, skipping hidden and build directories.

    One document per package — an oversized document means the package should
    split, not the file (see the /knowledge skill).
    """
    for path in sorted(root.rglob("KNOWLEDGE.md")):
        relative_parts = path.relative_to(root).parts[:-1]
        if any(
            part.startswith(SKIP_DIR_PREFIXES) or part in SKIP_DIR_NAMES
            for part in relative_parts
        ):
            continue
        yield path


def load(path: Path) -> tuple[dict[str, object], list[str]]:
    """Return (raw frontmatter, body lines) for a KNOWLEDGE.md file.

    Raises ParseError when the frontmatter fence is missing or malformed.
    """
    document = _split_document(path.read_text(encoding="utf-8"))
    if document is None:
        raise ParseError(1, "missing or unclosed '---' frontmatter fence")
    frontmatter_lines, body_lines = document
    return _parse_frontmatter(frontmatter_lines), body_lines


_KEY_VALUE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$")


def _split_document(text: str) -> tuple[list[str], list[str]] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], lines[index + 1 :]
    return None


def _parse_frontmatter(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[0].isspace():
            raise ParseError(index + 1, f"unexpected indentation: {line.strip()!r}")
        matched = _KEY_VALUE.match(line)
        if matched is None:
            raise ParseError(index + 1, f"expected 'key: value', got {line.strip()!r}")
        key, rest = matched.group(1), matched.group(2).strip()
        if rest:
            data[key] = _parse_inline(rest)
            index += 1
            continue
        value, index = _parse_block(lines, index + 1)
        data[key] = value
    return data


def _parse_inline(raw: str) -> str | list[str]:
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_unquote(item) for item in inner.split(",")]
    return _unquote(raw)


def _unquote(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return value


def _parse_block(
    lines: list[str], start: int
) -> tuple[list[object] | dict[str, str], int]:
    """Parse the indented block after a bare ``key:`` line.

    Returns the parsed value and the index of the first line after the block.
    """
    items: list[object] = []
    mapping: dict[str, str] = {}
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if not line[0].isspace():
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            entry, index = _parse_list_item(lines, index)
            items.append(entry)
        else:
            matched = _KEY_VALUE.match(stripped)
            if matched is None or not matched.group(2).strip():
                raise ParseError(
                    index + 1,
                    "expected '- item' or 'key: value' (one nesting level only), "
                    f"got {stripped!r}",
                )
            mapping[matched.group(1)] = _unquote(matched.group(2))
            index += 1
    if items and mapping:
        raise ParseError(index, "a block cannot mix list items and mapping entries")
    return (items if items else mapping), index


def _parse_list_item(lines: list[str], start: int) -> tuple[object, int]:
    """Parse one ``- item`` entry, consuming continuation lines of a flat mapping."""
    stripped = lines[start].strip()
    item = stripped[2:].strip()
    matched = _KEY_VALUE.match(item)
    if matched is None or not matched.group(2).strip():
        return _unquote(item), start + 1
    entry: dict[str, str] = {matched.group(1): _unquote(matched.group(2))}
    index = start + 1
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        stripped = line.strip()
        if not line[0].isspace() or stripped.startswith("- "):
            break
        continued = _KEY_VALUE.match(stripped)
        if continued is None or not continued.group(2).strip():
            raise ParseError(
                index + 1, f"expected 'key: value' inside a list entry, got {stripped!r}"
            )
        entry[continued.group(1)] = _unquote(continued.group(2))
        index += 1
    return entry, index
