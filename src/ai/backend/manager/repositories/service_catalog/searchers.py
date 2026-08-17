"""Searcher implementations for the service catalog repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.manager.data.service_catalog.types import (
    ServiceCatalogData,
    ServiceCatalogEndpointData,
)
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ServiceCatalogSearcher(Searcher[ServiceCatalogRow, ServiceCatalogData]):
    """Reads registered services with their endpoints eagerly loaded.

    The endpoints are a to-many of the same entity rather than a second one, so the
    select stays single-entity and the conversion assembles the nested value.
    """

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ServiceCatalogRow).options(selectinload(ServiceCatalogRow.endpoints))

    @override
    def to_data(self, row: ServiceCatalogRow) -> ServiceCatalogData:
        return ServiceCatalogData(
            id=row.id,
            service_group=row.service_group,
            instance_id=row.instance_id,
            display_name=row.display_name,
            version=row.version,
            labels=row.labels,
            status=row.status,
            startup_time=row.startup_time,
            registered_at=row.registered_at,
            last_heartbeat=row.last_heartbeat,
            config_hash=row.config_hash,
            endpoints=[
                ServiceCatalogEndpointData(
                    id=endpoint.id,
                    service_id=endpoint.service_id,
                    role=endpoint.role,
                    scope=endpoint.scope,
                    address=endpoint.address,
                    port=endpoint.port,
                    protocol=endpoint.protocol,
                    metadata=endpoint.metadata_,
                )
                for endpoint in row.endpoints
            ],
        )
