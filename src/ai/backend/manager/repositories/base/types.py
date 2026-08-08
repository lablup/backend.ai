"""Type definitions for repository layer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from ai.backend.common.identifier.entity import EntityID
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
class BulkResultWithFailures[TData]:
    """What a bulk write did to each entity the caller named.

    Named as the atomic bulk results are, minus a spec name it cannot carry — one type
    serves both the updater and the purger — leaving the part a caller has to know:
    some of these may have failed while the rest went through.

    Keyed by entity rather than positional: the bulk shape answers per entity, and an
    answer attached to the wrong one is worse than no answer.

    Ordering is per group, not the caller's. A caller that needs its own order re-reads
    these by the ids it passed in.

    Names its fields as the other bulk results do, so a caller reading ``successes`` and
    ``errors`` off this reads them the same way off ``BulkUpdaterResult``.
    """

    successes: dict[EntityID, TData]
    errors: dict[EntityID, Exception]
