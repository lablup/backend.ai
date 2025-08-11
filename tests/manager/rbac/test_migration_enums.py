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

    def test_owner_operations_match_original(self):
        """Test that owner_operations() returns the same values as original."""
        migration_ops = OperationType.owner_operations()
        original_ops = OriginalOperationType.owner_operations()

        # Convert migration ops to values for comparison
        migration_values = {op.value for op in migration_ops}
        original_values = {op.value for op in original_ops}

        assert migration_values == original_values, (
            f"owner_operations mismatch: migration={migration_values}, original={original_values}"
        )

    def test_admin_operations_match_original(self):
        """Test that admin_operations() returns the same values as original."""
        migration_ops = OperationType.admin_operations()
        original_ops = OriginalOperationType.admin_operations()

        # Convert migration ops to values for comparison
        migration_values = {op.value for op in migration_ops}
        original_values = {op.value for op in original_ops}

        assert migration_values == original_values, (
            f"admin_operations mismatch: migration={migration_values}, original={original_values}"
        )

    def test_member_operations_match_original(self):
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
    def test_to_original(self):
        for scope_type in ScopeType:
            original = scope_type.to_original()
            assert original.value == scope_type.value


class TestEntityType:
    def test_to_original(self):
        for entity_type in EntityType:
            original = entity_type.to_original()
            assert original.value == entity_type.value

    def test_scope_types_match_original(self):
        """Test that _scope_types() returns the same values as original."""
        migration_types = EntityType._scope_types()
        original_types = OriginalEntityType._scope_types()

        # Convert to values for comparison
        migration_values = {t.value for t in migration_types}
        original_values = {t.value for t in original_types}

        assert migration_values == original_values, (
            f"_scope_types mismatch: migration={migration_values}, original={original_values}"
        )

    def test_resource_types_match_original(self):
        """Test that _resource_types() returns the same values as original."""
        migration_types = EntityType._resource_types()
        original_types = OriginalEntityType._resource_types()

        # Convert to values for comparison
        migration_values = {t.value for t in migration_types}
        original_values = {t.value for t in original_types}

        assert migration_values == original_values, (
            f"_resource_types mismatch: migration={migration_values}, original={original_values}"
        )

    def test_owner_accessible_entity_types_in_user_match_original(self):
        """Test that owner_accessible_entity_types_in_user() returns the same values as original."""
        migration_types = EntityType.owner_accessible_entity_types_in_user()
        original_types = OriginalEntityType.owner_accessible_entity_types_in_user()

        # Convert to values for comparison
        migration_values = {t.value for t in migration_types}
        original_values = {t.value for t in original_types}

        assert migration_values == original_values, (
            f"owner_accessible_entity_types_in_user mismatch: migration={migration_values}, original={original_values}"
        )

    def test_admin_accessible_entity_types_in_project_match_original(self):
        """Test that admin_accessible_entity_types_in_project() returns the same values as original."""
        migration_types = EntityType.admin_accessible_entity_types_in_project()
        original_types = OriginalEntityType.admin_accessible_entity_types_in_project()

        # Convert to values for comparison
        migration_values = {t.value for t in migration_types}
        original_values = {t.value for t in original_types}

        assert migration_values == original_values, (
            f"admin_accessible_entity_types_in_project mismatch: migration={migration_values}, original={original_values}"
        )

    def test_member_accessible_entity_types_in_project_match_original(self):
        """Test that member_accessible_entity_types_in_project() returns the same values as original."""
        migration_types = EntityType.member_accessible_entity_types_in_project()
        original_types = OriginalEntityType.member_accessible_entity_types_in_project()

        # Convert to values for comparison
        migration_values = {t.value for t in migration_types}
        original_values = {t.value for t in original_types}

        assert migration_values == original_values, (
            f"member_accessible_entity_types_in_project mismatch: migration={migration_values}, original={original_values}"
        )


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
