"""Search resource group-scoped domains action and result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.domain.types import DomainSearchScope
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class SearchRGDomainsAction(DomainAction):
    """Action to search domains within a resource group scope.

    Returns only domains that are associated with the specified resource group
    through the sgroups_for_domains relationship.

    Args:
        scope: DomainSearchScope containing resource_group filter.
        querier: BatchQuerier containing additional filters, orders, and pagination.
    """

    scope: DomainSearchScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return self.scope.resource_group

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchRGDomainsActionResult(BaseActionResult):
    """Result of SearchRGDomainsAction.

    Args:
        items: List of domain data items in the current page.
        total_count: Total number of domains matching the filter within the scope.
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
