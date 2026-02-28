"""Tests for ScopeEntityCombinationGQL type and rbacScopeEntityCombinations query."""

from __future__ import annotations

from ai.backend.manager.api.gql.rbac.resolver.permission import rbac_scope_entity_combinations
from ai.backend.manager.api.gql.rbac.types.permission import (
    RBACElementTypeGQL,
    ScopeEntityCombinationGQL,
)


class TestScopeEntityCombinationGQL:
    def test_type_has_required_fields(self) -> None:
        """Test that ScopeEntityCombinationGQL can be instantiated with correct fields."""
        combo = ScopeEntityCombinationGQL(
            scope_type=RBACElementTypeGQL.DOMAIN,
            valid_entity_types=[RBACElementTypeGQL.PROJECT, RBACElementTypeGQL.USER],
        )
        assert combo.scope_type == RBACElementTypeGQL.DOMAIN
        assert combo.valid_entity_types == [
            RBACElementTypeGQL.PROJECT,
            RBACElementTypeGQL.USER,
        ]

    def test_type_with_empty_valid_entity_types(self) -> None:
        """Test that ScopeEntityCombinationGQL works with empty valid entity types list."""
        combo = ScopeEntityCombinationGQL(
            scope_type=RBACElementTypeGQL.USER,
            valid_entity_types=[],
        )
        assert combo.scope_type == RBACElementTypeGQL.USER
        assert combo.valid_entity_types == []


class TestRbacScopeEntityCombinationsQuery:
    def test_query_field_exists_in_schema(self) -> None:
        """Test that rbacScopeEntityCombinations is registered as a strawberry field."""
        assert rbac_scope_entity_combinations.base_resolver is not None
