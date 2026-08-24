"""Update specs for container registries."""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ContainerRegistryUpdater(DataUpdater[ContainerRegistryRow, ContainerRegistryData]):
    """Edit a container registry's connection settings and allowed projects.

    ``allowed_groups`` names project associations, which are rows of their own; the
    repository writes them beside the update.
    """

    registry_id: ContainerRegistryID
    url: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    type: OptionalState[ContainerRegistryType] = field(
        default_factory=OptionalState[ContainerRegistryType].nop
    )
    registry_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    is_global: TriState[bool] = field(default_factory=TriState[bool].nop)
    project: TriState[str] = field(default_factory=TriState[str].nop)
    username: TriState[str] = field(default_factory=TriState[str].nop)
    password: TriState[str] = field(default_factory=TriState[str].nop)
    ssl_verify: TriState[bool] = field(default_factory=TriState[bool].nop)
    extra: TriState[dict[str, Any]] = field(default_factory=TriState[dict[str, Any]].nop)
    allowed_groups: TriState[AllowedGroupsModel] = field(
        default_factory=TriState[AllowedGroupsModel].nop
    )

    @property
    def has_allowed_groups_update(self) -> bool:
        """Whether allowed_groups carries projects to add or remove."""
        groups = self.allowed_groups.optional_value()
        return groups is not None and (bool(groups.add) or bool(groups.remove))

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
        self.is_global.update_dict(to_update, "is_global")
        self.project.update_dict(to_update, "project")
        self.username.update_dict(to_update, "username")
        self.password.update_dict(to_update, "password")
        self.ssl_verify.update_dict(to_update, "ssl_verify")
        self.extra.update_dict(to_update, "extra")
        return to_update

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()
