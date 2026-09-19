"""Conditions on which other entity uses a row."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation


@dataclass(frozen=True)
class UsedBy:
    """An entity whose use narrows a scoped operation, and the rows it uses.

    The caller must be able to read ``target``; the use grants nothing.
    """

    target: EntityIdentifier
    condition: QueryCondition


class UsageConditions[TID: EntityIdentifier]:
    """Rows another entity uses, found through ``correlation``.

    ``using_id`` is the using entity's id among the correlated rows.
    """

    _correlation: ToManyCorrelation
    _using_id: FilterColumn

    def __init__(self, correlation: ToManyCorrelation, using_id: FilterColumn) -> None:
        self._correlation = correlation
        self._using_id = using_id

    def used_by(self, entity_id: TID) -> UsedBy:
        """The rows the entity uses."""
        return UsedBy(
            target=entity_id,
            condition=self._correlation.some([lambda: self._using_id == entity_id]),
        )
