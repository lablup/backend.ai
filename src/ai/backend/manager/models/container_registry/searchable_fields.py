"""What a container registry search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ContainerRegistryOwnFields(RowDataConverter[ContainerRegistryRow, ContainerRegistryData]):
    """The container registry's own columns."""

    id = SearchableField(
        ContainerRegistryRow.id,
        UUIDConditions(ContainerRegistryRow.id),
        ColumnOrder(ContainerRegistryRow.id),
    )
    url = SearchableField(
        ContainerRegistryRow.url,
        StringConditions(ContainerRegistryRow.url),
        ColumnOrder(ContainerRegistryRow.url),
    )
    registry_name = SearchableField(
        ContainerRegistryRow.registry_name,
        StringConditions(ContainerRegistryRow.registry_name),
        ColumnOrder(ContainerRegistryRow.registry_name),
    )
    type = SearchableField(
        ContainerRegistryRow.type,
        EnumConditions(ContainerRegistryRow.type, ContainerRegistryType),
        ColumnOrder(ContainerRegistryRow.type),
    )
    project = SearchableField(
        ContainerRegistryRow.project,
        StringConditions(ContainerRegistryRow.project),
        ColumnOrder(ContainerRegistryRow.project),
    )
    username = SearchableField(
        ContainerRegistryRow.username,
        StringConditions(ContainerRegistryRow.username),
        ColumnOrder(ContainerRegistryRow.username),
    )
    password = SearchableField(ContainerRegistryRow.password, None, None)
    """Sensitive: the credential the manager authenticates to the registry with."""
    ssl_verify = SearchableField(
        ContainerRegistryRow.ssl_verify,
        BoolConditions(ContainerRegistryRow.ssl_verify),
        ColumnOrder(ContainerRegistryRow.ssl_verify),
    )
    is_global = SearchableField(
        ContainerRegistryRow.is_global,
        BoolConditions(ContainerRegistryRow.is_global),
        ColumnOrder(ContainerRegistryRow.is_global),
    )
    """Whether the registry is registered in public."""
    extra = SearchableField(ContainerRegistryRow.extra, None, None)
    """Impossible: a JSON document of per-type settings."""

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return ContainerRegistryData(
            id=self.id.read(row),
            url=self.url.read(row),
            registry_name=self.registry_name.read(row),
            type=self.type.read(row),
            project=self.project.read(row),
            username=self.username.read(row),
            password=self.password.read(row),
            ssl_verify=self.ssl_verify.read(row),
            is_global=self.is_global.read(row),
            extra=self.extra.read(row),
        )


class ContainerRegistrySearchableFields:
    own = _ContainerRegistryOwnFields()
