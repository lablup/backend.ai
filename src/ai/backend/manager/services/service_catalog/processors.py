from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.service_catalog.actions.search import (
    SearchServiceCatalogsAction,
    SearchServiceCatalogsActionResult,
)
from ai.backend.manager.services.service_catalog.service import ServiceCatalogService


class ServiceCatalogProcessors(AbstractProcessorPackage):
    """Processor package for service catalog operations."""

    search_service_catalogs: ActionProcessor[
        SearchServiceCatalogsAction, SearchServiceCatalogsActionResult
    ]

    def __init__(
        self, service: ServiceCatalogService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.search_service_catalogs = ActionProcessor(
            service.search_service_catalogs, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            SearchServiceCatalogsAction.spec(),
        ]
