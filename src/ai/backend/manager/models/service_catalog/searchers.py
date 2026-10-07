"""Searcher implementations for the service catalog repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.service_catalog.searchable_fields import (
    ServiceCatalogSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ServiceCatalogSearcher(Searcher[ServiceCatalogRow, ServiceCatalogData]):
    """Reads registered services."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ServiceCatalogRow)

    @override
    def to_data(self, row: ServiceCatalogRow) -> ServiceCatalogData:
        return ServiceCatalogSearchableFields.own.to_data(row)
