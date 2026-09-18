"""Base of the orders a searchable field declares."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.manager.models.clauses import QueryOrder


class SearchOrder(ABC):
    """Orders a query by one field."""

    @abstractmethod
    def apply(self, ascending: bool) -> QueryOrder:
        raise NotImplementedError
