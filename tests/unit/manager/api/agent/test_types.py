"""
Tests for Agent GraphQL types.

Tests the GraphQL type layer for agent-related queries.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import AgentId, ResourceSlot, SlotName
from ai.backend.manager.api.gql_legacy.agent import AgentSummary
from ai.backend.manager.data.agent.types import AgentData, AgentStatus


def create_mock_agent_data(
    agent_id: str,
    status: AgentStatus = AgentStatus.ALIVE,
    scaling_group: str = "default",
) -> AgentData:
    """Create a mock AgentData for testing."""
    return AgentData(
        id=AgentId(agent_id),
        status=status,
        status_changed=None,
        region="test-region",
        scaling_group=scaling_group,
        schedulable=True,
        available_slots=ResourceSlot({SlotName("cpu"): Decimal("8")}),
        cached_occupied_slots=ResourceSlot({}),
        actual_occupied_slots=ResourceSlot({}),
        addr="tcp://127.0.0.1:6001",
        public_host="127.0.0.1",
        first_contact=None,
        lost_at=None,
        version="24.12.0",
        architecture="x86_64",
        compute_plugins={},
        public_key=None,
        auto_terminate_abusing_kernel=False,
    )


class TestAgentSummaryLoadSlice:
    """Tests for AgentSummary.load_slice method."""

    @pytest.fixture
    def mock_graph_ctx(self) -> MagicMock:
        """Create a mock GraphQueryContext."""
        ctx = MagicMock()
        ctx.db = MagicMock()
        ctx.agent_repository = MagicMock()
        return ctx

    @pytest.fixture
    def mock_session_with_pagination_bug(self) -> AsyncMock:
        """
        Mock DB session simulating pagination bug caused by JOIN with KernelRow.

        OLD code (scalars): Returns only 1 agent due to JOIN row multiplication
        NEW code (execute): Returns both agents correctly
        """
        mock_session = AsyncMock()

        # OLD code path: scalars() -> unique().all() -> row.id
        # Simulates bug: JOIN causes only 1 unique agent after LIMIT
        mock_unique_result = MagicMock()
        mock_unique_result.all.return_value = [
            MagicMock(id="agent-001"),
            # agent-002 missing: LIMIT 20 consumed by agent-001's kernel rows
        ]
        mock_scalars_result = MagicMock()
        mock_scalars_result.unique.return_value = mock_unique_result
        mock_session.scalars = AsyncMock(return_value=mock_scalars_result)

        # NEW code path: execute() -> iterate rows -> row[0]
        # Returns both agents correctly
        mock_execute_result = MagicMock()
        mock_execute_result.__iter__ = lambda _: iter([
            (AgentId("agent-001"),),
            (AgentId("agent-002"),),
        ])
        mock_session.execute = AsyncMock(return_value=mock_execute_result)

        return mock_session

    async def test_pagination_not_affected_by_kernel_count(
        self,
        mock_graph_ctx: MagicMock,
        mock_session_with_pagination_bug: AsyncMock,
    ) -> None:
        """
        Regression test: Pagination returns correct agent count regardless of kernel count.

        Previously, JOIN with KernelRow caused agents with many kernels to consume
        multiple LIMIT slots, returning fewer unique agents than expected.
        """
        mock_graph_ctx.db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session_with_pagination_bug)
            )
        )

        agent_data_map = {
            AgentId("agent-001"): create_mock_agent_data("agent-001"),
            AgentId("agent-002"): create_mock_agent_data("agent-002"),
        }
        requested_ids: list[AgentId] = []

        def capture_ids(ids: list[AgentId]) -> MagicMock:
            requested_ids.clear()
            requested_ids.extend(ids)
            return MagicMock()

        async def mock_list_data(_: list) -> list[AgentData]:
            return [agent_data_map[aid] for aid in requested_ids if aid in agent_data_map]

        mock_graph_ctx.agent_repository.list_data = AsyncMock(side_effect=mock_list_data)

        with (
            patch(
                "ai.backend.manager.api.gql_legacy.agent.QueryConditions.by_ids",
                side_effect=capture_ids,
            ),
            patch(
                "ai.backend.manager.api.gql_legacy.agent._append_sgroup_from_clause",
                new=AsyncMock(side_effect=lambda _ctx, query, *_a, **_kw: query),
            ),
        ):
            result = await AgentSummary.load_slice(
                mock_graph_ctx,
                limit=20,
                offset=0,
                access_key="AKIATEST",
            )

        assert len(result) == 2
