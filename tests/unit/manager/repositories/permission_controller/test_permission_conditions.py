"""
Unit tests for PermissionConditions and exists_permission_combined.
Tests verify that condition factories produce correct SQLAlchemy expressions.
"""

from __future__ import annotations

from ai.backend.manager.data.permission.types import EntityType, OperationType, ScopeType
from ai.backend.manager.models.rbac_models.conditions import (
    AssignedUserConditions,
    PermissionConditions,
)


class TestPermissionConditions:
    """Tests for PermissionConditions query condition factories."""

    def test_by_scope_id_produces_equality_clause(self) -> None:
        """by_scope_id should generate scope_id == 'global' clause."""
        condition = PermissionConditions.by_scope_id("global")
        clause = condition()

        # Compile to SQL and check for expected pattern
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "permissions.scope_id = 'global'" in compiled

    def test_by_scope_types_produces_in_clause(self) -> None:
        """by_scope_types should generate scope_type IN (...) clause."""
        condition = PermissionConditions.by_scope_types([ScopeType.DOMAIN, ScopeType.PROJECT])
        clause = condition()

        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "permissions.scope_type IN" in compiled
        assert "domain" in compiled.lower()
        assert "project" in compiled.lower()

    def test_by_entity_types_produces_in_clause(self) -> None:
        """by_entity_types should generate entity_type IN (...) clause."""
        condition = PermissionConditions.by_entity_types([EntityType.SESSION])
        clause = condition()

        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "permissions.entity_type IN" in compiled
        assert "session" in compiled.lower()

    def test_by_operations_produces_in_clause(self) -> None:
        """by_operations should generate operation IN (...) clause."""
        condition = PermissionConditions.by_operations([OperationType.READ, OperationType.CREATE])
        clause = condition()

        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "permissions.operation IN" in compiled
        assert "read" in compiled.lower()
        assert "create" in compiled.lower()


class TestExistsPermissionCombined:
    """Tests for AssignedUserConditions.exists_permission_combined."""

    def test_exists_permission_combined_structure(self) -> None:
        """exists_permission_combined should produce EXISTS subquery with role_id join."""
        # Create sample permission conditions
        permission_conditions = [
            PermissionConditions.by_scope_id("global"),
            PermissionConditions.by_entity_types([EntityType.SESSION]),
        ]

        condition = AssignedUserConditions.exists_permission_combined(permission_conditions)
        clause = condition()

        # Compile to SQL
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))

        # Verify EXISTS structure
        assert "EXISTS" in compiled.upper()
        assert "SELECT 1" in compiled.upper()

        # Verify role_id join
        assert "permissions.role_id = user_roles.role_id" in compiled

        # Verify both conditions are present
        assert "permissions.scope_id = 'global'" in compiled
        assert "permissions.entity_type IN" in compiled
        assert "session" in compiled.lower()

    def test_exists_permission_combined_with_multiple_operations(self) -> None:
        """exists_permission_combined should combine multiple operation filters."""
        permission_conditions = [
            PermissionConditions.by_scope_types([ScopeType.DOMAIN, ScopeType.PROJECT]),
            PermissionConditions.by_operations([OperationType.READ, OperationType.UPDATE]),
        ]

        condition = AssignedUserConditions.exists_permission_combined(permission_conditions)
        clause = condition()

        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))

        # Verify both scope_types and operations are in the WHERE clause
        assert "permissions.scope_type IN" in compiled
        assert "permissions.operation IN" in compiled
        assert "domain" in compiled.lower()
        assert "project" in compiled.lower()
        assert "read" in compiled.lower()
        assert "update" in compiled.lower()

    def test_exists_permission_combined_empty_conditions(self) -> None:
        """exists_permission_combined with empty list should produce basic EXISTS with join only."""
        condition = AssignedUserConditions.exists_permission_combined([])
        clause = condition()

        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))

        # Should have EXISTS and join, but no additional WHERE clauses
        assert "EXISTS" in compiled.upper()
        assert "permissions.role_id = user_roles.role_id" in compiled
        # Should not have extra conditions
        assert "scope_id" not in compiled
        assert "entity_type" not in compiled
        assert "operation" not in compiled
