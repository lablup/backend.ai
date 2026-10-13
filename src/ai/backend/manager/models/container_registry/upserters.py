"""Upsert specs for the container_registries table."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.container_registry.searchable_fields import (
    ContainerRegistrySearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("ContainerRegistryUpserter",)


@dataclass
class ContainerRegistryUpserter(EntityUpserter[ContainerRegistryRow, ContainerRegistryData]):
    """Write a container registry under its stated id. Conflict key: id.
    Images name a registry by ``registry_name`` and ``project``, and ``is_global`` picks
    the scopes it is created in; an overwrite leaves the three as they are."""

    id: ContainerRegistryID
    url: str
    registry_type: ContainerRegistryType
    registry_name: str
    is_global: bool
    project: str | None
    username: str | None
    password: str | None
    ssl_verify: bool
    extra: dict[str, Any] | None

    @override
    def entity_id(self, row: ContainerRegistryRow) -> ContainerRegistryID:
        return ContainerRegistryID(row.id)

    @override
    def created_in(self, row: ContainerRegistryRow) -> Collection[EntityIdentifier]:
        if not row.is_global:
            return (global_entity_id(GlobalEntityName.GLOBAL),)
        return (
            global_entity_id(GlobalEntityName.GLOBAL),
            global_entity_id(GlobalEntityName.PUBLIC),
        )

    @override
    def row_class(self) -> type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "registry_name": self.registry_name,
            "project": self.project,
            "is_global": self.is_global,
            **self.build_update_values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "type": self.registry_type,
            "username": self.username,
            "password": self.password,
            "ssl_verify": self.ssl_verify,
            "extra": self.extra,
        }

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return ContainerRegistrySearchableFields.own.to_data(row)
