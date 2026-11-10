from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.services.service_catalog.actions.bulk_get import (
    BulkGetServiceCatalogsAction,
)
from ai.backend.manager.services.service_catalog.actions.search import (
    SearchServiceCatalogsAction,
)
from ai.backend.manager.services.service_catalog.service import ServiceCatalogService


class ServiceCatalogProcessors:
    """The search runs straight against ops; the bulk read keeps a service, which reads
    the endpoints of the services it found in a second query."""

    global_search_service_catalogs: GlobalActionProcessor[
        SearchServiceCatalogsAction,
        BatchOpsResult[ServiceCatalogData],
    ]
    bulk_get: PartialBulkActionProcessor[BulkGetServiceCatalogsAction, ServiceCatalogData]

    def __init__(
        self, group: ProcessorGroup[ServiceCatalogData], service: ServiceCatalogService
    ) -> None:
        self.global_search_service_catalogs = group.global_searcher_ops(SearchServiceCatalogsAction)
        self.bulk_get = group.partial_bulk(BulkGetServiceCatalogsAction, service.bulk_get)
