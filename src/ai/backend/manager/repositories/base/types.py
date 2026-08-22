"""Type definitions for repository layer."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from ai.backend.manager.models.clauses import QueryCondition

# Moved to models/specs/types.py with the v2 spec lineage; re-imported here for the
# legacy spec modules that still import them from this path.
from ai.backend.manager.models.specs.types import ConflictCheck as ConflictCheck
from ai.backend.manager.models.specs.types import IntegrityErrorCheck as IntegrityErrorCheck

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

# Factory function that creates a cursor condition from a decoded cursor value (str or UUID)
type CursorConditionFactory = Callable[[str], QueryCondition]

TRow = TypeVar("TRow", bound="Row[Any]")


@dataclass
class LegacyBulkResultWithFailures[TData]:
    """What a legacy bulk write did to each row the caller named.

    Keyed by a bare uuid, unlike the v2 :class:`BulkResultWithFailures`: this path
    predates entity identifiers and goes away with it.
    """

    successes: dict[uuid.UUID, TData]
    errors: dict[uuid.UUID, Exception]
