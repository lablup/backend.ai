from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.etcd_config.repository import EtcdConfigRepository
from ai.backend.testutils.db import with_tables


class TestEtcdConfigRepository:
    """Integration tests for EtcdConfigRepository with a real database."""

    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [ResourceGroupRow, AgentRow, ResourceSlotTypeRow, AgentResourceRow],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> EtcdConfigRepository:
        return EtcdConfigRepository(database)

    async def _seed_agents(self, database: ExtendedAsyncSAEngine, scaling_group: str) -> None:
        resource_group_id = ResourceGroupID(uuid4())
        agent_ids = [str(uuid4()), str(uuid4())]
        async with database.begin_session() as db_sess:
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=scaling_group,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            db_sess.add_all([
                ResourceSlotTypeRow(slot_name="cpu", slot_type="count", rank=0),
                ResourceSlotTypeRow(slot_name="mem", slot_type="bytes", rank=0),
                ResourceSlotTypeRow(slot_name="cuda.device", slot_type="count", rank=0),
            ])
            for index, agent_id in enumerate(agent_ids):
                db_sess.add(
                    AgentRow(
                        id=agent_id,
                        status=AgentStatus.ALIVE,
                        status_changed=datetime.now(UTC),
                        region="test-region",
                        scaling_group=scaling_group,
                        resource_group_id=resource_group_id,
                        addr=f"tcp://127.0.0.1:{6001 + index}",
                        version="26.9.0",
                        architecture="x86_64",
                        compute_plugins={},
                    )
                )
            db_sess.add_all([
                AgentResourceRow(agent_id=agent_ids[0], slot_name="cpu", capacity=Decimal("8")),
                AgentResourceRow(agent_id=agent_ids[0], slot_name="mem", capacity=Decimal("32768")),
                AgentResourceRow(agent_id=agent_ids[1], slot_name="cpu", capacity=Decimal("16")),
                AgentResourceRow(
                    agent_id=agent_ids[1], slot_name="cuda.device", capacity=Decimal("2")
                ),
            ])

    async def test_get_available_agent_slots_returns_slot_keys(
        self,
        repository: EtcdConfigRepository,
        database: ExtendedAsyncSAEngine,
    ) -> None:
        """When agents exist with slots, returns the union of all slot keys."""
        await self._seed_agents(database, "default")

        assert await repository.get_available_agent_slots("default") == {
            "cpu",
            "mem",
            "cuda.device",
        }

    async def test_get_available_agent_slots_empty_when_no_agents(
        self,
        repository: EtcdConfigRepository,
    ) -> None:
        """When no agents match, returns an empty set."""
        result = await repository.get_available_agent_slots("nonexistent-sgroup")
        assert result == set()
