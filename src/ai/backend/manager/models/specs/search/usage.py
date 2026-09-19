"""Conditions on which other entity uses a row."""

from __future__ import annotations

import uuid

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation


class UsageConditions:
    """Rows another entity uses, found through ``correlation``.

    ``using_id`` is the using entity's id among the correlated rows. A usage narrows a
    search and grants nothing; the caller's read of the using entity is checked elsewhere.
    """

    _correlation: ToManyCorrelation
    _using_id: FilterColumn

    def __init__(self, correlation: ToManyCorrelation, using_id: FilterColumn) -> None:
        self._correlation = correlation
        self._using_id = using_id

    def used_by(self, entity_id: uuid.UUID) -> QueryCondition:
        """Rows the entity uses."""
        return self._correlation.some([lambda: self._using_id == entity_id])
