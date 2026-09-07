import uuid

from ai.backend.common.data.entity.permission import PERMISSION_FIELD_TYPE, PermissionID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.lookups import RolePermissionOwnerLookup
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.models.rbac_models.permission.scopes import PermissionOperationScope


class TestRolePermissionCreator:
    def test_the_row_is_built_under_the_role_that_owns_it(self) -> None:
        role_id = RoleID(uuid.uuid4())
        scope = ProjectID(uuid.uuid4())
        creator = RolePermissionCreator(
            scope=scope, entity_type=EntityType("session"), permission=Permission.READ
        )

        row = creator.build_row(role_id)

        assert row.role_id == role_id
        assert row.scope_type == "project"
        assert row.scope_id == str(scope)
        assert row.entity_type == "session"
        assert row.permission == Permission.READ

    def test_a_duplicate_entry_is_mapped_to_a_domain_error(self) -> None:
        creator = RolePermissionCreator(
            scope=ProjectID(uuid.uuid4()),
            entity_type=EntityType("session"),
            permission=Permission.READ,
        )

        (check,) = creator.integrity_error_checks()

        assert check.error.error_title == "The role already holds the permission."

    def test_the_field_id_is_read_off_the_settled_row(self) -> None:
        permission_id = PermissionID(uuid.uuid4())
        creator = RolePermissionCreator(
            scope=ProjectID(uuid.uuid4()),
            entity_type=EntityType("session"),
            permission=Permission.READ,
        )

        field_id = creator.field_id(PermissionRow(id=permission_id))

        assert field_id == permission_id
        assert PermissionID.field_type() == PERMISSION_FIELD_TYPE


class TestRolePermissionReadSpecs:
    def test_the_owner_lookup_selects_the_row_id_beside_its_role(self) -> None:
        permission_id = PermissionID(uuid.uuid4())

        query = RolePermissionOwnerLookup().build_query([permission_id])

        assert [c.name for c in query.selected_columns] == ["id", "role_id"]
        assert query.whereclause is not None
        assert query.whereclause.compare(PermissionRow.id.in_([permission_id]))

    def test_the_owner_lookup_answers_a_role_id(self) -> None:
        value = uuid.uuid4()

        owner = RolePermissionOwnerLookup().to_entity_id(value)

        assert owner == RoleID(value)
        assert owner.entity_type() == "role"

    def test_the_operation_scope_bounds_the_read_to_one_role(self) -> None:
        role_id = RoleID(uuid.uuid4())

        condition = PermissionOperationScope(role_id=role_id).to_condition()()

        assert str(condition) == "permissions.role_id = :role_id_1"


class TestRolePermissionPurger:
    def test_the_purger_keys_on_the_permission_row_id(self) -> None:
        permission_id = PermissionID(uuid.uuid4())
        purger = RolePermissionPurger(permission_id=permission_id)

        assert purger.row_class() is PermissionRow
        assert purger.target_id_column() is PermissionRow.id
        assert purger.target_id_value() == permission_id
        assert purger.conflict_checks() == ()
