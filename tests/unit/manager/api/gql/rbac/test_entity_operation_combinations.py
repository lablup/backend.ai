"""Tests for the rbac_entity_operation_combinations resolver."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action import RBAC_ACTION_REGISTRY
from ai.backend.manager.actions.action.rbac import (
    RBACActionName,
    build_operation_description,
)
from ai.backend.manager.api.gql.rbac.resolver import permission as permission_resolver


class TestBuildOperationDescription:
    @pytest.mark.parametrize(
        ("action_name", "element_type", "expected"),
        [
            (RBACActionName.CREATE, RBACElementType.SESSION, "Create a new session"),
            (RBACActionName.GET, RBACElementType.SESSION, "Get session details"),
            (RBACActionName.SEARCH, RBACElementType.SESSION, "Search session list"),
            (RBACActionName.UPDATE, RBACElementType.SESSION, "Update session"),
            (RBACActionName.SOFT_DELETE, RBACElementType.SESSION, "Soft-delete session"),
            (RBACActionName.HARD_DELETE, RBACElementType.SESSION, "Hard-delete session"),
            (
                RBACActionName.GRANT_ALL,
                RBACElementType.SESSION,
                "Grant all permissions for session",
            ),
            (
                RBACActionName.GRANT_READ,
                RBACElementType.SESSION,
                "Grant read permission for session",
            ),
            (
                RBACActionName.GRANT_UPDATE,
                RBACElementType.SESSION,
                "Grant update permission for session",
            ),
            (
                RBACActionName.GRANT_SOFT_DELETE,
                RBACElementType.SESSION,
                "Grant soft-delete permission for session",
            ),
            (
                RBACActionName.GRANT_HARD_DELETE,
                RBACElementType.SESSION,
                "Grant hard-delete permission for session",
            ),
        ],
    )
    def test_description_for_each_action_name(
        self,
        action_name: RBACActionName,
        element_type: RBACElementType,
        expected: str,
    ) -> None:
        result = build_operation_description(action_name, element_type)
        assert result == expected

    def test_underscored_element_type_uses_spaces(self) -> None:
        result = build_operation_description(
            RBACActionName.CREATE, RBACElementType.MODEL_DEPLOYMENT
        )
        assert result == "Create a new model deployment"


class TestRbacEntityOperationCombinationsResolver:
    async def test_returns_expected_structure(self) -> None:
        info = MagicMock()
        resolver_fn = permission_resolver.rbac_entity_operation_combinations.base_resolver
        result = await resolver_fn(info)
        assert isinstance(result, list)
        assert len(result) > 0
        for combo in result:
            assert hasattr(combo, "entity_type")
            assert hasattr(combo, "operations")
            assert isinstance(combo.operations, list)
            for op in combo.operations:
                assert hasattr(op, "operation")
                assert hasattr(op, "description")
                assert hasattr(op, "required_permission")

    async def test_operations_are_sorted(self) -> None:
        info = MagicMock()
        resolver_fn = permission_resolver.rbac_entity_operation_combinations.base_resolver
        result = await resolver_fn(info)
        for combo in result:
            op_names = [op.operation for op in combo.operations]
            assert op_names == sorted(op_names)

    async def test_entity_types_are_sorted(self) -> None:
        info = MagicMock()
        resolver_fn = permission_resolver.rbac_entity_operation_combinations.base_resolver
        result = await resolver_fn(info)
        entity_values = [combo.entity_type.value for combo in result]
        assert entity_values == sorted(entity_values)

    async def test_registry_entries_are_present(self) -> None:
        info = MagicMock()
        resolver_fn = permission_resolver.rbac_entity_operation_combinations.base_resolver
        result = await resolver_fn(info)
        # Collect all entity_type -> operation pairs from the result
        result_pairs: set[tuple[str, str]] = set()
        for combo in result:
            for op in combo.operations:
                result_pairs.add((combo.entity_type.value, op.operation))
        # Every registry entry must appear in the result
        for action_cls in RBAC_ACTION_REGISTRY:
            perm = action_cls.required_permission()
            name = action_cls.action_name()
            assert (perm.element_type.value, name.value) in result_pairs
