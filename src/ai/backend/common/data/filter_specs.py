from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class StringMatchSpec:
    """Specification for string matching operations in query conditions."""

    value: str
    case_insensitive: bool
    negated: bool


@dataclass(frozen=True)
class UUIDEqualMatchSpec:
    """Specification for UUID equality operations (=, !=)."""

    value: uuid.UUID
    negated: bool


@dataclass(frozen=True)
class UUIDInMatchSpec:
    """Specification for UUID IN operations (IN, NOT IN)."""

    values: list[uuid.UUID]
    negated: bool
