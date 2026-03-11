from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent.row import AgentRow, agents

AgentFixtureData = dict[str, Any]
AgentFactory = Callable[..., Coroutine[Any, Any, AgentFixtureData]]


@pytest.fixture()
async def agent_factory(
    db_engine: SAEngine,
    scaling_group_fixture: str,
) -> AsyncIterator[AgentFactory]:
    """Factory fixture that creates agents via direct DB insertion and purges them on teardown."""
    created_ids: list[str] = []

    async def _create(**overrides: Any) -> AgentFixtureData:
        unique = secrets.token_hex(4)
        agent_id = f"i-agent-{unique}"
        defaults: dict[str, Any] = {
            "id": agent_id,
            "status": AgentStatus.ALIVE,
            "region": "test-region",
            "scaling_group": scaling_group_fixture,
            "schedulable": True,
            "available_slots": ResourceSlot({"cpu": "4", "mem": "8g"}),
            "occupied_slots": ResourceSlot(),
            "addr": f"192.168.1.{len(created_ids) + 10}:6001",
            "version": "24.03.0",
            "architecture": "x86_64",
            "compute_plugins": {},
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(agents).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    # Cleanup: remove agents in reverse order
    async with db_engine.begin() as conn:
        for aid in reversed(created_ids):
            await conn.execute(agents.delete().where(agents.c.id == aid))


@pytest.fixture()
async def target_agent(
    agent_factory: AgentFactory,
) -> AgentFixtureData:
    """Pre-created agent for tests that need an existing agent."""
    return await agent_factory()


class TestAgentSearch:
    """Test scenarios for agent search operations."""

    async def test_search_all_agents(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_factory: AgentFactory,
    ) -> None:
        """Search all agents returns paginated agent list."""
        # Create 3 test agents
        await agent_factory()
        await agent_factory()
        await agent_factory()

        result = await admin_registry.agent.paginated_list(
            status="ALIVE",
            page_size=10,
        )

        assert result.total >= 3
        assert len(result.items) >= 3

    async def test_search_with_status_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_factory: AgentFactory,
    ) -> None:
        """Search with status filter returns only matching agents."""
        # Create agents with different statuses
        await agent_factory(status=AgentStatus.ALIVE)
        await agent_factory(status=AgentStatus.LOST)

        alive_result = await admin_registry.agent.paginated_list(
            status="ALIVE",
            page_size=10,
        )
        lost_result = await admin_registry.agent.paginated_list(
            status="LOST",
            page_size=10,
        )

        # Check that ALIVE query returns at least our ALIVE agent
        assert alive_result.total >= 1
        alive_statuses = {item["status"] for item in alive_result.items}
        assert "ALIVE" in alive_statuses

        # Check that LOST query returns our LOST agent
        assert lost_result.total >= 1
        lost_statuses = {item["status"] for item in lost_result.items}
        assert "LOST" in lost_statuses

    async def test_search_with_scaling_group_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_factory: AgentFactory,
        db_engine: SAEngine,
    ) -> None:
        """Search with scaling_group filter returns agents in specific scaling group."""
        # Create a custom scaling group for isolation
        custom_sg = f"test-sg-{secrets.token_hex(4)}"
        async with db_engine.begin() as conn:
            from ai.backend.manager.models.scaling_group import scaling_groups

            await conn.execute(
                sa.insert(scaling_groups).values(
                    name=custom_sg,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts={},
                )
            )

        try:
            # Create agent in custom scaling group
            await agent_factory(scaling_group=custom_sg)

            result = await admin_registry.agent.paginated_list(
                status="ALIVE",
                scaling_group=custom_sg,
                page_size=10,
            )

            assert result.total >= 1
            for item in result.items:
                assert item["scaling_group"] == custom_sg
        finally:
            # Cleanup: agents will be cleaned up by agent_factory
            # Remove the scaling group
            async with db_engine.begin() as conn:
                await conn.execute(
                    scaling_groups.delete().where(scaling_groups.c.name == custom_sg)
                )

    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_factory: AgentFactory,
    ) -> None:
        """Search with pagination returns correct page."""
        # Create 5 test agents
        for _ in range(5):
            await agent_factory()

        # Get first page (2 items)
        page1 = await admin_registry.agent.paginated_list(
            status="ALIVE",
            page_offset=0,
            page_size=2,
        )
        # Get second page (2 items)
        page2 = await admin_registry.agent.paginated_list(
            status="ALIVE",
            page_offset=2,
            page_size=2,
        )

        assert len(page1.items) == 2
        assert len(page2.items) == 2
        # Items should be different
        page1_ids = {item["id"] for item in page1.items}
        page2_ids = {item["id"] for item in page2.items}
        assert page1_ids != page2_ids

    async def test_search_with_sorting(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_factory: AgentFactory,
    ) -> None:
        """Search with sorting returns correctly ordered results."""
        # Create agents with different IDs
        agent1 = await agent_factory(id="i-agent-aaa")
        agent2 = await agent_factory(id="i-agent-zzz")

        # Sort by id ascending
        result_asc = await admin_registry.agent.paginated_list(
            status="ALIVE",
            order="id",
            page_size=100,
        )
        # Sort by id descending
        result_desc = await admin_registry.agent.paginated_list(
            status="ALIVE",
            order="-id",
            page_size=100,
        )

        # Find our test agents in results
        ids_asc = [item["id"] for item in result_asc.items]
        ids_desc = [item["id"] for item in result_desc.items]

        # Check that our agents appear in expected order
        aaa_idx_asc = ids_asc.index(agent1["id"]) if agent1["id"] in ids_asc else -1
        zzz_idx_asc = ids_asc.index(agent2["id"]) if agent2["id"] in ids_asc else -1
        aaa_idx_desc = ids_desc.index(agent1["id"]) if agent1["id"] in ids_desc else -1
        zzz_idx_desc = ids_desc.index(agent2["id"]) if agent2["id"] in ids_desc else -1

        if aaa_idx_asc >= 0 and zzz_idx_asc >= 0:
            assert aaa_idx_asc < zzz_idx_asc  # aaa comes before zzz in ascending
        if aaa_idx_desc >= 0 and zzz_idx_desc >= 0:
            assert aaa_idx_desc > zzz_idx_desc  # aaa comes after zzz in descending

    async def test_compound_filters(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_factory: AgentFactory,
        scaling_group_fixture: str,
    ) -> None:
        """Compound filters return intersection of conditions."""
        # Create agents with different combinations
        await agent_factory(status=AgentStatus.ALIVE, scaling_group=scaling_group_fixture)
        await agent_factory(status=AgentStatus.LOST, scaling_group=scaling_group_fixture)

        result = await admin_registry.agent.paginated_list(
            status="ALIVE",
            scaling_group=scaling_group_fixture,
            page_size=100,
        )

        # All results should match both filters
        for item in result.items:
            if item["scaling_group"] == scaling_group_fixture:
                assert item["status"] == "ALIVE"

    async def test_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Empty result returns total=0 and empty items."""
        # Search for a non-existent scaling group
        nonexistent_sg = f"nonexistent-sg-{secrets.token_hex(8)}"

        result = await admin_registry.agent.paginated_list(
            status="ALIVE",
            scaling_group=nonexistent_sg,
            page_size=10,
        )

        assert result.total == 0
        assert len(result.items) == 0
