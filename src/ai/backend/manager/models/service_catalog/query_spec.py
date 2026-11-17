"""What a service catalog search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.data.service_catalog.types import (
    ServiceCatalogData,
    ServiceCatalogEndpointData,
)
from ai.backend.manager.models.service_catalog.row import (
    ServiceCatalogEndpointRow,
    ServiceCatalogRow,
)
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedQueryColumn, QueryColumn


class _ServiceCatalogEndpointOwnColumns(
    RowDataConverter[ServiceCatalogEndpointRow, ServiceCatalogEndpointData]
):
    """An endpoint row's own columns."""

    field_id = QueryColumn(
        ServiceCatalogEndpointRow.id,
        UUIDConditions(ServiceCatalogEndpointRow.id),
        ColumnOrder(ServiceCatalogEndpointRow.id),
    )
    service_id = QueryColumn(
        ServiceCatalogEndpointRow.service_id,
        UUIDConditions(ServiceCatalogEndpointRow.service_id),
        ColumnOrder(ServiceCatalogEndpointRow.service_id),
    )
    role = QueryColumn(
        ServiceCatalogEndpointRow.role,
        StringConditions(ServiceCatalogEndpointRow.role),
        ColumnOrder(ServiceCatalogEndpointRow.role),
    )
    scope = QueryColumn(
        ServiceCatalogEndpointRow.scope,
        StringConditions(ServiceCatalogEndpointRow.scope),
        ColumnOrder(ServiceCatalogEndpointRow.scope),
    )
    address = QueryColumn(
        ServiceCatalogEndpointRow.address,
        StringConditions(ServiceCatalogEndpointRow.address),
        ColumnOrder(ServiceCatalogEndpointRow.address),
    )
    port = QueryColumn(
        ServiceCatalogEndpointRow.port,
        IntConditions(ServiceCatalogEndpointRow.port),
        ColumnOrder(ServiceCatalogEndpointRow.port),
    )
    protocol = QueryColumn(
        ServiceCatalogEndpointRow.protocol,
        StringConditions(ServiceCatalogEndpointRow.protocol),
        ColumnOrder(ServiceCatalogEndpointRow.protocol),
    )
    metadata_ = QueryColumn(ServiceCatalogEndpointRow.metadata_, None, None)
    """Impossible: a JSON document of endpoint metadata."""

    @override
    def to_data(self, row: ServiceCatalogEndpointRow) -> ServiceCatalogEndpointData:
        return ServiceCatalogEndpointData(
            id=ServiceCatalogID(self.field_id.read(row)),
            service_id=ServiceCatalogID(self.service_id.read(row)),
            role=self.role.read(row),
            scope=self.scope.read(row),
            address=self.address.read(row),
            port=self.port.read(row),
            protocol=self.protocol.read(row),
            metadata=self.metadata_.read(row),
        )


class ServiceCatalogEndpointQuerySpec:
    own = _ServiceCatalogEndpointOwnColumns()


class _ServiceCatalogOwnColumns(RowDataConverter[ServiceCatalogRow, ServiceCatalogData]):
    """The registered service's own columns. ``endpoints`` are declared in ``nested``."""

    id = QueryColumn(
        ServiceCatalogRow.id,
        UUIDConditions(ServiceCatalogRow.id),
        ColumnOrder(ServiceCatalogRow.id),
    )
    service_group = QueryColumn(
        ServiceCatalogRow.service_group,
        StringConditions(ServiceCatalogRow.service_group),
        ColumnOrder(ServiceCatalogRow.service_group),
    )
    instance_id = QueryColumn(
        ServiceCatalogRow.instance_id,
        StringConditions(ServiceCatalogRow.instance_id),
        ColumnOrder(ServiceCatalogRow.instance_id),
    )
    display_name = QueryColumn(
        ServiceCatalogRow.display_name,
        StringConditions(ServiceCatalogRow.display_name),
        ColumnOrder(ServiceCatalogRow.display_name),
    )
    version = QueryColumn(
        ServiceCatalogRow.version,
        StringConditions(ServiceCatalogRow.version),
        ColumnOrder(ServiceCatalogRow.version),
    )
    labels = QueryColumn(ServiceCatalogRow.labels, None, None)
    """Impossible: a JSON document of the service's labels."""
    status = QueryColumn(
        ServiceCatalogRow.status,
        EnumConditions(ServiceCatalogRow.status, ServiceCatalogStatus),
        ColumnOrder(ServiceCatalogRow.status),
    )
    startup_time = QueryColumn(
        ServiceCatalogRow.startup_time,
        DateTimeConditions(ServiceCatalogRow.startup_time),
        ColumnOrder(ServiceCatalogRow.startup_time),
    )
    registered_at = QueryColumn(
        ServiceCatalogRow.registered_at,
        DateTimeConditions(ServiceCatalogRow.registered_at),
        ColumnOrder(ServiceCatalogRow.registered_at),
    )
    last_heartbeat = QueryColumn(
        ServiceCatalogRow.last_heartbeat,
        DateTimeConditions(ServiceCatalogRow.last_heartbeat),
        ColumnOrder(ServiceCatalogRow.last_heartbeat),
    )
    config_hash = QueryColumn(
        ServiceCatalogRow.config_hash,
        StringConditions(ServiceCatalogRow.config_hash),
        ColumnOrder(ServiceCatalogRow.config_hash),
    )

    @override
    def to_data(self, row: ServiceCatalogRow) -> ServiceCatalogData:
        return ServiceCatalogData(
            id=ServiceCatalogID(self.id.read(row)),
            service_group=self.service_group.read(row),
            instance_id=self.instance_id.read(row),
            display_name=self.display_name.read(row),
            version=self.version.read(row),
            labels=self.labels.read(row),
            status=self.status.read(row),
            startup_time=self.startup_time.read(row),
            registered_at=self.registered_at.read(row),
            last_heartbeat=self.last_heartbeat.read(row),
            config_hash=self.config_hash.read(row),
        )


class _ServiceCatalogNestedColumns:
    """The endpoints the registered service exposes."""

    endpoints = NestedQueryColumn(
        ServiceCatalogEndpointQuerySpec.own,
        ToManyCorrelation(
            ServiceCatalogEndpointRow,
            ServiceCatalogRow,
            ServiceCatalogEndpointRow.service_id == ServiceCatalogRow.id,
        ),
    )


class ServiceCatalogQuerySpec:
    own = _ServiceCatalogOwnColumns()
    nested = _ServiceCatalogNestedColumns
