from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType, ScopeType
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class PermissionUpdaterSpec(UpdaterSpec[PermissionRow]):
    """UpdaterSpec for permission updates."""

    scope_type: OptionalState[ScopeType] = field(default_factory=OptionalState.nop)
    scope_id: OptionalState[str] = field(default_factory=OptionalState.nop)
    entity_type: OptionalState[EntityType] = field(default_factory=OptionalState.nop)
    permission: OptionalState[Permission] = field(default_factory=OptionalState.nop)

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
        if (permission := self.permission.optional_value()) is not None:
            to_update["permission"] = single_bit(permission)
        return to_update
