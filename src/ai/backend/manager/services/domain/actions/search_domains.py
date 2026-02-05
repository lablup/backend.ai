"""Search domains action and result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class SearchDomainsAction(DomainAction):
    """Action to search domains with filtering, ordering, and pagination.

    Args:
        querier: BatchQuerier containing filters, orders, and pagination options.
    """

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchDomainsActionResult(BaseActionResult):
    """Result of SearchDomainsAction.

    Args:
        items: List of domain data items in the current page.
        total_count: Total number of domains matching the filter.
        has_next_page: Whether there are more items after the current page.
        has_previous_page: Whether there are items before the current page.
    """

    items: list[DomainData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
