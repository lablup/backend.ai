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
    """Rows tied to another entity by a use, found through ``correlation``.

    ``other_id`` is the other entity's id among the correlated rows. The correlation is
    built around the searched row, so one declaration answers one direction. Declare
    ``UsedByConditions`` or ``UsesConditions``, never this class.
    """

    _correlation: ToManyCorrelation
    _other_id: FilterColumn

    def __init__(self, correlation: ToManyCorrelation, other_id: FilterColumn) -> None:
        self._correlation = correlation
        self._other_id = other_id

    def _narrow(self, entity_id: TID) -> UsedBy:
        return UsedBy(
            target=entity_id,
            condition=self._correlation.some([lambda: self._other_id == entity_id]),
        )


class UsedByConditions[TID: EntityIdentifier](UsageConditions[TID]):
    """Rows the named entity uses. The searched side is the used one."""

    def used_by(self, entity_id: TID) -> UsedBy:
        """The rows the entity uses."""
        return self._narrow(entity_id)


class UsesConditions[TID: EntityIdentifier](UsageConditions[TID]):
    """Rows using the named entity. The searched side is the using one."""

    def uses(self, entity_id: TID) -> UsedBy:
        """The rows using the entity."""
        return self._narrow(entity_id)
