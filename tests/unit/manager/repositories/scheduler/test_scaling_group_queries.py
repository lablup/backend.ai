"""
Tests for scaling-group discovery queries in ScheduleDBSource.

Regression coverage for BA-5629: session status promotions must run on
scaling groups even when all their agents have ``schedulable=False``.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.db import with_tables


class TestScalingGroupQueries:
    """Tests for get_schedulable_scaling_groups / get_scaling_groups_with_active_agents."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ScalingGroupRow,
                AgentRow,
            ],
        ):
            yield database_connection

    async def _make_scaling_group(
        self, db: ExtendedAsyncSAEngine, name: str
    ) -> None:
        async with db.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(
                        allowed_session_types=[],
                        pending_timeout=timedelta(hours=1),
                        config={},
                    ),
                    driver_opts={},
                    is_active=True,
                )
            )

    async def _make_agent(
        self,
        db: ExtendedAsyncSAEngine,
        scaling_group: str,
        *,
        status: AgentStatus,
        schedulable: bool,
    ) -> AgentId:
        agent_id = AgentId(f"test-agent-{uuid.uuid4().hex[:8]}")
        async with db.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=status,
                    region="local",
                    scaling_group=scaling_group,
                    available_slots=ResourceSlot({
                        "cpu": Decimal("10"),
                        "mem": Decimal("10240"),
                    }),
                    occupied_slots=ResourceSlot(),
                    addr="127.0.0.1:6001",
                    version="1.0.0",
                    architecture="x86_64",
                    schedulable=schedulable,
                )
            )
        return agent_id

    async def test_schedulable_query_excludes_unschedulable_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        sg_schedulable = f"sg-sched-{uuid.uuid4().hex[:8]}"
        sg_unschedulable = f"sg-unsched-{uuid.uuid4().hex[:8]}"
        await self._make_scaling_group(db_with_cleanup, sg_schedulable)
        await self._make_scaling_group(db_with_cleanup, sg_unschedulable)
        await self._make_agent(
            db_with_cleanup,
            sg_schedulable,
            status=AgentStatus.ALIVE,
            schedulable=True,
        )
        await self._make_agent(
            db_with_cleanup,
            sg_unschedulable,
            status=AgentStatus.ALIVE,
            schedulable=False,
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        schedulable = set(await db_source.get_schedulable_scaling_groups())

        assert sg_schedulable in schedulable
        assert sg_unschedulable not in schedulable

    async def test_active_query_includes_unschedulable_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Regression for BA-5629.

        ``get_scaling_groups_with_active_agents()`` must return scaling
        groups whose only ALIVE agents have ``schedulable=False``, so that
        session status promotions (e.g. TERMINATING -> TERMINATED) still
        run for sessions pinned to those agents.
        """
        sg_schedulable = f"sg-sched-{uuid.uuid4().hex[:8]}"
        sg_unschedulable = f"sg-unsched-{uuid.uuid4().hex[:8]}"
        sg_lost = f"sg-lost-{uuid.uuid4().hex[:8]}"
        await self._make_scaling_group(db_with_cleanup, sg_schedulable)
        await self._make_scaling_group(db_with_cleanup, sg_unschedulable)
        await self._make_scaling_group(db_with_cleanup, sg_lost)
        await self._make_agent(
            db_with_cleanup,
            sg_schedulable,
            status=AgentStatus.ALIVE,
            schedulable=True,
        )
        await self._make_agent(
            db_with_cleanup,
            sg_unschedulable,
            status=AgentStatus.ALIVE,
            schedulable=False,
        )
        await self._make_agent(
            db_with_cleanup,
            sg_lost,
            status=AgentStatus.LOST,
            schedulable=True,
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        active = set(await db_source.get_scaling_groups_with_active_agents())

        assert sg_schedulable in active
        assert sg_unschedulable in active
        assert sg_lost not in active
