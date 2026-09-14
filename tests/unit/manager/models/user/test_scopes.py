from __future__ import annotations

import uuid

from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.user.scopes import RoleUserOperationScope


class TestRoleUserOperationScope:
    def test_filters_users_through_role_assignments(self) -> None:
        scope = RoleUserOperationScope(role_id=RoleID(uuid.uuid4()))

        condition = scope.to_condition()()

        assert str(condition) == (
            "users.uuid IN (SELECT user_roles.user_id \n"
            "FROM user_roles \n"
            "WHERE user_roles.role_id = :role_id_1)"
        )

    def test_requires_the_role_to_exist(self) -> None:
        role_id = RoleID(uuid.uuid4())
        scope = RoleUserOperationScope(role_id=role_id)

        (check,) = scope.existence_checks

        assert check.column is RoleRow.id
        assert check.value == role_id
        assert isinstance(check.error, RoleNotFound)
