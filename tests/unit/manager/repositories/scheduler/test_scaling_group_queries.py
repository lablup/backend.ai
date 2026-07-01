"""
Tests for resource-group discovery queries in ScheduleDBSource.

Regression coverage for BA-5629: session status promotions must run on
resource groups even when all their agents have ``schedulable=False``.
"""

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ScalingGroupFixture:
    """Named resource groups used by the mixed-agent scenario."""

    schedulable: str
    unschedulable: str
    lost: str
    empty: str


async def _make_scaling_group(db: ExtendedAsyncSAEngine, name: str) -> None:
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


class TestScalingGroupQueries:
    """Tests for get_schedulable_scaling_groups / get_all_scaling_groups."""

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

    @pytest.fixture
    async def mixed_agents_scenario(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ScalingGroupFixture:
        """Four resource groups covering schedulable, unschedulable, lost, and empty cases:

        - ``schedulable``: ALIVE + schedulable=True
        - ``unschedulable``: ALIVE + schedulable=False (the BA-5629 case)
        - ``lost``: LOST + schedulable=True (included only in the all-groups query)
        - ``empty``: no agents at all (must still be included in the all-groups query)
        """
        fixture = ScalingGroupFixture(
            schedulable=f"sg-sched-{uuid.uuid4().hex[:8]}",
            unschedulable=f"sg-unsched-{uuid.uuid4().hex[:8]}",
            lost=f"sg-lost-{uuid.uuid4().hex[:8]}",
            empty=f"sg-empty-{uuid.uuid4().hex[:8]}",
        )
        await _make_scaling_group(db_with_cleanup, fixture.schedulable)
        await _make_scaling_group(db_with_cleanup, fixture.unschedulable)
        await _make_scaling_group(db_with_cleanup, fixture.lost)
        await _make_scaling_group(db_with_cleanup, fixture.empty)
        await _make_agent(
            db_with_cleanup,
            fixture.schedulable,
            status=AgentStatus.ALIVE,
            schedulable=True,
        )
        await _make_agent(
            db_with_cleanup,
            fixture.unschedulable,
            status=AgentStatus.ALIVE,
            schedulable=False,
        )
        await _make_agent(
            db_with_cleanup,
            fixture.lost,
            status=AgentStatus.LOST,
            schedulable=True,
        )
        return fixture

    async def test_schedulable_query_excludes_unschedulable_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mixed_agents_scenario: ScalingGroupFixture,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup)
        schedulable = set(await db_source.get_schedulable_scaling_groups())

        assert mixed_agents_scenario.schedulable in schedulable
        assert mixed_agents_scenario.unschedulable not in schedulable
        assert mixed_agents_scenario.lost not in schedulable
        assert mixed_agents_scenario.empty not in schedulable

    async def test_all_scaling_groups_query_includes_unschedulable_and_lost_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mixed_agents_scenario: ScalingGroupFixture,
    ) -> None:
        """Regression for BA-5629.

        ``get_all_scaling_groups()`` must return all defined resource groups,
        even when they have no ALIVE, schedulable, or any agents, so that coordinator
        promotion and termination checks still visit sessions pinned there.
        """
        db_source = ScheduleDBSource(db_with_cleanup)
        scaling_groups = set(await db_source.get_all_scaling_groups())

        assert mixed_agents_scenario.schedulable in scaling_groups
        assert mixed_agents_scenario.unschedulable in scaling_groups
        assert mixed_agents_scenario.lost in scaling_groups
        assert mixed_agents_scenario.empty in scaling_groups
