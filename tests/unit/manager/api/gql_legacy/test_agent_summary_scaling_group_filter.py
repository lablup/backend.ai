"""agentSummaryList with a resource group named stays within the allowed ones."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import sqlalchemy as sa

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
        allowed = MagicMock()
        allowed.name = "rg-allowed"
        with (
            patch(
                "ai.backend.manager.api.gql_legacy.agent._query_domain_groups_by_ak",
                AsyncMock(return_value=("default", [])),
            ),
            patch(
                "ai.backend.manager.models.scaling_group.query_allowed_sgroups",
                AsyncMock(return_value=[allowed]),
            ),
        ):
            query = await _append_sgroup_from_clause(
                graph_ctx, sa.select(AgentRow), "AKIACALLER", None, scaling_group="rg-other"
            )
        where = str(query.whereclause)
        assert "agents.scaling_group IN" in where
        assert "agents.scaling_group =" in where
