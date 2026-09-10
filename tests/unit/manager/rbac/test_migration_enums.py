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
    def test_owner_holds_every_operation(self) -> None:
        assert OperationType.owner_operations() == set(OperationType)

    def test_member_reads_only(self) -> None:
        assert OperationType.member_operations() == {OperationType.READ}


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
