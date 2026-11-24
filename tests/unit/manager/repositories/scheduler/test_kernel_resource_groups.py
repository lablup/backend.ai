"""Sessions with kernels in a resource group other than the session's, in the scheduling fetch."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.schema.resource_group import PreemptionConfig
from ai.backend.common.types import AccessKey, AgentId, KernelId, SessionId
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.views.sokovan.workload import PreemptionScopeKey
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels


@dataclass(frozen=True)
class _ResourceGroupWithAgent:
    id: ResourceGroupID
    name: str
    agent_id: str


@dataclass(frozen=True)
class _SpanningSession:
    """A session whose second kernel is in the other resource group."""

    session_id: SessionId
    kernel_id_in_session_group: KernelId
    kernel_id_in_other_group: KernelId


@pytest.fixture
def db_source(db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
    return ScheduleDBSource(
        db_with_cleanup,
        ReconcileOpsProvider(db_with_cleanup),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


@pytest.fixture
async def other_resource_group(db_with_cleanup: ExtendedAsyncSAEngine) -> _ResourceGroupWithAgent:
    """Another resource group with preemption on and one agent."""
    group = _ResourceGroupWithAgent(
        id=ResourceGroupID(uuid.uuid4()),
        name=f"other-sgroup-{uuid.uuid4().hex[:8]}",
        agent_id=f"other-agent-{uuid.uuid4().hex[:8]}",
    )
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            ResourceGroupRow(
                id=group.id,
                name=group.name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(
                    allowed_session_types=[],
                    pending_timeout=timedelta(hours=1),
                    config={},
                    preemption=PreemptionConfig(enabled=True),
                ),
                driver_opts={},
                is_active=True,
            )
        )
        await db_sess.flush()
        db_sess.add(
            AgentRow(
                id=group.agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=group.name,
                resource_group_id=group.id,
                addr="127.0.0.1:6002",
                version="1.0.0",
                architecture="x86_64",
            )
        )
    return group


class _SpanningSessionFixtures:
    async def _create_spanning_session(
        self,
        db: ExtendedAsyncSAEngine,
        other_resource_group: _ResourceGroupWithAgent,
        *,
        session_status: SessionStatus,
        kernel_status: KernelStatus,
        assign_agents: bool,
        domain_id: DomainID,
        domain_name: str,
        resource_group_id: ResourceGroupID,
        resource_group_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str,
    ) -> _SpanningSession:
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db,
            domain_id=domain_id,
            domain_name=domain_name,
            resource_group_id=resource_group_id,
            resource_group_name=resource_group_name,
            group_id=group_id,
            user_uuid=user_uuid,
            access_key=access_key,
            agent_assignments=[
                (agent_id, Decimal("1"), Decimal("1024")),
                (other_resource_group.agent_id, Decimal("2"), Decimal("2048")),
            ],
            session_status=session_status,
            kernel_status=kernel_status,
            assign_agents=assign_agents,
        )
        async with db.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(KernelRow)
                .where(KernelRow.id == kernel_ids[1])
                .values(
                    resource_group_id=other_resource_group.id,
                    scaling_group=other_resource_group.name,
                )
            )
        return _SpanningSession(
            session_id=session_id,
            kernel_id_in_session_group=kernel_ids[0],
            kernel_id_in_other_group=kernel_ids[1],
        )


class TestPendingSpanningSession(_SpanningSessionFixtures):
    @pytest.fixture
    async def pending_spanning_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        other_resource_group: _ResourceGroupWithAgent,
        test_domain: DomainFixtureData,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> _SpanningSession:
        return await self._create_spanning_session(
            db_with_cleanup,
            other_resource_group,
            session_status=SessionStatus.PENDING,
            kernel_status=KernelStatus.PENDING,
            assign_agents=False,
            domain_id=test_domain.domain_id,
            domain_name=test_domain.domain_name,
            resource_group_id=test_scaling_group_id,
            resource_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

    async def test_fetch_carries_the_agents_and_the_group_of_every_kernel(
        self,
        db_source: ScheduleDBSource,
        other_resource_group: _ResourceGroupWithAgent,
        test_scaling_group_id: ResourceGroupID,
        test_agent_id: str,
        pending_spanning_session: _SpanningSession,
    ) -> None:
        fetch = await db_source.fetch_scheduling_fetch(test_scaling_group_id)

        assert fetch is not None
        assert [agent.id for agent in fetch.agents] == [AgentId(test_agent_id)]
        assert [(agent.id, agent.resource_group_id) for agent in fetch.agents_of_other_groups] == [
            (AgentId(other_resource_group.agent_id), other_resource_group.id)
        ]
        assert {
            kernel.kernel_id: kernel.resource_group_id
            for kernel in fetch.workloads[0].placement.kernels
        } == {
            pending_spanning_session.kernel_id_in_session_group: test_scaling_group_id,
            pending_spanning_session.kernel_id_in_other_group: other_resource_group.id,
        }

    async def test_the_session_waits_only_in_its_own_group(
        self,
        db_source: ScheduleDBSource,
        other_resource_group: _ResourceGroupWithAgent,
        pending_spanning_session: _SpanningSession,
    ) -> None:
        assert await db_source.fetch_scheduling_fetch(other_resource_group.id) is None


class TestRunningSpanningSession(_SpanningSessionFixtures):
    @pytest.fixture
    async def running_spanning_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        other_resource_group: _ResourceGroupWithAgent,
        test_domain: DomainFixtureData,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> _SpanningSession:
        """Running, with a higher-priority session waiting in the other group."""
        spanning_session = await self._create_spanning_session(
            db_with_cleanup,
            other_resource_group,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
            domain_id=test_domain.domain_id,
            domain_name=test_domain.domain_name,
            resource_group_id=test_scaling_group_id,
            resource_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(other_resource_group.agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain.domain_id,
            domain_name=test_domain.domain_name,
            resource_group_id=other_resource_group.id,
            resource_group_name=other_resource_group.name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        return spanning_session

    async def test_is_a_victim_candidate_in_the_other_group_for_its_kernel_there(
        self,
        db_source: ScheduleDBSource,
        other_resource_group: _ResourceGroupWithAgent,
        test_user_uuid: uuid.UUID,
        running_spanning_session: _SpanningSession,
    ) -> None:
        fetch = await db_source.fetch_scheduling_fetch(other_resource_group.id)

        assert fetch is not None
        candidates = fetch.preemption_candidates.by_key[
            PreemptionScopeKey(test_user_uuid)
        ].candidates
        assert [
            (candidate.session_id, candidate.allocated_slots_by_agent) for candidate in candidates
        ] == [
            (
                running_spanning_session.session_id,
                {
                    AgentId(other_resource_group.agent_id): {
                        "cpu": Decimal("2"),
                        "mem": Decimal("2048"),
                    }
                },
            )
        ]
