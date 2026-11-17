"""Read specs for the service catalog table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.models.service_catalog.query_spec import (
    ServiceCatalogQuerySpec,
)
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkServiceCatalogQuerier(BulkEntityQuerier[ServiceCatalogRow, ServiceCatalogData]):
    """The registered services the caller named."""

    @override
    def row_class(self) -> type[ServiceCatalogRow]:
        return ServiceCatalogRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ServiceCatalogRow.id

    @override
    def to_data(self, row: ServiceCatalogRow) -> ServiceCatalogData:
        return ServiceCatalogQuerySpec.own.to_data(row)
