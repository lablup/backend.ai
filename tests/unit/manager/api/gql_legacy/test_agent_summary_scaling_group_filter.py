"""agentSummaryList with a resource group named stays within the allowed ones. (BA-8902)"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.api.gql_legacy.agent import _append_sgroup_from_clause
from ai.backend.manager.models.agent.row import AgentRow


class TestAgentSummaryScalingGroupFilter:
    async def test_a_named_resource_group_is_still_bounded_by_the_allowed_ones(self) -> None:
        graph_ctx = MagicMock()
        graph_ctx.db.begin_readonly = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=MagicMock()),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        graph_ctx.scheduler_repository.get_domain_id_by_name = AsyncMock(return_value=uuid.uuid4())
        allowed = MagicMock()
        allowed.name = "rg-allowed"
        graph_ctx.scheduler_repository.query_allowed_resource_groups = AsyncMock(
            return_value=[allowed]
        )
        with patch(
            "ai.backend.manager.api.gql_legacy.agent._query_domain_groups_by_ak",
            AsyncMock(return_value=("default", UserID(uuid.uuid4()), [])),
        ):
            query = await _append_sgroup_from_clause(
                graph_ctx, sa.select(AgentRow), "AKIACALLER", None, scaling_group="rg-other"
            )
        where = str(query.whereclause)
        assert "agents.scaling_group IN" in where
        assert "agents.scaling_group =" in where
