from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.service_catalog.actions.base import ServiceCatalogAction


@dataclass
class SearchServiceCatalogsAction(ServiceCatalogAction):
    """Action to search service catalog entries."""

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchServiceCatalogsActionResult(BaseActionResult):
    """Result of searching service catalog entries."""

    data: list[ServiceCatalogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
