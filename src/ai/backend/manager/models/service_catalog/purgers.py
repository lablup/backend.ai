"""Purge specs for the service catalog."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.manager.data.service_catalog.types import ServiceCatalogEndpointData
from ai.backend.manager.models.service_catalog.row import ServiceCatalogEndpointRow
from ai.backend.manager.models.specs.purger import FieldBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ServiceCatalogEndpointBatchPurger(
    FieldBatchPurger[ServiceCatalogID, ServiceCatalogEndpointRow, ServiceCatalogEndpointData]
):
    """Every endpoint a service instance announced."""

    @override
    def build_subquery(
        self, owner_id: ServiceCatalogID
    ) -> sa.sql.Select[tuple[ServiceCatalogEndpointRow]]:
        return sa.select(ServiceCatalogEndpointRow).where(
            ServiceCatalogEndpointRow.service_id == owner_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ServiceCatalogEndpointRow) -> ServiceCatalogEndpointData:
        return ServiceCatalogEndpointData(
            id=row.id,
            service_id=row.service_id,
            role=row.role,
            scope=row.scope,
            address=row.address,
            port=row.port,
            protocol=row.protocol,
            metadata=row.metadata_,
        )
