from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RoleUpdaterSpec(UpdaterSpec[RoleRow]):
    """UpdaterSpec for role updates."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    source: OptionalState[RoleSource] = field(default_factory=OptionalState.nop)
    status: OptionalState[RoleStatus] = field(default_factory=OptionalState.nop)
    description: TriState[str] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.source.update_dict(to_update, "source")
        self.status.update_dict(to_update, "status")
        self.description.update_dict(to_update, "description")
        return to_update


@dataclass
class PermissionUpdaterSpec(UpdaterSpec[PermissionRow]):
    """UpdaterSpec for permission updates."""

    scope_type: OptionalState[ScopeType] = field(default_factory=OptionalState.nop)
    scope_id: OptionalState[str] = field(default_factory=OptionalState.nop)
    entity_type: OptionalState[EntityType] = field(default_factory=OptionalState.nop)
    operation: OptionalState[OperationType] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.scope_type.update_dict(to_update, "scope_type")
        self.scope_id.update_dict(to_update, "scope_id")
        self.entity_type.update_dict(to_update, "entity_type")
        self.operation.update_dict(to_update, "operation")
        return to_update
