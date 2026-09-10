"""Tests for the RBAC catalog resolvers and the operation descriptions they carry."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.dto.manager.v2.rbac.response import (
    EntityOperationCombinationInfo,
    OperationInfo,
)
from ai.backend.common.dto.manager.v2.rbac.types import OperationTypeDTO
from ai.backend.manager.actions.action.rbac import build_operation_description
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.api.gql.rbac.resolver import permission as permission_resolver


class TestBuildOperationDescription:
    @pytest.mark.parametrize(
        ("operation", "entity_type", "expected"),
        [
            (ActionOperationType.CREATE, SessionEntityType(), "Create a new session"),
            (ActionOperationType.GET, SessionEntityType(), "Get session details"),
            (ActionOperationType.SEARCH, SessionEntityType(), "Search session list"),
            (ActionOperationType.LOOKUP, SessionEntityType(), "Look up a session by name"),
            (ActionOperationType.UPDATE, SessionEntityType(), "Update session"),
            (ActionOperationType.UPSERT, SessionEntityType(), "Create or update session"),
            (ActionOperationType.DELETE, SessionEntityType(), "Soft-delete session"),
            (
                ActionOperationType.RESTORE,
                SessionEntityType(),
                "Restore a soft-deleted session",
            ),
            (ActionOperationType.PURGE, SessionEntityType(), "Hard-delete session"),
        ],
    )
    def test_description_for_each_operation(
        self,
        operation: ActionOperationType,
        entity_type: EntityType,
        expected: str,
    ) -> None:
        assert build_operation_description(operation, entity_type) == expected

    def test_every_operation_has_a_description(self) -> None:
        for operation in ActionOperationType:
            assert build_operation_description(operation, SessionEntityType())

    def test_underscored_entity_type_uses_spaces(self) -> None:
        result = build_operation_description(ActionOperationType.CREATE, ResourceGroupEntityType())
        assert result == "Create a new resource group"


def _info_answering(combinations: list[EntityOperationCombinationInfo]) -> MagicMock:
    info = MagicMock()
    info.context.adapters.rbac.get_entity_operation_combinations = AsyncMock(
        return_value=combinations
    )
    return info


class TestRbacEntityOperationCombinationsResolver:
    async def test_carries_the_adapter_answer_through(self) -> None:
        info = _info_answering([
            EntityOperationCombinationInfo(
                entity_type=SessionEntityType(),
                operations=[
                    OperationInfo(
                        operation="create_session",
                        description="Create a new session",
                        required_permission=OperationTypeDTO.CREATE,
                    )
                ],
            )
        ])
        resolver_fn = permission_resolver.rbac_entity_operation_combinations.base_resolver

        result = await resolver_fn(info)

        assert result is not None
        assert [combo.entity_type for combo in result] == [SessionEntityType()]
        assert [op.operation for op in result[0].operations] == ["create_session"]

    async def test_answers_an_empty_catalog(self) -> None:
        resolver_fn = permission_resolver.rbac_entity_operation_combinations.base_resolver

        assert await resolver_fn(_info_answering([])) == []
