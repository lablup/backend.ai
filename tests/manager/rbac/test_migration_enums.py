from ai.backend.manager.data.permission.types import (
    EntityType as OriginalEntityType,
)
from ai.backend.manager.data.permission.types import (
    OperationType as OriginalOperationType,
)
from ai.backend.manager.data.permission.types import (
    RoleSource as OriginalRoleSource,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as OriginalScopeType,
)
from ai.backend.manager.models.rbac_models.migration.enums import (
    OPERATIONS_FOR_CUSTOM_ROLE,
    OPERATIONS_FOR_SYSTEM_ROLE,
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)


class TestRoleSource:
    def test_to_original(self):
        assert RoleSource.SYSTEM.to_original() == OriginalRoleSource("system")
        assert RoleSource.CUSTOM.to_original() == OriginalRoleSource("custom")


class TestOperationType:
    def test_to_original(self):
        for op_type in OperationType:
            original = op_type.to_original()
            assert original.value == op_type.value

    def test_grant_operations(self):
        grant_operations = [op for op in OperationType if op.value.startswith("grant:")]
        assert len(grant_operations) == 5
        assert OperationType.GRANT_ALL in grant_operations
        assert OperationType.GRANT_READ in grant_operations
        assert OperationType.GRANT_UPDATE in grant_operations
        assert OperationType.GRANT_SOFT_DELETE in grant_operations
        assert OperationType.GRANT_HARD_DELETE in grant_operations

    def test_operations_for_system_role(self):
        assert isinstance(OPERATIONS_FOR_SYSTEM_ROLE, tuple)
        assert len(OPERATIONS_FOR_SYSTEM_ROLE) == len(OperationType)
        for op in OperationType:
            assert op in OPERATIONS_FOR_SYSTEM_ROLE

    def test_operations_for_custom_role(self):
        assert isinstance(OPERATIONS_FOR_CUSTOM_ROLE, tuple)
        assert len(OPERATIONS_FOR_CUSTOM_ROLE) == 1
        assert OperationType.READ in OPERATIONS_FOR_CUSTOM_ROLE


class TestScopeType:
    def test_to_original(self):
        for scope_type in ScopeType:
            original = scope_type.to_original()
            assert original.value == scope_type.value


class TestEntityType:
    def test_to_original(self):
        for entity_type in EntityType:
            original = entity_type.to_original()
            assert original.value == entity_type.value


class TestEnumConsistency:
    def test_no_duplicate_values_within_enums(self):
        for enum_class in [RoleSource, OperationType, ScopeType, EntityType]:
            values = [member.value for member in enum_class]
            assert len(values) == len(set(values)), (
                f"Duplicate values found in {enum_class.__name__}"
            )

    def test_migration_enum_values_exist_in_original(self):
        """Test that all migration enum values can be converted to original enum values."""
        # RoleSource - all values should exist in original
        migration_values = {member.value for member in RoleSource}
        original_values = {member.value for member in OriginalRoleSource}
        missing_values = migration_values - original_values
        assert not missing_values, f"RoleSource values missing in original: {missing_values}"

        # OperationType - all values should exist in original
        migration_values = {member.value for member in OperationType}
        original_values = {member.value for member in OriginalOperationType}
        missing_values = migration_values - original_values
        assert not missing_values, f"OperationType values missing in original: {missing_values}"

        # ScopeType - all values should exist in original
        migration_values = {member.value for member in ScopeType}
        original_values = {member.value for member in OriginalScopeType}
        missing_values = migration_values - original_values
        assert not missing_values, f"ScopeType values missing in original: {missing_values}"

        # EntityType - all values should exist in original
        migration_values = {member.value for member in EntityType}
        original_values = {member.value for member in OriginalEntityType}
        missing_values = migration_values - original_values
        assert not missing_values, f"EntityType values missing in original: {missing_values}"

    def test_migration_enum_values_match_original_when_same_name(self):
        """Test that when migration enum and original enum have the same member name, they have the same value."""
        # RoleSource
        for migration_member in RoleSource:
            try:
                original_member = OriginalRoleSource[migration_member.name]
                assert migration_member.value == original_member.value, (
                    f"RoleSource.{migration_member.name} value mismatch: "
                    f"migration={migration_member.value}, original={original_member.value}"
                )
            except KeyError:
                pass

        # OperationType
        for migration_member in OperationType:
            try:
                original_member = OriginalOperationType[migration_member.name]
                assert migration_member.value == original_member.value, (
                    f"OperationType.{migration_member.name} value mismatch: "
                    f"migration={migration_member.value}, original={original_member.value}"
                )
            except KeyError:
                pass

        # ScopeType
        for migration_member in ScopeType:
            try:
                original_member = OriginalScopeType[migration_member.name]
                assert migration_member.value == original_member.value, (
                    f"ScopeType.{migration_member.name} value mismatch: "
                    f"migration={migration_member.value}, original={original_member.value}"
                )
            except KeyError:
                pass

        # EntityType
        for migration_member in EntityType:
            try:
                original_member = OriginalEntityType[migration_member.name]
                assert migration_member.value == original_member.value, (
                    f"EntityType.{migration_member.name} value mismatch: "
                    f"migration={migration_member.value}, original={original_member.value}"
                )
            except KeyError:
                pass
