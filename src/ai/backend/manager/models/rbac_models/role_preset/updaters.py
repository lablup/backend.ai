"""DataUpdater implementations for the role preset repository.

The ``deleted`` column is split off from the general updater, so the ordinary edit
path has no field to make the transition with (`models/specs/AGENTS.md`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RolePresetUpdater(DataUpdater[RolePresetRow, RolePresetData]):
    """Edits a preset's declaration. Carries no ``deleted`` field."""

    preset_id: RolePresetID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    role_name_template: TriState[str] = field(default_factory=TriState[str].nop)
    scope_type: OptionalState[ScopeType] = field(default_factory=OptionalState[ScopeType].nop)
    auto_assign: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> RolePresetID:
        return self.preset_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.role_name_template.update_dict(to_update, "role_name_template")
        self.scope_type.update_dict(to_update, "scope_type")
        self.auto_assign.update_dict(to_update, "auto_assign")
        return to_update

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class RolePresetSoftDeleteUpdater(DataUpdater[RolePresetRow, RolePresetData]):
    """Marks a preset deleted; the value is constant so it cannot be passed wrong."""

    preset_id: RolePresetID

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> RolePresetID:
        return self.preset_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted": True}

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class RolePresetRestoreUpdater(DataUpdater[RolePresetRow, RolePresetData]):
    """Undoes the soft delete; the mirror of :class:`RolePresetSoftDeleteUpdater`."""

    preset_id: RolePresetID

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> RolePresetID:
        return self.preset_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted": False}

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()
