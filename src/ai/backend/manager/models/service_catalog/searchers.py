"""Searcher implementations for the service catalog repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import with_expression

from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.models.base import PydanticListColumn
from ai.backend.manager.models.service_catalog.row import (
    ServiceCatalogEndpointRow,
    ServiceCatalogRow,
)
from ai.backend.manager.models.service_catalog.searchable_fields import (
    ServiceCatalogSearchableFields,
)
from ai.backend.manager.models.service_catalog.types import ServiceCatalogEndpointRowJson
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ServiceCatalogSearcher(Searcher[ServiceCatalogRow, ServiceCatalogData]):
    """Reads registered services with their endpoints aggregated beside each row.

    The endpoints are a to-many of the same entity rather than a second one, so the
    select stays single-entity: a correlated subquery folds them into one JSON array
    on ``endpoint_rows`` and the conversion unfolds it.
    """

    @staticmethod
    def _endpoint_rows_json() -> sa.sql.expression.ColumnElement[Any]:
        """The service's endpoint rows as one JSON array, keyed by column name."""
        endpoint = ServiceCatalogEndpointRow.__table__
        rows_json = (
            sa.select(sa.func.json_agg(sa.func.row_to_json(endpoint.table_valued())))
            .where(endpoint.c.service_id == ServiceCatalogRow.id)
            .correlate(ServiceCatalogRow)
            .scalar_subquery()
        )
        return sa.type_coerce(rows_json, PydanticListColumn(ServiceCatalogEndpointRowJson))

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ServiceCatalogRow).options(
            with_expression(ServiceCatalogRow.endpoint_rows, self._endpoint_rows_json())
        )

    @override
    def to_data(self, row: ServiceCatalogRow) -> ServiceCatalogData:
        return ServiceCatalogSearchableFields.own.to_data(row)
