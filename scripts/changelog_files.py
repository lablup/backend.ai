"""Mapping rule from a release version to the changelog file holding it.

The changelog is split per version branch: every release of the ``26.9`` branch —
``26.9.0rc1``, ``26.9.0``, ``26.9.1`` — writes into ``CHANGELOG/26.9.md``. Each
release keeps its own heading block within that file; consolidating the
pre-release blocks into the final one is a release-time editorial step.

The root ``CHANGELOG.md`` is the frozen archive of releases up to 26.8.

Shared by ``run-towncrier.py`` (which writes the block) and
``extract-release-changelog.py`` (which reads it back).
"""

from __future__ import annotations

import re

# PEP 440 pre-release / post-release / development-release suffixes.
_SUFFIX_RE = re.compile(
    r"[._-]?(alpha|beta|preview|pre|rev|post|dev|rc|a|b|c|r)\d*$",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)(?:\.\d+)*$")

CHANGELOG_DIR = "CHANGELOG"


def changelog_filename(version: str) -> str:
    """Return the changelog path holding the given release version."""
    base = _SUFFIX_RE.sub("", version.strip())
    match = _VERSION_RE.match(base)
    if match is None:
        raise ValueError(f"Unrecognized release version: {version!r}")
    return f"{CHANGELOG_DIR}/{match.group(1)}.{match.group(2)}.md"
