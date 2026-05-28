from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base.updater import BatchUpdaterSpec, UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class RolePresetUpdaterSpec(UpdaterSpec[RolePresetRow]):
    """Single-row updater for role preset rows.

    The ``deleted`` column is intentionally not exposed — soft-delete state
    is managed only by the dedicated delete/restore operations via
    :class:`RolePresetDeletedFlagBatchUpdaterSpec`.
    """

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    scope_type: OptionalState[ScopeType] = field(default_factory=OptionalState[ScopeType].nop)
    auto_assign: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.scope_type.update_dict(to_update, "scope_type")
        self.auto_assign.update_dict(to_update, "auto_assign")
        return to_update


@dataclass
class RolePresetDeletedFlagBatchUpdaterSpec(BatchUpdaterSpec[RolePresetRow]):
    """Bulk update of the ``deleted`` flag — used by delete/restore."""

    deleted: bool

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted": self.deleted}
