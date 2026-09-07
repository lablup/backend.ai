import uuid

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.purgers import RolePurger
from ai.backend.manager.models.rbac_models.role.queriers import RoleQuerier
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role.updaters import (
    RoleRestoreUpdater,
    RoleSoftDeleteUpdater,
    RoleUpdater,
)
from ai.backend.manager.types import OptionalState, TriState


class TestRoleCreator:
    def test_the_scope_owns_and_governs_the_new_role(self) -> None:
        scope = ProjectID(uuid.uuid4())
        creator = RoleCreator(name="reader", scope=scope)

        row = creator.build_row()

        assert creator.created_in(row) == (scope,)
        assert row.name == "reader"
        assert row.source == RoleSource.CUSTOM
        assert row.status == RoleStatus.ACTIVE

    def test_the_entity_id_is_read_off_the_settled_row(self) -> None:
        role_id = RoleID(uuid.uuid4())
        creator = RoleCreator(name="reader", scope=ProjectID(uuid.uuid4()))

        entity_id = creator.entity_id(RoleRow(id=role_id, name="reader"))

        assert entity_id == role_id
        assert entity_id.entity_type() == "role"


class TestRoleUpdater:
    def test_an_omitted_field_is_left_out_of_the_write(self) -> None:
        updater = RoleUpdater(
            role_id=RoleID(uuid.uuid4()), name=OptionalState[str].update("editor")
        )

        assert updater.build_values() == {"name": "editor"}

    def test_a_description_is_cleared_by_the_tri_state(self) -> None:
        updater = RoleUpdater(role_id=RoleID(uuid.uuid4()), description=TriState[str].nullify())

        assert updater.build_values() == {"description": None}

    def test_the_general_edit_path_carries_no_status_field(self) -> None:
        assert "status" not in {f for f in RoleUpdater.__dataclass_fields__}

    def test_edit_and_soft_delete_guard_on_a_custom_source(self) -> None:
        role_id = RoleID(uuid.uuid4())
        for updater in (RoleUpdater(role_id=role_id), RoleSoftDeleteUpdater(role_id=role_id)):
            (guard,) = updater.guard_conditions()
            assert str(guard()) == str(RoleRow.source == RoleSource.CUSTOM)

    def test_soft_delete_and_restore_write_constants(self) -> None:
        role_id = RoleID(uuid.uuid4())

        deleted = RoleSoftDeleteUpdater(role_id=role_id).build_values()
        restored = RoleRestoreUpdater(role_id=role_id).build_values()

        assert deleted["status"] == RoleStatus.DELETED
        assert isinstance(deleted["deleted_at"], sa.sql.functions.Function)
        assert restored == {"status": RoleStatus.ACTIVE, "deleted_at": None}


class TestRoleReadAndPurgeSpecs:
    def test_the_querier_keys_on_the_role_id_column(self) -> None:
        role_id = RoleID(uuid.uuid4())
        querier = RoleQuerier(role_id=role_id)

        assert querier.row_class() is RoleRow
        assert querier.entity_id_column() is RoleRow.id
        assert querier.entity_id_value() == role_id

    def test_the_purger_names_the_role_as_the_entity_it_tears_down(self) -> None:
        role_id = RoleID(uuid.uuid4())
        purger = RolePurger(role_id=role_id)

        assert purger.row_class() is RoleRow
        assert purger.target_id_column() is RoleRow.id
        assert purger.entity_id() == role_id

    def test_the_purger_declines_a_system_role(self) -> None:
        purger = RolePurger(role_id=RoleID(uuid.uuid4()))

        (check,) = purger.conflict_checks()
        assert isinstance(check.error, SystemRoleNotEditable)
