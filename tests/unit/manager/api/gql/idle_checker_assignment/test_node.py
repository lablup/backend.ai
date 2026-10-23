"""Tests for reading an idle checker assignment through ``node(id:)`` by its ends."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import strawberry
from strawberry.federation import Schema
from strawberry.tools import create_type

from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import IdleCheckerScopeRefDTO
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    IdleCheckerAssignmentNode,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.manager.api.gql.base import to_relation_global_id
from ai.backend.manager.api.gql.idle_checker_assignment.types import IdleCheckerAssignmentGQL
from ai.backend.manager.api.gql.node_field import node
from ai.backend.manager.errors.idle_checker import IdleCheckerAssignmentNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission

_NODE_QUERY = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    id
    ... on IdleCheckerAssignment { scopeType scopeId idleCheckerId }
  }
}
"""


@pytest.fixture
def schema() -> Schema:
    return Schema(
        query=create_type("Query", [node]),
        types=[IdleCheckerAssignmentGQL],
        federation_version="2.7",
    )


@pytest.fixture
def scope_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def idle_checker_id() -> IdleCheckerID:
    return IdleCheckerID(uuid.uuid4())


def _assignment_node(
    scope_id: uuid.UUID, idle_checker_id: IdleCheckerID
) -> IdleCheckerAssignmentNode:
    now = datetime(2026, 10, 20, tzinfo=UTC)
    return IdleCheckerAssignmentNode(
        id=IdleCheckerAssignmentID(uuid.uuid4()),
        scope_type=IdleCheckerScopeTypeDTO.PROJECT,
        scope_id=scope_id,
        idle_checker_id=idle_checker_id,
        enabled=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def relation_id(scope_id: uuid.UUID, idle_checker_id: IdleCheckerID) -> str:
    return to_relation_global_id(IdleCheckerAssignmentGQL, "project", scope_id, idle_checker_id)


@pytest.fixture
def context() -> MagicMock:
    ctx = MagicMock()
    ctx.adapters.idle_checker_assignment.get = AsyncMock()
    return ctx


async def _execute(
    schema: Schema, query: str, variables: dict[str, Any], context: MagicMock
) -> strawberry.types.ExecutionResult:
    return await schema.execute(query, variable_values=variables, context_value=context)


class TestIdleCheckerAssignmentNode:
    async def test_reads_the_assignment_of_the_same_ends(
        self,
        schema: Schema,
        context: MagicMock,
        scope_id: uuid.UUID,
        idle_checker_id: IdleCheckerID,
        relation_id: str,
    ) -> None:
        context.adapters.idle_checker_assignment.get.return_value = _assignment_node(
            scope_id, idle_checker_id
        )

        result = await _execute(schema, _NODE_QUERY, {"id": relation_id}, context)

        assert result.errors is None
        assert result.data == {
            "node": {
                "__typename": "IdleCheckerAssignment",
                "id": relation_id,
                "scopeType": "PROJECT",
                "scopeId": str(scope_id),
                "idleCheckerId": str(idle_checker_id),
            }
        }
        context.adapters.idle_checker_assignment.get.assert_awaited_once_with(
            IdleCheckerScopeRefDTO(scope_type=IdleCheckerScopeTypeDTO.PROJECT, scope_id=scope_id),
            idle_checker_id,
        )

    async def test_id_does_not_depend_on_the_row(
        self,
        schema: Schema,
        context: MagicMock,
        scope_id: uuid.UUID,
        idle_checker_id: IdleCheckerID,
        relation_id: str,
    ) -> None:
        context.adapters.idle_checker_assignment.get.side_effect = [
            _assignment_node(scope_id, idle_checker_id),
            _assignment_node(scope_id, idle_checker_id),
        ]

        first = await _execute(schema, _NODE_QUERY, {"id": relation_id}, context)
        second = await _execute(schema, _NODE_QUERY, {"id": relation_id}, context)

        assert first.data is not None and second.data is not None
        assert first.data["node"]["id"] == second.data["node"]["id"] == relation_id

    async def test_denied_scope_is_null_with_an_error(
        self, schema: Schema, context: MagicMock, relation_id: str
    ) -> None:
        context.adapters.idle_checker_assignment.get.side_effect = NotEnoughPermission()

        result = await _execute(schema, _NODE_QUERY, {"id": relation_id}, context)

        assert result.data == {"node": None}
        assert result.errors is not None

    async def test_missing_assignment_is_null(
        self, schema: Schema, context: MagicMock, relation_id: str
    ) -> None:
        context.adapters.idle_checker_assignment.get.side_effect = IdleCheckerAssignmentNotFound()

        result = await _execute(schema, _NODE_QUERY, {"id": relation_id}, context)

        assert result.errors is None
        assert result.data == {"node": None}

    @pytest.mark.parametrize(
        "ends",
        [
            ("project", "not-a-uuid", str(uuid.uuid4())),
            ("no_such_scope", str(uuid.uuid4()), str(uuid.uuid4())),
            ("project", str(uuid.uuid4())),
        ],
    )
    async def test_malformed_id_is_an_error(
        self, schema: Schema, context: MagicMock, ends: tuple[str, ...]
    ) -> None:
        global_id = to_relation_global_id(IdleCheckerAssignmentGQL, *ends)

        result = await _execute(schema, _NODE_QUERY, {"id": global_id}, context)

        assert result.data == {"node": None}
        assert result.errors is not None
        context.adapters.idle_checker_assignment.get.assert_not_awaited()
