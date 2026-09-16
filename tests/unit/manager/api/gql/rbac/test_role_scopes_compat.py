"""Tests for the deprecated `Role.scopes` connection kept for older clients."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.dto.manager.v2.rbac.types import RoleSourceDTO, RoleStatusDTO
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.rbac.types.entity import (
    EntityFilterGQL,
    EntityOrderByGQL,
    EntityOrderField,
)
from ai.backend.manager.api.gql.rbac.types.role import RoleGQL


@pytest.fixture
def role() -> RoleGQL:
    created_at = datetime(2026, 9, 10, tzinfo=UTC)
    return RoleGQL(
        id=str(uuid.uuid4()),
        name="member",
        description=None,
        source=RoleSourceDTO.CUSTOM,
        status=RoleStatusDTO.ACTIVE,
        created_at=created_at,
        updated_at=created_at,
        deleted_at=None,
        auto_assign=False,
        scope_type="project",
        scope_id=uuid.uuid4(),
    )


class TestRoleScopes:
    async def test_holds_the_scope_the_role_belongs_to(self, role: RoleGQL) -> None:
        connection = await role.scopes()

        assert connection is not None
        assert connection.count == 1
        (edge,) = connection.edges
        assert edge.node.scope_type == role.scope_type
        assert edge.node.scope_id == str(role.scope_id)
        assert edge.node.entity_type == "role"
        assert edge.node.entity_id == role.id
        assert edge.node.registered_at == role.created_at

    @pytest.mark.parametrize(
        "page",
        [
            pytest.param({"offset": 1}, id="offset-past-the-scope"),
            pytest.param({"first": 0}, id="first-none"),
            pytest.param({"limit": 0}, id="limit-none"),
        ],
    )
    async def test_page_holding_nothing_is_empty(self, role: RoleGQL, page: dict[str, Any]) -> None:
        connection = await role.scopes(**page)

        assert connection is not None
        assert connection.edges == []
        assert connection.count == 1

    async def test_filter_and_order_are_ignored(self, role: RoleGQL) -> None:
        connection = await role.scopes(
            filter=EntityFilterGQL(scope_type=StringFilter(equals="domain")),
            order_by=[
                EntityOrderByGQL(field=EntityOrderField.REGISTERED_AT, direction=OrderDirection.ASC)
            ],
        )

        assert connection is not None
        assert len(connection.edges) == 1


class TestEntityRefResolvedNodes:
    @pytest.fixture
    def mock_info(self) -> MagicMock:
        info = MagicMock()
        info.context.data_loaders.entity_node_loader.load = AsyncMock(return_value=None)
        return info

    async def test_entity_is_loaded_as_a_role(self, role: RoleGQL, mock_info: MagicMock) -> None:
        connection = await role.scopes()
        assert connection is not None
        (edge,) = connection.edges

        await edge.node.entity(info=mock_info)

        loaded_id = mock_info.context.data_loaders.entity_node_loader.load.call_args.args[0]
        assert isinstance(loaded_id.entity_type(), RoleEntityType)
        assert loaded_id == uuid.UUID(role.id)

    async def test_scope_is_loaded_as_the_scope_kind(
        self, role: RoleGQL, mock_info: MagicMock
    ) -> None:
        connection = await role.scopes()
        assert connection is not None
        (edge,) = connection.edges

        await edge.node.scope(info=mock_info)

        loaded_id = mock_info.context.data_loaders.entity_node_loader.load.call_args.args[0]
        assert isinstance(loaded_id.entity_type(), ProjectEntityType)
        assert loaded_id == role.scope_id
