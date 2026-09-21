"""Update specs for container registries."""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.container_registry.searchable_fields import (
    ContainerRegistrySearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ContainerRegistryUpdater(DataUpdater[ContainerRegistryRow, ContainerRegistryData]):
    """Edit a container registry's connection settings.

    The projects allowed on it are rows of their own, written by the relation
    operations; a value whose change drags other writes along is not an updater field.
    `is_global` is one: :class:`ContainerRegistryGlobalUpdater` writes it.
    """

    registry_id: ContainerRegistryID
    url: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    type: OptionalState[ContainerRegistryType] = field(
        default_factory=OptionalState[ContainerRegistryType].nop
    )
    registry_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    project: TriState[str] = field(default_factory=TriState[str].nop)
    username: TriState[str] = field(default_factory=TriState[str].nop)
    password: TriState[str] = field(default_factory=TriState[str].nop)
    ssl_verify: TriState[bool] = field(default_factory=TriState[bool].nop)
    extra: TriState[dict[str, Any]] = field(default_factory=TriState[dict[str, Any]].nop)

    @property
    @override
    def row_class(self) -> builtins.type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ContainerRegistryRow.id

    @override
    def target_id_value(self) -> ContainerRegistryID:
        return self.registry_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.url.update_dict(to_update, "url")
        self.type.update_dict(to_update, "type")
        self.registry_name.update_dict(to_update, "registry_name")
        self.project.update_dict(to_update, "project")
        self.username.update_dict(to_update, "username")
        self.password.update_dict(to_update, "password")
        self.ssl_verify.update_dict(to_update, "ssl_verify")
        self.extra.update_dict(to_update, "extra")
        return to_update

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return ContainerRegistrySearchableFields.own.to_data(row)


@dataclass
class ContainerRegistryGlobalUpdater(DataUpdater[ContainerRegistryRow, ContainerRegistryData]):
    """Write `is_global`, which the repository follows with the registry's membership
    of the `public` scope."""

    registry_id: ContainerRegistryID
    is_global: bool

    @property
    @override
    def row_class(self) -> builtins.type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ContainerRegistryRow.id

    @override
    def target_id_value(self) -> ContainerRegistryID:
        return self.registry_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_global": self.is_global}

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return ContainerRegistrySearchableFields.own.to_data(row)
