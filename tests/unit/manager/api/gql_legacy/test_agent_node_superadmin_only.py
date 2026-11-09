"""AgentNode.get_node (node(id:) and the federation reference) resolves only for a superadmin. (BA-8882)"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
from graphql_relay import to_global_id

from ai.backend.manager.api.gql_legacy.agent import AgentNode
from ai.backend.manager.models.user.row import UserRole


class TestAgentNodeSuperadminOnly:
    @pytest.fixture
    def make_info(self) -> Callable[[UserRole], graphene.ResolveInfo]:
        def _make(role: UserRole) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = {"role": role, "domain_name": "default", "uuid": uuid.uuid4()}
            ctx.agent_repository.list_data = AsyncMock(return_value=[])
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    @pytest.fixture
    def agent_global_id(self) -> str:
        return to_global_id("AgentNode", "i-agent-1")

    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.ADMIN, UserRole.MONITOR],
        ids=["user", "admin", "monitor"],
    )
    async def test_a_non_superadmin_gets_null_without_a_repository_read(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        agent_global_id: str,
        role: UserRole,
    ) -> None:
        info = make_info(role)
        assert await AgentNode.get_node(info, agent_global_id) is None
        info.context.agent_repository.list_data.assert_not_called()

    async def test_a_superadmin_reaches_the_agent_repository(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        agent_global_id: str,
    ) -> None:
        info = make_info(UserRole.SUPERADMIN)
        assert await AgentNode.get_node(info, agent_global_id) is None
        info.context.agent_repository.list_data.assert_awaited_once()
