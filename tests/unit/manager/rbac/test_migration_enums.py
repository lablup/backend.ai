from ai.backend.manager.data.permission.types import (
    OperationType as OriginalOperationType,
)
from ai.backend.manager.data.permission.types import (
    RoleSource as OriginalRoleSource,
)
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)


class TestRoleSource:
    def test_to_original(self) -> None:
        assert RoleSource.SYSTEM.to_original() == OriginalRoleSource("system")
        assert RoleSource.CUSTOM.to_original() == OriginalRoleSource("custom")


class TestOperationType:
    def test_to_original(self) -> None:
        for op_type in OperationType:
            original = op_type.to_original()
            assert original.value == op_type.value

    def test_grant_operations(self) -> None:
        grant_operations = [op for op in OperationType if op.value.startswith("grant:")]
        assert len(grant_operations) == 5
        assert OperationType.GRANT_ALL in grant_operations
        assert OperationType.GRANT_READ in grant_operations
        assert OperationType.GRANT_UPDATE in grant_operations
        assert OperationType.GRANT_SOFT_DELETE in grant_operations
        assert OperationType.GRANT_HARD_DELETE in grant_operations

    def test_owner_operations_match_original(self) -> None:
        """Test that owner_operations() returns the same values as original."""
        migration_ops = OperationType.owner_operations()
        original_ops = OriginalOperationType.owner_operations()

        # Convert migration ops to values for comparison
        migration_values = {op.value for op in migration_ops}
        original_values = {op.value for op in original_ops}

        assert migration_values == original_values, (
            f"owner_operations mismatch: migration={migration_values}, original={original_values}"
        )

    def test_admin_operations_match_original(self) -> None:
        """Test that admin_operations() returns the same values as original."""
        migration_ops = OperationType.admin_operations()
        original_ops = OriginalOperationType.admin_operations()

        # Convert migration ops to values for comparison
        migration_values = {op.value for op in migration_ops}
        original_values = {op.value for op in original_ops}

        assert migration_values == original_values, (
            f"admin_operations mismatch: migration={migration_values}, original={original_values}"
        )

    def test_member_operations_match_original(self) -> None:
        """Test that member_operations() returns the same values as original."""
        migration_ops = OperationType.member_operations()
        original_ops = OriginalOperationType.member_operations()

        # Convert migration ops to values for comparison
        migration_values = {op.value for op in migration_ops}
        original_values = {op.value for op in original_ops}

        assert migration_values == original_values, (
            f"member_operations mismatch: migration={migration_values}, original={original_values}"
        )


class TestScopeType:
    def test_to_original(self) -> None:
        for scope_type in ScopeType:
            assert scope_type.to_original() == scope_type.value


class TestEntityType:
    def test_to_original(self) -> None:
        for entity_type in EntityType:
            assert entity_type.to_original() == entity_type.value


class TestEnumConsistency:
    def test_no_duplicate_values_within_enums(self) -> None:
        for enum_class in [RoleSource, OperationType, ScopeType, EntityType]:
            values = [member.value for member in enum_class]
            assert len(values) == len(set(values)), (
                f"Duplicate values found in {enum_class.__name__}"
            )
