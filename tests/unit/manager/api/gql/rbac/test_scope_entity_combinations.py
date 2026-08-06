"""Tests for the rbac_scope_entity_combinations resolver."""

from __future__ import annotations

from unittest.mock import MagicMock

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.api.gql.rbac.resolver import permission as permission_resolver


class TestRbacScopeEntityCombinationsResolver:
    async def test_idle_checker_is_available_under_supported_scopes(self) -> None:
        resolver_fn = permission_resolver.rbac_scope_entity_combinations.base_resolver
        result = await resolver_fn(MagicMock())
        assert result is not None

        combinations = {
            combination.scope_type.value: {
                entity_type.value for entity_type in combination.valid_entity_types
            }
            for combination in result
        }
        for scope in (
            RBACElementType.DOMAIN,
            RBACElementType.PROJECT,
            RBACElementType.RESOURCE_GROUP,
        ):
            assert RBACElementType.IDLE_CHECKER.value in combinations[scope.value]
