import uuid

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.searchable_fields import (
    RolePresetSearchableFields,
)
from ai.backend.manager.models.specs.soft_delete import RestoreUpdater, SoftDeleteUpdater


def _updaters(
    preset_id: RolePresetID,
) -> tuple[
    SoftDeleteUpdater[RolePresetRow, RolePresetData], RestoreUpdater[RolePresetRow, RolePresetData]
]:
    return (
        SoftDeleteUpdater(
            target_row=RolePresetRow,
            target_column=RolePresetRow.id,
            target_id=preset_id,
            converter=RolePresetSearchableFields.own,
        ),
        RestoreUpdater(
            target_row=RolePresetRow,
            target_column=RolePresetRow.id,
            target_id=preset_id,
            converter=RolePresetSearchableFields.own,
        ),
    )


class TestSoftDeleteUpdaters:
    def test_soft_delete_and_restore_write_deleted_at_alone(self) -> None:
        deleted, restored = _updaters(RolePresetID(uuid.uuid4()))

        deleted_values = deleted.build_values()
        assert set(deleted_values) == {"deleted_at"}
        assert isinstance(deleted_values["deleted_at"], sa.sql.functions.Function)
        assert restored.build_values() == {"deleted_at": None}

    def test_the_row_is_read_back_through_the_converter(self) -> None:
        preset_id = RolePresetID(uuid.uuid4())
        row = RolePresetRow(
            id=preset_id,
            name="member",
            role_name_template=None,
            scope_type=DomainEntityType(),
            auto_assign=False,
            deleted_at=None,
        )
        for updater in _updaters(preset_id):
            data = updater.to_data(row)
            assert data.id == preset_id
            assert data.deleted_at is None
