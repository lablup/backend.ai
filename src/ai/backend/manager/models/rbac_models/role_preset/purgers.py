from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RolePresetPurger(EntityPurger[RolePresetRow, RolePresetData]):
    """Purger for a role preset. Its permission rows follow by FK cascade."""

    preset_id: RolePresetID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RolePresetRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()
