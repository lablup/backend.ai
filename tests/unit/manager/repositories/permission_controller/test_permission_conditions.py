"""Unit tests for the deprecated role assignment filters reaching permission rows.

The conditions inside the EXISTS come from the permission declaration, so the tests
check that they land on the same permission row.
"""

from __future__ import annotations

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.filter_specs import StringInMatchSpec
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.rbac_models.user_role.deprecated_search import (
    DeprecatedRoleAssignmentConditions,
)


def _entity_types_in(*entity_types: str) -> StringInMatchSpec:
    return StringInMatchSpec(values=list(entity_types), case_insensitive=False, negated=False)


class TestPermissionDeclaration:
    """The permission declaration's own filters."""

    def test_entity_type_in_produces_in_clause(self) -> None:
        condition = PermissionSearchableFields.own.entity_type.filter.in_(
            _entity_types_in(str(SessionEntityType()))
        )
        compiled = str(condition().compile(compile_kwargs={"literal_binds": True}))

        assert "permissions.entity_type IN" in compiled
        assert "session" in compiled.lower()

    def test_permission_in_produces_in_clause(self) -> None:
        condition = PermissionSearchableFields.own.permission.filter.in_([
            Permission.READ,
            Permission.CREATE,
        ])
        compiled = str(condition().compile(compile_kwargs={"literal_binds": True}))

        assert "permissions.permission IN" in compiled
        assert str(int(Permission.READ)) in compiled
        assert str(int(Permission.CREATE)) in compiled


class TestExistsPermissionCombined:
    """Tests for DeprecatedRoleAssignmentConditions.exists_permission_combined."""

    def test_exists_permission_combined_structure(self) -> None:
        """exists_permission_combined should produce EXISTS subquery with role_id join."""
        permission_conditions = [
            PermissionSearchableFields.own.permission.filter.in_([Permission.READ]),
            PermissionSearchableFields.own.entity_type.filter.in_(
                _entity_types_in(str(SessionEntityType()))
            ),
        ]

        condition = DeprecatedRoleAssignmentConditions.exists_permission_combined(
            permission_conditions
        )
        compiled = str(condition().compile(compile_kwargs={"literal_binds": True}))

        assert "EXISTS" in compiled.upper()
        assert "SELECT 1" in compiled.upper()
        assert "permissions.role_id = user_roles.role_id" in compiled
        assert "permissions.permission IN" in compiled
        assert "permissions.entity_type IN" in compiled
        assert "session" in compiled.lower()

    def test_exists_permission_combined_with_multiple_operations(self) -> None:
        """exists_permission_combined should combine multiple operation filters."""
        permission_conditions = [
            PermissionSearchableFields.own.entity_type.filter.in_(
                _entity_types_in(str(SessionEntityType()), str(VFolderEntityType()))
            ),
            PermissionSearchableFields.own.permission.filter.in_([
                Permission.READ,
                Permission.UPDATE,
            ]),
        ]

        condition = DeprecatedRoleAssignmentConditions.exists_permission_combined(
            permission_conditions
        )
        compiled = str(condition().compile(compile_kwargs={"literal_binds": True}))

        assert "permissions.entity_type IN" in compiled
        assert "permissions.permission IN" in compiled
        assert "session" in compiled.lower()
        assert "vfolder" in compiled.lower()
        assert str(int(Permission.READ)) in compiled
        assert str(int(Permission.UPDATE)) in compiled

    def test_exists_permission_combined_empty_conditions(self) -> None:
        """An empty list leaves the EXISTS carrying the join alone."""
        condition = DeprecatedRoleAssignmentConditions.exists_permission_combined([])
        compiled = str(condition().compile(compile_kwargs={"literal_binds": True}))

        assert "EXISTS" in compiled.upper()
        assert "permissions.role_id = user_roles.role_id" in compiled
        assert "scope_id" not in compiled
        assert "entity_type" not in compiled
        assert "operation" not in compiled
