"""What a domain search can filter and order by, and how a domain row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.manager.data.domain.types import DomainData, DomainStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.conditions.array import ArrayConditions
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import QueryColumn


class _DomainOwnColumns(RowDataConverter[DomainRow, DomainData]):
    """The domain's own columns."""

    id = QueryColumn(DomainRow.id, UUIDConditions(DomainRow.id), ColumnOrder(DomainRow.id))
    name = QueryColumn(
        DomainRow.name,
        StringConditions(sa.type_coerce(DomainRow.name, sa.String())),
        ColumnOrder(DomainRow.name),
    )
    description = QueryColumn(
        DomainRow.description,
        StringConditions(DomainRow.description),
        ColumnOrder(DomainRow.description),
    )
    is_active = QueryColumn(
        DomainRow.is_active,
        BoolConditions(DomainRow.is_active),
        ColumnOrder(DomainRow.is_active),
    )
    is_default = QueryColumn(
        DomainRow.is_default,
        BoolConditions(DomainRow.is_default),
        ColumnOrder(DomainRow.is_default),
    )
    status = QueryColumn(
        DomainRow.status,
        EnumConditions(DomainRow.status, DomainStatus),
        ColumnOrder(DomainRow.status),
    )
    """Declared, not exposed: the lifecycle column the write guards read."""
    created_at = QueryColumn(
        DomainRow.created_at,
        DateTimeConditions(DomainRow.created_at),
        ColumnOrder(DomainRow.created_at),
    )
    updated_at = QueryColumn(
        DomainRow.updated_at,
        DateTimeConditions(DomainRow.updated_at),
        ColumnOrder(DomainRow.updated_at),
    )
    integration_name = QueryColumn(
        DomainRow.integration_id,
        StringConditions(DomainRow.integration_id),
        ColumnOrder(DomainRow.integration_id),
    )
    allowed_docker_registries = QueryColumn(
        DomainRow.allowed_docker_registries,
        ArrayConditions(DomainRow.allowed_docker_registries, sa.String()),
        None,
    )
    """Impossible to order: an array."""
    total_resource_slots = QueryColumn(DomainRow.total_resource_slots, None, None)
    """Impossible: a JSON document of slot names to amounts."""
    allowed_vfolder_hosts = QueryColumn(DomainRow.allowed_vfolder_hosts, None, None)
    """Impossible: a JSON document of hosts to permission sets."""
    dotfiles = QueryColumn(DomainRow.dotfiles, None, None)
    """Sensitive: user-written files that can hold credentials verbatim. Binary as well."""

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return DomainData(
            id=self.id.read(row),
            name=self.name.read(row),
            description=self.description.read(row),
            is_active=self.is_active.read(row),
            is_default=self.is_default.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
            total_resource_slots=self.total_resource_slots.read(row),
            allowed_vfolder_hosts=self.allowed_vfolder_hosts.read(row),
            allowed_docker_registries=self.allowed_docker_registries.read(row),
            integration_name=self.integration_name.read(row),
            dotfiles=self.dotfiles.read(row),
        )


class DomainQuerySpec:
    own = _DomainOwnColumns()
