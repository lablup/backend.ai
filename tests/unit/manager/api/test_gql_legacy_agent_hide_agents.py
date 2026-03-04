"""
Regression test: superadmin must bypass hide_agents restriction
in agent_summary and agent_summary_list GQL resolvers. (BA-4862)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest

from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.user import UserRole


def _make_mock_info(role: UserRole) -> MagicMock:
    ctx = MagicMock()
    ctx.user = {
        "role": role,
        "domain_name": "default",
        "uuid": uuid.uuid4(),
        "email": "test@test.com",
    }
    ctx.access_key = "TESTKEY"
    ctx.config_provider.config.manager.hide_agents = True
    info = MagicMock(spec=graphene.ResolveInfo)
    info.context = ctx
    return info


class TestAgentSummaryHideAgents:
    """Superadmin must bypass hide_agents in agent_summary resolvers."""

    async def test_agent_summary_allows_superadmin_when_hide_agents(self) -> None:
        info = _make_mock_info(UserRole.SUPERADMIN)
        loader = AsyncMock()
        loader.load = AsyncMock(return_value=MagicMock())
        info.context.dataloader_manager.get_loader_by_func.return_value = loader

        result = await Query.resolve_agent_summary(
            None,
            info,
            agent_id="test-agent-id",
        )
        assert result is not None

    async def test_agent_summary_blocks_non_superadmin_when_hide_agents(self) -> None:
        info = _make_mock_info(UserRole.ADMIN)

        with pytest.raises(ObjectNotFound):
            await Query.resolve_agent_summary(
                None,
                info,
                agent_id="test-agent-id",
            )

    async def test_agent_summary_list_allows_superadmin_when_hide_agents(self) -> None:
        info = _make_mock_info(UserRole.SUPERADMIN)
        info.context.__class__ = type("GraphQueryContext", (), {})
        mock_load_count = AsyncMock(return_value=1)
        mock_load_slice = AsyncMock(return_value=[MagicMock()])

        with (
            pytest.MonkeyPatch.context() as mp,
        ):
            mp.setattr(
                "ai.backend.manager.api.gql_legacy.agent.AgentSummary.load_count",
                mock_load_count,
            )
            mp.setattr(
                "ai.backend.manager.api.gql_legacy.agent.AgentSummary.load_slice",
                mock_load_slice,
            )
            result = await Query.resolve_agent_summary_list(
                None,
                info,
                limit=50,
                offset=0,
            )
        assert result is not None

    async def test_agent_summary_list_blocks_non_superadmin_when_hide_agents(self) -> None:
        info = _make_mock_info(UserRole.USER)

        with pytest.raises(ObjectNotFound):
            await Query.resolve_agent_summary_list(
                None,
                info,
                limit=50,
                offset=0,
            )
