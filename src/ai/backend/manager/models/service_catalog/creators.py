"""Creator specs for the service catalog."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.service_catalog import (
    ServiceCatalogEndpointID,
    ServiceCatalogID,
)
from ai.backend.manager.data.service_catalog.types import ServiceCatalogEndpointData
from ai.backend.manager.models.service_catalog.row import ServiceCatalogEndpointRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ServiceCatalogEndpointCreator(
    FieldCreator[ServiceCatalogID, ServiceCatalogEndpointRow, ServiceCatalogEndpointData]
):
    """Creator for one endpoint a service instance announced."""

    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: Mapping[str, Any] | None

    @override
    def build_row(self, owner_id: ServiceCatalogID) -> ServiceCatalogEndpointRow:
        return ServiceCatalogEndpointRow(
            service_id=owner_id,
            role=self.role,
            scope=self.scope,
            address=self.address,
            port=self.port,
            protocol=self.protocol,
            metadata_=dict(self.metadata) if self.metadata is not None else None,
        )

    @override
    def field_id(self, row: ServiceCatalogEndpointRow) -> ServiceCatalogEndpointID:
        return ServiceCatalogEndpointID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
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
