"""Type definitions for repository layer."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import (
    BulkResultWithFailures as BulkResultWithFailures,
)

# Moved to models/specs/types.py with the v2 spec lineage; re-imported here for the
# legacy spec modules that still import them from this path.
from ai.backend.manager.models.specs.types import ConflictCheck as ConflictCheck
from ai.backend.manager.models.specs.types import IntegrityErrorCheck as IntegrityErrorCheck

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

# Factory function that creates a cursor condition from a decoded cursor value (str or UUID)
type CursorConditionFactory = Callable[[str], QueryCondition]

TRow = TypeVar("TRow", bound="Row[Any]")
