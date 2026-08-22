from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.services.service_catalog.actions.search import (
    SearchServiceCatalogsAction,
)


class ServiceCatalogProcessors:
    """The search runs straight against ops, so this domain has no service."""

    global_search_service_catalogs: GlobalActionProcessor[
        SearchServiceCatalogsAction,
        BatchOpsResult[ServiceCatalogData],
    ]

    def __init__(self, group: ProcessorGroup[ServiceCatalogData]) -> None:
        self.global_search_service_catalogs = group.global_search_ops(SearchServiceCatalogsAction)
