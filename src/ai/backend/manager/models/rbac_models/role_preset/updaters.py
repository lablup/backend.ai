"""DataUpdater implementations for the role preset repository.

Soft delete and restore are the shared updaters in ``models/specs/soft_delete.py``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.role_preset import (
    RolePresetOwnerAssignNotAllowed,
    RolePresetUpdateConflict,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.searchable_fields import (
    RolePresetSearchableFields,
)
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RolePresetUpdater(GuardedDataUpdater[RolePresetRow, RolePresetData]):
    """Edits a preset's declaration. Carries no ``deleted_at`` field."""

    preset_id: RolePresetID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    role_name_template: TriState[str] = field(default_factory=TriState[str].nop)
    scope_type: OptionalState[EntityType] = field(default_factory=OptionalState[EntityType].nop)
    auto_assign: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    auto_assign_to_owner: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RolePresetRow.id

    @override
    def target_id_value(self) -> RolePresetID:
        return self.preset_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_role_presets_name",
                error=RolePresetUpdateConflict(
                    f"Role preset {self.preset_id} would share its name with another "
                    "preset in the same scope"
                ),
            ),
        )

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        """Only a project has an owner, so only a project preset takes the flag on."""
        if not self.auto_assign_to_owner.optional_value():
            return ()
        return (
            GuardCheck(
                condition=lambda: RolePresetRow.scope_type == ProjectEntityType(),
                error=RolePresetOwnerAssignNotAllowed(
                    f"Role preset {self.preset_id} is not in the project scope"
                ),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.role_name_template.update_dict(to_update, "role_name_template")
        self.scope_type.update_dict(to_update, "scope_type")
        self.auto_assign.update_dict(to_update, "auto_assign")
        self.auto_assign_to_owner.update_dict(to_update, "auto_assign_to_owner")
        return to_update

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return RolePresetSearchableFields.own.to_data(row)
