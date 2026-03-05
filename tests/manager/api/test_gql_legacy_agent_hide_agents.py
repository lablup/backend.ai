"""
Regression test: superadmin must bypass hide_agents restriction
in agent_summary and agent_summary_list GQL resolvers. (BA-4862)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest

from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.gql import Query
from ai.backend.manager.models.user import UserRole


class TestAgentSummaryHideAgents:
    """Superadmin must bypass hide_agents in agent_summary resolvers."""

    @pytest.fixture
    def mock_info_with_hide_agents_true(self, request: pytest.FixtureRequest) -> MagicMock:
        role: UserRole = request.param
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

    @pytest.fixture
    def mock_info_with_hide_agents_false(self, request: pytest.FixtureRequest) -> MagicMock:
        role: UserRole = request.param
        ctx = MagicMock()
        ctx.user = {
            "role": role,
            "domain_name": "default",
            "uuid": uuid.uuid4(),
            "email": "test@test.com",
        }
        ctx.access_key = "TESTKEY"
        ctx.config_provider.config.manager.hide_agents = False
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

    @pytest.mark.parametrize(
        "mock_info_with_hide_agents_true", [UserRole.SUPERADMIN], indirect=True
    )
    async def test_agent_summary_allows_superadmin(
        self, mock_info_with_hide_agents_true: MagicMock
    ) -> None:
        loader = AsyncMock()
        loader.load = AsyncMock(return_value=MagicMock())
        mock_info_with_hide_agents_true.context.dataloader_manager.get_loader_by_func.return_value = loader

        result = await Query.resolve_agent_summary(
            None,
            mock_info_with_hide_agents_true,
            agent_id="test-agent-id",
        )
        assert result is not None

    @pytest.mark.parametrize(
        "mock_info_with_hide_agents_true", [UserRole.ADMIN, UserRole.USER], indirect=True
    )
    async def test_agent_summary_blocks_non_superadmin(
        self, mock_info_with_hide_agents_true: MagicMock
    ) -> None:
        with pytest.raises(ObjectNotFound):
            await Query.resolve_agent_summary(
                None,
                mock_info_with_hide_agents_true,
                agent_id="test-agent-id",
            )

    @pytest.fixture
    def mock_agent_summary_loader(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "ai.backend.manager.models.gql_models.agent.AgentSummary.load_count",
            AsyncMock(return_value=1),
        )
        monkeypatch.setattr(
            "ai.backend.manager.models.gql_models.agent.AgentSummary.load_slice",
            AsyncMock(return_value=[MagicMock()]),
        )

    @pytest.mark.parametrize(
        "mock_info_with_hide_agents_true", [UserRole.SUPERADMIN], indirect=True
    )
    @pytest.mark.usefixtures("mock_agent_summary_loader")
    async def test_agent_summary_list_allows_superadmin(
        self, mock_info_with_hide_agents_true: MagicMock
    ) -> None:
        mock_info_with_hide_agents_true.context.__class__ = type("GraphQueryContext", (), {})

        result = await Query.resolve_agent_summary_list(
            None,
            mock_info_with_hide_agents_true,
            limit=50,
            offset=0,
        )
        assert result is not None

    @pytest.mark.parametrize(
        "mock_info_with_hide_agents_true", [UserRole.ADMIN, UserRole.USER], indirect=True
    )
    async def test_agent_summary_list_blocks_non_superadmin(
        self, mock_info_with_hide_agents_true: MagicMock
    ) -> None:
        with pytest.raises(ObjectNotFound):
            await Query.resolve_agent_summary_list(
                None,
                mock_info_with_hide_agents_true,
                limit=50,
                offset=0,
            )

    @pytest.mark.parametrize(
        "mock_info_with_hide_agents_false",
        [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.USER],
        indirect=True,
    )
    async def test_agent_summary_allows_any_role_when_hide_agents_disabled(
        self, mock_info_with_hide_agents_false: MagicMock
    ) -> None:
        loader = AsyncMock()
        loader.load = AsyncMock(return_value=MagicMock())
        mock_info_with_hide_agents_false.context.dataloader_manager.get_loader_by_func.return_value = loader

        result = await Query.resolve_agent_summary(
            None,
            mock_info_with_hide_agents_false,
            agent_id="test-agent-id",
        )
        assert result is not None

    @pytest.mark.parametrize(
        "mock_info_with_hide_agents_false",
        [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.USER],
        indirect=True,
    )
    @pytest.mark.usefixtures("mock_agent_summary_loader")
    async def test_agent_summary_list_allows_any_role_when_hide_agents_disabled(
        self, mock_info_with_hide_agents_false: MagicMock
    ) -> None:
        mock_info_with_hide_agents_false.context.__class__ = type("GraphQueryContext", (), {})

        result = await Query.resolve_agent_summary_list(
            None,
            mock_info_with_hide_agents_false,
            limit=50,
            offset=0,
        )
        assert result is not None
