"""BA-6749: preemption transitions of ``ScheduleDBSource.mark_sessions_status``.

Covers the two transitions the preemption path marks — PREEMPTED (RUNNING victim
confirmed) and PENDING (reschedule victim re-enqueued) — plus the handoff to the
existing termination path and the per-resource-group preemption mode lookup,
against a real database.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import cast

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.schema.resource_group import PreemptionConfig
from ai.backend.common.types import AccessKey, PreemptionMode, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import create_pending_session_with_kernels

_REASON = "PREEMPTED_BY_SCHEDULER"


async def _free_allocations(db: ExtendedAsyncSAEngine, session_id: SessionId) -> None:
    """Mark the session's allocations as freed, as kernel termination does."""
    async with db.begin_session() as db_sess:
        kernel_ids = (
            (
                await db_sess.execute(
                    sa.select(KernelRow.id).where(KernelRow.session_id == session_id)
                )
            )
            .scalars()
            .all()
        )
        await db_sess.execute(
            sa.update(ResourceAllocationRow)
            .where(ResourceAllocationRow.kernel_id.in_(kernel_ids))
            .values(free_at=datetime.now(tzutc()))
        )


async def _session_status(db: ExtendedAsyncSAEngine, session_id: SessionId) -> SessionStatus:
    async with db.begin_readonly_session() as db_sess:
        status = await db_sess.scalar(
            sa.select(SessionRow.status).where(SessionRow.id == session_id)
        )
    return cast(SessionStatus, status)


@pytest.fixture
async def set_preemption_mode(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_scaling_group_id: ResourceGroupID,
    test_scaling_group_name: str,
) -> Callable[[PreemptionMode], Awaitable[None]]:
    """Factory that rewrites the test group's configured preemption mode."""

    async def _set(mode: PreemptionMode) -> None:
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(ScalingGroupRow)
                .where(ScalingGroupRow.id == test_scaling_group_id)
                .values(
                    scheduler_opts=ScalingGroupOpts(
                        allowed_session_types=[],
                        pending_timeout=timedelta(hours=1),
                        config={},
                        preemption=PreemptionConfig(enabled=True, mode=mode),
                    )
                )
            )

    return _set


class TestMarkSessionsPreempted:
    """RUNNING victims move to PREEMPTED while their kernels keep running."""

    async def test_running_victim_becomes_preempted_with_kernels_untouched(
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
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
        )

        preempted = await ScheduleDBSource(db_with_cleanup).mark_sessions_status(
            [session_id], SessionStatus.PREEMPTED, _REASON
        )

        assert preempted == [session_id]
        assert await _session_status(db_with_cleanup, session_id) == SessionStatus.PREEMPTED
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kernel_status = await db_sess.scalar(
                sa.select(KernelRow.status).where(KernelRow.id == kernel_ids[0])
            )
        assert kernel_status == KernelStatus.RUNNING

    async def test_terminal_session_is_skipped(
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
        """A session that already finished is not dragged back out of its
        terminal status."""
        session_id, _ = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            session_status=SessionStatus.TERMINATED,
            kernel_status=KernelStatus.TERMINATED,
        )

        preempted = await ScheduleDBSource(db_with_cleanup).mark_sessions_status(
            [session_id], SessionStatus.PREEMPTED, _REASON
        )

        assert preempted == []
        assert await _session_status(db_with_cleanup, session_id) == SessionStatus.TERMINATED


class TestMarkSessionsRescheduling:
    """The reschedule branch only moves the session; the teardown is the
    RESCHEDULING handler's job."""

    async def test_only_the_session_moves(
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
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            session_status=SessionStatus.PREEMPTED,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
        )

        marked = await ScheduleDBSource(db_with_cleanup).mark_sessions_status(
            [session_id], SessionStatus.RESCHEDULING, _REASON
        )

        assert marked == [session_id]
        assert await _session_status(db_with_cleanup, session_id) == SessionStatus.RESCHEDULING
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kernel_status = await db_sess.scalar(
                sa.select(KernelRow.status).where(KernelRow.id == kernel_ids[0])
            )
        assert kernel_status == KernelStatus.RUNNING


class TestTerminatePreemptedVictim:
    """Terminate mode hands the victim to the standard termination path."""

    async def test_preempted_victim_enters_termination_with_the_preemption_reason(
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
        """PREEMPTED is terminatable, so the existing termination path moves the
        victim (and its kernels) to TERMINATING under _REASON."""
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            session_status=SessionStatus.PREEMPTED,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
        )

        result = await ScheduleDBSource(db_with_cleanup).mark_sessions_terminating(
            [session_id], _REASON
        )

        assert result.terminating_sessions == [session_id]
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            session_row = (
                await db_sess.execute(
                    sa.select(SessionRow.status, SessionRow.status_info).where(
                        SessionRow.id == session_id
                    )
                )
            ).one()
            kernel_status = await db_sess.scalar(
                sa.select(KernelRow.status).where(KernelRow.id == kernel_ids[0])
            )
        assert session_row.status == SessionStatus.TERMINATING
        assert session_row.status_info == _REASON
        assert kernel_status == KernelStatus.TERMINATING


class TestRequeueSessionsToPending:
    """Re-enqueue of a RESCHEDULING session whose kernels are gone: the kernels
    drop their placement, then the session becomes PENDING."""

    async def test_victim_and_kernels_return_to_pending_with_priorities_kept(
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
        """The same session id is re-enqueued: session and kernels go PENDING,
        agent assignments are cleared, and job_priority/priority survive."""
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            job_priority=7,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            session_status=SessionStatus.RESCHEDULING,
            kernel_status=KernelStatus.TERMINATED,
            assign_agents=True,
        )
        # Kernel termination freed the allocations before the requeue runs.
        await _free_allocations(db_with_cleanup, session_id)

        db_source = ScheduleDBSource(db_with_cleanup)
        reset = await db_source.reset_kernels_to_pending_for_sessions([session_id], _REASON)
        requeued = await db_source.mark_sessions_status(
            [session_id], SessionStatus.PENDING, _REASON
        )

        assert reset == 1
        assert requeued == [session_id]
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            session_row = (
                await db_sess.execute(
                    sa.select(
                        SessionRow.status,
                        SessionRow.priority,
                        SessionRow.job_priority,
                    ).where(SessionRow.id == session_id)
                )
            ).one()
            kernel_row = (
                await db_sess.execute(
                    sa.select(KernelRow.status, KernelRow.agent, KernelRow.agent_addr).where(
                        KernelRow.id == kernel_ids[0]
                    )
                )
            ).one()
        assert session_row.status == SessionStatus.PENDING
        assert session_row.job_priority == 7
        assert kernel_row.status == KernelStatus.PENDING
        assert kernel_row.agent is None
        assert kernel_row.agent_addr is None

    async def test_freed_allocations_are_restored_to_the_pending_shape(
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
        """The requeued session must be schedulable again: its allocations keep
        ``requested`` but lose the usage/free marks, so the pending fetch reads
        the original request."""
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            session_status=SessionStatus.RESCHEDULING,
            kernel_status=KernelStatus.TERMINATED,
            assign_agents=True,
        )
        await _free_allocations(db_with_cleanup, session_id)

        await ScheduleDBSource(db_with_cleanup).reset_kernels_to_pending_for_sessions(
            [session_id], _REASON
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            allocations = (
                (
                    await db_sess.execute(
                        sa.select(ResourceAllocationRow).where(
                            ResourceAllocationRow.kernel_id == kernel_ids[0]
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert allocations
        assert {row.slot_name: row.requested for row in allocations} == {
            "cpu": Decimal("2.000000"),
            "mem": Decimal("4096.000000"),
        }
        for row in allocations:
            assert row.used is None
            assert row.used_at is None
            assert row.free_at is None

    async def test_terminal_session_is_not_requeued(
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
        """A cancelled session stays cancelled — the re-enqueue does not revive it."""
        session_id, _ = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            resource_group_id=test_scaling_group_id,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            session_status=SessionStatus.CANCELLED,
            kernel_status=KernelStatus.CANCELLED,
        )

        requeued = await ScheduleDBSource(db_with_cleanup).mark_sessions_status(
            [session_id], SessionStatus.PENDING, _REASON
        )

        assert requeued == []
        assert await _session_status(db_with_cleanup, session_id) == SessionStatus.CANCELLED


class TestGetResourceGroupPreemptionMode:
    async def test_reads_the_configured_mode(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        set_preemption_mode: Callable[[PreemptionMode], Awaitable[None]],
    ) -> None:
        await set_preemption_mode(PreemptionMode.RESCHEDULE)

        mode = await ScheduleDBSource(db_with_cleanup).get_resource_group_preemption_mode(
            test_scaling_group_id
        )

        assert mode == PreemptionMode.RESCHEDULE

    async def test_defaults_to_terminate(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
    ) -> None:
        """A group that never configured preemption reports the default mode."""
        mode = await ScheduleDBSource(db_with_cleanup).get_resource_group_preemption_mode(
            test_scaling_group_id
        )

        assert mode == PreemptionMode.TERMINATE
