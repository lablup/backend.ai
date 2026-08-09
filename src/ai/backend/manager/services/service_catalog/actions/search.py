from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.service_catalog import SERVICE_CATALOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.repositories.service_catalog.searchers import ServiceCatalogSearcher


@dataclass
class SearchServiceCatalogsAction(SearchGlobalOpsAction[ServiceCatalogRow, ServiceCatalogData]):
    """Page through the registered services."""

    searcher: ServiceCatalogSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SERVICE_CATALOG_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_search_service_catalogs"

    @override
    def to_searcher(self) -> ServiceCatalogSearcher:
        return self.searcher
