"""Tests for the Relay ``node(id:)`` and ``nodes(ids:)`` root fields."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
import strawberry
from strawberry.dataloader import DataLoader
from strawberry.federation import Schema
from strawberry.relay import to_base64
from strawberry.tools import create_type

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.dto.manager.v2.entity.response import EntityTypeNode, ListEntityTypesPayload
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.gql.entity.types.node import EntityTypeGQL
from ai.backend.manager.api.gql.fair_share.types.domain import DomainFairShareGQL
from ai.backend.manager.api.gql.node_field import node, nodes
from ai.backend.manager.api.gql.role_preset.types.node import RolePresetGQL
from ai.backend.manager.errors.permission import NotEnoughPermission

_NODES_QUERY = """
query ($ids: [ID!]!) {
  nodes(ids: $ids) { __typename id }
}
"""

_NODE_QUERY = """
query ($id: ID!) {
  node(id: $id) { __typename id }
}
"""


@pytest.fixture
def schema() -> Schema:
    return Schema(
        query=create_type("Query", [node, nodes]),
        types=[EntityTypeGQL, DomainFairShareGQL, RolePresetGQL],
        federation_version="2.7",
    )


@pytest.fixture
def readable_preset_id() -> RolePresetID:
    return RolePresetID(uuid.uuid4())


@pytest.fixture
def denied_preset_id() -> RolePresetID:
    return RolePresetID(uuid.uuid4())


@pytest.fixture
def missing_preset_id() -> RolePresetID:
    return RolePresetID(uuid.uuid4())


@pytest.fixture
def preset_batches() -> list[list[RolePresetID]]:
    return []


@pytest.fixture
def context(
    readable_preset_id: RolePresetID,
    denied_preset_id: RolePresetID,
    preset_batches: list[list[RolePresetID]],
) -> MagicMock:
    now = datetime(2026, 10, 13, tzinfo=UTC)

    async def load_presets(
        ids: Sequence[RolePresetID],
    ) -> list[RolePresetGQL | Exception | None]:
        preset_batches.append(list(ids))
        results: list[RolePresetGQL | Exception | None] = []
        for preset_id in ids:
            if preset_id == readable_preset_id:
                results.append(
                    RolePresetGQL.from_pydantic(
                        RolePresetNode(
                            id=preset_id,
                            entity_id=preset_id,
                            name="preset",
                            scope_type=DomainEntityType(),
                            auto_assign=False,
                            deleted=False,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                )
            elif preset_id == denied_preset_id:
                results.append(NotEnoughPermission())
            else:
                results.append(None)
        return results

    ctx = MagicMock()
    ctx.adapters.entity.list_entity_types.return_value = ListEntityTypesPayload(
        items=[EntityTypeNode(name="domain")]
    )
    ctx.data_loaders.role_preset_loader = DataLoader(load_fn=load_presets)
    return ctx


async def _execute(
    schema: Schema, query: str, variables: dict[str, Any], context: MagicMock
) -> strawberry.types.ExecutionResult:
    return await schema.execute(query, variable_values=variables, context_value=context)


class TestNodes:
    async def test_returns_nodes_of_several_types_in_the_given_order(
        self,
        schema: Schema,
        context: MagicMock,
        readable_preset_id: RolePresetID,
        missing_preset_id: RolePresetID,
    ) -> None:
        ids = [
            to_base64("RolePreset", str(readable_preset_id)),
            to_base64("EntityType", "domain"),
            to_base64("RolePreset", str(missing_preset_id)),
            to_base64("EntityType", "no-such-type"),
        ]

        result = await _execute(schema, _NODES_QUERY, {"ids": ids}, context)

        assert result.errors is None
        assert result.data == {
            "nodes": [
                {"__typename": "RolePreset", "id": ids[0]},
                {"__typename": "EntityType", "id": ids[1]},
                None,
                None,
            ]
        }

    async def test_reads_ids_of_one_type_in_one_batch(
        self,
        schema: Schema,
        context: MagicMock,
        readable_preset_id: RolePresetID,
        missing_preset_id: RolePresetID,
        preset_batches: list[list[RolePresetID]],
    ) -> None:
        ids = [
            to_base64("RolePreset", str(readable_preset_id)),
            to_base64("EntityType", "domain"),
            to_base64("RolePreset", str(missing_preset_id)),
        ]

        await _execute(schema, _NODES_QUERY, {"ids": ids}, context)

        assert preset_batches == [[readable_preset_id, missing_preset_id]]

    async def test_denied_id_is_null_with_its_own_error(
        self,
        schema: Schema,
        context: MagicMock,
        readable_preset_id: RolePresetID,
        denied_preset_id: RolePresetID,
    ) -> None:
        ids = [
            to_base64("RolePreset", str(denied_preset_id)),
            to_base64("RolePreset", str(readable_preset_id)),
        ]

        result = await _execute(schema, _NODES_QUERY, {"ids": ids}, context)

        assert result.data == {"nodes": [None, {"__typename": "RolePreset", "id": ids[1]}]}
        assert result.errors is not None
        assert [error.path for error in result.errors] == [["nodes", 0]]

    async def test_fair_share_id_is_null(self, schema: Schema, context: MagicMock) -> None:
        ids = [to_base64("DomainFairShare", "default:default")]

        result = await _execute(schema, _NODES_QUERY, {"ids": ids}, context)

        assert result.errors is None
        assert result.data == {"nodes": [None]}


class TestNode:
    async def test_returns_the_node(
        self, schema: Schema, context: MagicMock, readable_preset_id: RolePresetID
    ) -> None:
        node_id = to_base64("RolePreset", str(readable_preset_id))

        result = await _execute(schema, _NODE_QUERY, {"id": node_id}, context)

        assert result.errors is None
        assert result.data == {"node": {"__typename": "RolePreset", "id": node_id}}

    async def test_fair_share_id_is_null(self, schema: Schema, context: MagicMock) -> None:
        node_id = to_base64("DomainFairShare", "default:default")

        result = await _execute(schema, _NODE_QUERY, {"id": node_id}, context)

        assert result.errors is None
        assert result.data == {"node": None}
