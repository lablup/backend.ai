from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.service_catalog.actions.base import ServiceCatalogAction

if TYPE_CHECKING:
    from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow


@dataclass
class SearchServiceCatalogsAction(ServiceCatalogAction):
    """Action to search service catalog entries."""

    service_group: str | None = None
    status: str | None = None
    first: int | None = None
    offset: int | None = None

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

    catalogs: list[ServiceCatalogRow]

    @override
    def entity_id(self) -> str | None:
        return None
