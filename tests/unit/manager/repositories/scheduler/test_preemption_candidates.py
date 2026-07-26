"""BA-6747: preemption victim candidate loading in the scheduling fetch.

The candidate prefilter is defined at the load site
(``ScheduleDBSource._fetch_preemption_candidates``); these tests verify it
against a real database.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.schema.resource_group import PreemptionConfig
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import create_pending_session_with_kernels


async def _create_allocated_session(
    db: ExtendedAsyncSAEngine,
    *,
    domain_id: DomainID,
    domain_name: str,
    resource_group_id: ResourceGroupID,
    scaling_group_name: str,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    access_key: AccessKey,
    agent_assignments: list[tuple[str, Decimal, Decimal]],
    job_priority: int = 0,
    is_preemptible: bool = True,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
    session_status: SessionStatus = SessionStatus.RUNNING,
    kernel_status: KernelStatus = KernelStatus.RUNNING,
) -> SessionId:
    """A resource-holding session: the shared factory with agents assigned."""
    session_id, _ = await create_pending_session_with_kernels(
        db,
        domain_id=domain_id,
        domain_name=domain_name,
        resource_group_id=resource_group_id,
        scaling_group_name=scaling_group_name,
        group_id=group_id,
        user_uuid=user_uuid,
        access_key=access_key,
        agent_assignments=agent_assignments,
        job_priority=job_priority,
        is_preemptible=is_preemptible,
        session_type=session_type,
        session_status=session_status,
        kernel_status=kernel_status,
        assign_agents=True,
    )
    return session_id


async def _create_extra_user(
    db: ExtendedAsyncSAEngine,
    *,
    domain_name: str,
    user_resource_policy: str,
    keypair_resource_policy: str,
) -> tuple[uuid.UUID, AccessKey]:
    """Create a second user with its own keypair."""
    user_uuid = uuid.uuid4()
    suffix = uuid.uuid4().hex[:8]
    email = f"extra-user-{suffix}@test.com"
    access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
    async with db.begin_session() as db_sess:
        db_sess.add(
            UserRow(
                uuid=user_uuid,
                email=email,
                username=f"extra-user-{suffix}",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                domain_name=domain_name,
                resource_policy=user_resource_policy,
            )
        )
        await db_sess.flush()
        db_sess.add(
            KeyPairRow(
                user_id=email,
                access_key=access_key,
                secret_key=SecretKey(f"SK{uuid.uuid4().hex}"),
                is_active=True,
                is_admin=False,
                resource_policy=keypair_resource_policy,
                rate_limit=1000,
                num_queries=0,
                user=user_uuid,
            )
        )
        await db_sess.flush()
    return user_uuid, access_key


async def _create_extra_agent(
    db: ExtendedAsyncSAEngine,
    *,
    scaling_group_name: str,
    resource_group_id: ResourceGroupID,
) -> str:
    agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
    async with db.begin_session() as db_sess:
        db_sess.add(
            AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=scaling_group_name,
                resource_group_id=resource_group_id,
                available_slots=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("10240")}),
                occupied_slots=ResourceSlot(),
                addr="127.0.0.1:6001",
                version="1.0.0",
                architecture="x86_64",
            )
        )
        await db_sess.flush()
    return agent_id


@pytest.fixture
async def preemption_enabled(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_scaling_group_name: str,
    test_scaling_group_id: ResourceGroupID,
) -> None:
    """Turn on preemption for the test scaling group."""
    async with db_with_cleanup.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(ScalingGroupRow)
            .where(ScalingGroupRow.id == test_scaling_group_id)
            .values(
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[],
                    pending_timeout=timedelta(hours=1),
                    config={},
                    preemption=PreemptionConfig(enabled=True),
                )
            )
        )


class TestFetchPreemptionCandidates:
    """Preemption candidate loading in ScheduleDBSource.fetch_scheduling_fetch."""

    async def test_disabled_group_returns_empty_snapshot(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # A session that would qualify if preemption were enabled
        await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            job_priority=0,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        assert fetch.preemption_candidates.by_user == {}

    async def test_excludes_non_victim_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
        preemption_enabled: None,
    ) -> None:
        """Equal-priority, non-preemptible, TERMINATING, and private sessions never load."""
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # Included: same owner, strictly lower job_priority, preemptible
        victim_id = await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            job_priority=5,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # Excluded: job_priority equals the owner's max pending (not strictly lower)
        await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # Excluded: not preemptible
        await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=5,
            is_preemptible=False,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # Excluded: already terminating — its resources free without preemption
        await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=0,
            session_status=SessionStatus.TERMINATING,
            kernel_status=KernelStatus.TERMINATING,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # Excluded: private (system) sessions are never victims
        await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=0,
            session_type=SessionTypes.SYSTEM,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        by_user = fetch.preemption_candidates.by_user
        assert set(by_user.keys()) == {UserID(test_user_uuid)}
        candidates = by_user[UserID(test_user_uuid)].candidates
        assert [c.session_id for c in candidates] == [victim_id]
        candidate = candidates[0]
        assert candidate.job_priority == 5
        assert candidate.started_at is not None
        assert candidate.allocated_slots_by_agent == {
            AgentId(test_agent_id): {
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
            },
        }

    async def test_scheduled_victim_included_without_started_at(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
        preemption_enabled: None,
    ) -> None:
        """SCHEDULED sessions hold agent resources and qualify as victims."""
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        scheduled_victim_id = await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("1024"))],
            job_priority=1,
            session_status=SessionStatus.SCHEDULED,
            kernel_status=KernelStatus.SCHEDULED,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        candidates = fetch.preemption_candidates.by_user[UserID(test_user_uuid)].candidates
        assert [c.session_id for c in candidates] == [scheduled_victim_id]
        # Pre-running candidate: reservation amounts, no execution start
        candidate = candidates[0]
        assert candidate.started_at is None
        assert candidate.allocated_slots_by_agent == {
            AgentId(test_agent_id): {
                "cpu": Decimal("2"),
                "mem": Decimal("1024"),
            },
        }

    async def test_per_owner_thresholds_do_not_leak(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
        resource_slot_types: None,
        preemption_enabled: None,
    ) -> None:
        """Each owner's candidates compare against that owner's own max pending."""
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        victim_id = await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            job_priority=5,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # Second owner with their own, lower pending threshold (max pending
        # job_priority = 3). Their thresholds must not leak across owners.
        other_user, other_access_key = await _create_extra_user(
            db_with_cleanup,
            domain_name=test_domain_name,
            user_resource_policy=test_user_resource_policy_name,
            keypair_resource_policy=test_keypair_resource_policy_name,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=3,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=other_user,
            access_key=other_access_key,
        )
        # Excluded: below the FIRST owner's max (10) but not below its own
        # owner's max (3) — would leak in if the threshold were global
        await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=5,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=other_user,
            access_key=other_access_key,
        )
        # Included: strictly below its own owner's max (3)
        other_victim_id = await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("3"), Decimal("2048"))],
            job_priority=2,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=other_user,
            access_key=other_access_key,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        by_user = fetch.preemption_candidates.by_user
        assert set(by_user.keys()) == {UserID(test_user_uuid), UserID(other_user)}
        assert [c.session_id for c in by_user[UserID(test_user_uuid)].candidates] == [victim_id]
        other_candidates = by_user[UserID(other_user)].candidates
        assert [c.session_id for c in other_candidates] == [other_victim_id]
        assert other_candidates[0].job_priority == 2

    async def test_private_pending_does_not_initiate_preemption(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
        resource_slot_types: None,
        preemption_enabled: None,
    ) -> None:
        """A pending private (SFTP/system) session sets no preemption threshold."""
        # First owner's only pending is private: their running session must
        # not become a candidate on its behalf
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            session_type=SessionTypes.SYSTEM,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            job_priority=0,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        # Second owner with a regular pending keeps the candidate query alive
        other_user, other_access_key = await _create_extra_user(
            db_with_cleanup,
            domain_name=test_domain_name,
            user_resource_policy=test_user_resource_policy_name,
            keypair_resource_policy=test_keypair_resource_policy_name,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=other_user,
            access_key=other_access_key,
        )
        other_victim_id = await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=5,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=other_user,
            access_key=other_access_key,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        by_user = fetch.preemption_candidates.by_user
        assert set(by_user.keys()) == {UserID(other_user)}
        assert [c.session_id for c in by_user[UserID(other_user)].candidates] == [other_victim_id]

    async def test_reclaimable_totals_sum_owner_victims_per_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
        preemption_enabled: None,
    ) -> None:
        """The derived per-agent view sums all of the owner's victims."""
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        victim_ids: set[SessionId] = set()
        for job_priority, cpu, mem, session_status, kernel_status in (
            (5, "2", "4096", SessionStatus.RUNNING, KernelStatus.RUNNING),
            (4, "1", "1024", SessionStatus.RUNNING, KernelStatus.RUNNING),
            (1, "2", "1024", SessionStatus.SCHEDULED, KernelStatus.SCHEDULED),
        ):
            victim_ids.add(
                await _create_allocated_session(
                    db_with_cleanup,
                    agent_assignments=[(test_agent_id, Decimal(cpu), Decimal(mem))],
                    job_priority=job_priority,
                    session_status=session_status,
                    kernel_status=kernel_status,
                    domain_id=test_domain_id,
                    domain_name=test_domain_name,
                    resource_group_id=test_scaling_group_id,
                    scaling_group_name=test_scaling_group_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    access_key=test_access_key,
                )
            )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        user_entry = fetch.preemption_candidates.by_user[UserID(test_user_uuid)]
        agent_entry = user_entry.by_agent[AgentId(test_agent_id)]
        assert {c.session_id for c in agent_entry.candidates} == victim_ids
        assert agent_entry.total_reclaimable == {
            "cpu": Decimal("5"),
            "mem": Decimal("6144"),
        }

    async def test_multi_node_session_is_one_candidate_with_per_agent_slots(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
        preemption_enabled: None,
    ) -> None:
        second_agent_id = await _create_extra_agent(
            db_with_cleanup,
            scaling_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            job_priority=10,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )
        victim_id = await _create_allocated_session(
            db_with_cleanup,
            agent_assignments=[
                (test_agent_id, Decimal("1"), Decimal("1024")),
                (second_agent_id, Decimal("2"), Decimal("2048")),
            ],
            job_priority=0,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        by_user = fetch.preemption_candidates.by_user
        assert set(by_user.keys()) == {UserID(test_user_uuid)}
        user_entry = by_user[UserID(test_user_uuid)]
        assert len(user_entry.candidates) == 1
        candidate = user_entry.candidates[0]
        assert candidate.session_id == victim_id
        assert candidate.allocated_slots_by_agent == {
            AgentId(test_agent_id): {"cpu": Decimal("1"), "mem": Decimal("1024")},
            AgentId(second_agent_id): {"cpu": Decimal("2"), "mem": Decimal("2048")},
        }
        # Derived per-agent view: the same single candidate under both agents,
        # each with agent-scoped reclaimable totals
        assert set(user_entry.by_agent.keys()) == {
            AgentId(test_agent_id),
            AgentId(second_agent_id),
        }
        assert user_entry.by_agent[AgentId(test_agent_id)].candidates == [candidate]
        assert user_entry.by_agent[AgentId(test_agent_id)].total_reclaimable == {
            "cpu": Decimal("1"),
            "mem": Decimal("1024"),
        }
        assert user_entry.by_agent[AgentId(second_agent_id)].total_reclaimable == {
            "cpu": Decimal("2"),
            "mem": Decimal("2048"),
        }
