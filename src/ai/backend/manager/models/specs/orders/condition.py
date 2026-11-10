"""Order by whether a condition holds."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryCondition, QueryOrder


class ConditionOrder:
    """Puts the rows a condition holds for ahead of, or behind, the rest."""

    _condition: QueryCondition

    def __init__(self, condition: QueryCondition) -> None:
        self._condition = condition

    def first(self) -> QueryOrder:
        return self._condition().desc()

    def last(self) -> QueryOrder:
        return self._condition().asc()
